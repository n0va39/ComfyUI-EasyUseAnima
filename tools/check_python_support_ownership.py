#!/usr/bin/env python3
"""Validate the PTC-08 support-artifact ownership contract.

The contract is deliberately separate from the shipped Python disposition plan.
It inventories tests, fixtures, maintenance tools, official runners, and the
manual/live matrices already named by G-06 without importing production code.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "tests"
    / "fixtures"
    / "python_support_ownership_contract.v1.json"
)
OWNER_CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "tests"
    / "fixtures"
    / "python_test_ownership_contract.v1.json"
)
CONTRACT_SCHEMA_VERSION = 1
EXPECTED_KINDS = (
    "generated_baseline",
    "maintenance_tool",
    "manual_live_matrix",
    "runner",
    "test",
    "test_fixture",
)
EXPECTED_MODES = (
    "benchmark-on-demand",
    "direct-python",
    "fixture-input",
    "manual-on-trigger",
    "node-smoke",
    "official-runner",
    "unittest",
)
EXPECTED_SUPPORT_PATTERNS = (
    "tests/**/*.json",
    "tests/**/*.mjs",
    "tests/**/*.py",
    "tools/**/*.ps1",
    "tools/**/*.py",
)
EXPECTED_LINKED_CONTRACTS = {
    "production_owner_map": "tests/fixtures/python_test_ownership_contract.v1.json"
}
SPECIAL_GROUP = "cross-cutting"


class ContractError(ValueError):
    """The checked-in support ownership plan is invalid or incomplete."""


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_sorted_unique_strings(values: object, *, field: str) -> tuple[str, ...]:
    if not isinstance(values, list) or not all(
        isinstance(value, str) and value for value in values
    ):
        raise ContractError(f"{field} must be a list of non-empty strings")
    if values != sorted(set(values)):
        raise ContractError(f"{field} must be sorted and unique")
    return tuple(values)


def _load_owner_groups(document: object) -> tuple[str, ...]:
    if not isinstance(document, dict) or not isinstance(document.get("groups"), list):
        raise ContractError("production owner contract must contain groups")
    names: list[str] = []
    for group in document["groups"]:
        if not isinstance(group, dict) or not isinstance(group.get("name"), str):
            raise ContractError("production owner group is malformed")
        names.append(group["name"])
    if names != sorted(set(names)):
        raise ContractError("production owner groups must be sorted and unique")
    return tuple(names)


def _manual_matrix_paths(document: object) -> tuple[str, ...]:
    if not isinstance(document, dict) or not isinstance(document.get("matrices"), list):
        raise ContractError("production owner contract must contain matrices")
    paths = [
        matrix.get("owner")
        for matrix in document["matrices"]
        if isinstance(matrix, dict) and matrix.get("mode") == "manual-on-trigger"
    ]
    if not paths or not all(isinstance(path, str) and path for path in paths):
        raise ContractError("manual-on-trigger matrices must name support owners")
    if len(paths) != len(set(paths)):
        raise ContractError("manual/live matrix owners must be unique")
    return tuple(sorted(paths))


def discover_support_paths(
    repository_root: Path,
    owner_document: object,
) -> tuple[str, ...]:
    """Return the exact current support scope without using Git or production imports."""

    paths: set[str] = set()
    for pattern in EXPECTED_SUPPORT_PATTERNS:
        for candidate in repository_root.glob(pattern):
            if candidate.is_file() and "__pycache__" not in candidate.parts:
                paths.add(candidate.relative_to(repository_root).as_posix())
    for path in _manual_matrix_paths(owner_document):
        candidate = repository_root / path
        if not candidate.is_file():
            raise ContractError(f"manual/live matrix does not exist: {path}")
        paths.add(path)
    return tuple(sorted(paths))


def _expected_kind_mode(path: str) -> tuple[set[str], set[str]]:
    if path.startswith("docs/"):
        return {"manual_live_matrix"}, {"manual-on-trigger"}
    if path.startswith("tests/fixtures/"):
        return {"generated_baseline", "test_fixture"}, {"fixture-input"}
    if path.startswith("tests/") and path.endswith(".mjs"):
        return {"test"}, {"node-smoke"}
    if path.startswith("tests/") and path.endswith(".py"):
        if Path(path).name.startswith("test"):
            return {"test"}, {"unittest"}
        return {"test_fixture"}, {"fixture-input"}
    if path.startswith("tools/") and path.endswith(".ps1"):
        return {"runner"}, {"official-runner"}
    if path.startswith("tools/benchmark_") and path.endswith(".py"):
        return {"maintenance_tool"}, {"benchmark-on-demand"}
    if path.startswith("tools/") and path.endswith(".py"):
        return {"maintenance_tool"}, {"direct-python"}
    raise ContractError(f"path is outside the reviewed support scope: {path}")


def validate_contract(
    document: object,
    *,
    owner_document: object,
    repository_root: Path = REPOSITORY_ROOT,
) -> dict[str, object]:
    """Validate and normalize the static PTC-08 support document."""

    expected_keys = {
        "allowed_execution_modes",
        "allowed_kinds",
        "baseline_commit",
        "entries",
        "inventory",
        "linked_contracts",
        "schema_version",
    }
    if not isinstance(document, dict) or set(document) != expected_keys:
        raise ContractError("contract keys do not match the PTC-08 schema")
    if document["schema_version"] != CONTRACT_SCHEMA_VERSION:
        raise ContractError("unsupported support contract schema_version")
    baseline_commit = document["baseline_commit"]
    if not isinstance(baseline_commit, str) or not re.fullmatch(
        r"[0-9a-f]{40}", baseline_commit
    ):
        raise ContractError("baseline_commit must be a full Git SHA")
    if tuple(document["allowed_kinds"]) != EXPECTED_KINDS:
        raise ContractError("allowed support kinds must remain the reviewed PTC-08 set")
    if tuple(document["allowed_execution_modes"]) != EXPECTED_MODES:
        raise ContractError("execution modes must remain the reviewed PTC-08 set")
    if document["linked_contracts"] != EXPECTED_LINKED_CONTRACTS:
        raise ContractError("support ownership must reuse the G-06 production owner map")

    inventory = document["inventory"]
    if not isinstance(inventory, dict) or set(inventory) != {
        "expected_files",
        "manual_matrix_source",
        "patterns",
    }:
        raise ContractError("inventory keys do not match the PTC-08 schema")
    if tuple(inventory["patterns"]) != EXPECTED_SUPPORT_PATTERNS:
        raise ContractError("support inventory patterns must remain exact")
    if inventory["manual_matrix_source"] != EXPECTED_LINKED_CONTRACTS[
        "production_owner_map"
    ]:
        raise ContractError("manual/live inventory must reuse the G-06 matrix source")
    expected_files = inventory["expected_files"]
    if type(expected_files) is not int or expected_files <= 0:
        raise ContractError("expected_files must be a positive integer")

    owner_groups = _load_owner_groups(owner_document)
    allowed_groups = set(owner_groups) | {SPECIAL_GROUP}
    manual_paths = set(_manual_matrix_paths(owner_document))
    entries = document["entries"]
    if not isinstance(entries, list):
        raise ContractError("entries must be a list")

    normalized: list[dict[str, object]] = []
    paths: list[str] = []
    for raw in entries:
        if not isinstance(raw, dict) or set(raw) != {
            "execution_mode",
            "generated",
            "kind",
            "owner",
            "path",
            "production_groups",
            "purpose",
        }:
            raise ContractError("entry keys do not match the PTC-08 schema")
        path = raw["path"]
        owner = raw["owner"]
        purpose = raw["purpose"]
        kind = raw["kind"]
        mode = raw["execution_mode"]
        generated = raw["generated"]
        if not isinstance(path, str) or not path:
            raise ContractError("support path must be a non-empty string")
        if not isinstance(owner, str) or not owner:
            raise ContractError(f"support owner is missing: {path}")
        if not isinstance(purpose, str) or len(purpose.strip()) < 20:
            raise ContractError(f"support purpose is not concrete: {path}")
        if kind not in EXPECTED_KINDS or mode not in EXPECTED_MODES:
            raise ContractError(f"unknown support kind or execution mode: {path}")
        expected_kinds, expected_modes = _expected_kind_mode(path)
        if kind not in expected_kinds or mode not in expected_modes:
            raise ContractError(f"support kind/mode does not match its path: {path}")
        if type(generated) is not bool:
            raise ContractError(f"generated must be a boolean: {path}")
        if generated != (kind == "generated_baseline"):
            raise ContractError(f"generated flag and kind disagree: {path}")
        groups = _require_sorted_unique_strings(
            raw["production_groups"], field=f"{path}.production_groups"
        )
        if not groups or not set(groups) <= allowed_groups:
            raise ContractError(f"support production group is invalid: {path}")
        if path.startswith("docs/") != (path in manual_paths):
            raise ContractError(f"manual/live matrix scope drift: {path}")
        paths.append(path)
        normalized.append(
            {
                "execution_mode": mode,
                "generated": generated,
                "kind": kind,
                "owner": owner,
                "path": path,
                "production_groups": groups,
                "purpose": purpose.strip(),
            }
        )

    if paths != sorted(set(paths)):
        raise ContractError("support entries must be sorted and unique by path")
    if expected_files != len(paths):
        raise ContractError("expected_files does not match the support entries")
    path_set = set(paths)
    kind_by_path = {str(entry["path"]): str(entry["kind"]) for entry in normalized}
    responsible_owner_kinds = {
        "maintenance_tool",
        "manual_live_matrix",
        "runner",
        "test",
    }
    for entry in normalized:
        path = str(entry["path"])
        owner = str(entry["owner"])
        if owner not in path_set:
            raise ContractError(f"support owner is outside the exact inventory: {path}")
        if kind_by_path[owner] not in responsible_owner_kinds:
            raise ContractError(f"support owner is not a responsible executable: {path}")
        if entry["kind"] in {"generated_baseline", "test_fixture"} and owner == path:
            raise ContractError(f"fixture cannot own itself: {path}")

    covered_groups = {
        group
        for entry in normalized
        for group in entry["production_groups"]
        if group != SPECIAL_GROUP
    }
    if covered_groups != set(owner_groups):
        missing = sorted(set(owner_groups) - covered_groups)
        extra = sorted(covered_groups - set(owner_groups))
        raise ContractError(
            f"support production-group coverage drift: missing={missing}, extra={extra}"
        )

    return {
        "baseline_commit": baseline_commit,
        "entries": tuple(normalized),
        "expected_files": expected_files,
        "owner_groups": owner_groups,
        "paths": tuple(paths),
        "schema_version": CONTRACT_SCHEMA_VERSION,
    }


def check_repository(
    repository_root: Path = REPOSITORY_ROOT,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
) -> list[dict[str, object]]:
    """Return deterministic exact-scope violations for the current repository."""

    owner_document = _load_json(repository_root / OWNER_CONTRACT_PATH.relative_to(REPOSITORY_ROOT))
    contract = validate_contract(
        _load_json(contract_path),
        owner_document=owner_document,
        repository_root=repository_root,
    )
    actual = discover_support_paths(repository_root, owner_document)
    return check_current_inventory(actual, contract)


def check_current_inventory(
    actual_paths: Sequence[str],
    contract: Mapping[str, object],
) -> list[dict[str, object]]:
    """Return missing/unclassified violations for an already validated contract."""

    expected = set(contract["paths"])
    actual = set(actual_paths)
    violations = [
        {"rule": "missing-support-artifact", "path": path}
        for path in sorted(expected - actual)
    ]
    violations.extend(
        {"rule": "unclassified-support-artifact", "path": path}
        for path in sorted(actual - expected)
    )
    return violations


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT_PATH)
    args = parser.parse_args(argv)
    violations = check_repository(REPOSITORY_ROOT, args.contract)
    if violations:
        json.dump({"violations": violations}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 1
    document = _load_json(args.contract)
    print(
        "Python support ownership contract passed: "
        f"{document['inventory']['expected_files']} artifacts, 0 orphans."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
