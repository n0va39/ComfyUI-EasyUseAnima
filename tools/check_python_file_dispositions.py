#!/usr/bin/env python3
"""Validate the blocking Total Python Convergence file-disposition plan.

The plan reuses the analyzer inventory, G-06 test-owner map, G-05 size ledger,
and compatibility registry.  It does not import production modules or maintain
a second generated source inventory.
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
    / "python_file_disposition_contract.v1.json"
)
CONTRACT_SCHEMA_VERSION = 1
EXPECTED_DISPOSITIONS = (
    "cohesive_retain",
    "delete",
    "merge",
    "move",
    "permanent_entrypoint",
    "split",
)
EXPECTED_STATUSES = ("complete", "planned")
EXPECTED_LINKED_CONTRACTS = {
    "compatibility_registry": "docs/architecture/python-compatibility-shims.md",
    "import_owner_map": "tests/fixtures/python_test_ownership_contract.v1.json",
    "size_ledger": "tests/fixtures/python_size_complexity_contract.v1.json",
}
SPECIAL_OWNER_GROUPS = {"compatibility", "entrypoint", "package"}
SIZE_VERDICTS = {
    "cohesive_retain",
    "delete_after_canonical_cutover",
    "move_retain_cohesive",
    "split",
}
GENERIC_TARGET_STEM = re.compile(r"^(?:helper|helpers|misc|util|utils)\d*$")


class ContractError(ValueError):
    """The checked-in disposition plan is invalid or incomplete."""


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


def _load_owner_groups(document: object) -> dict[str, dict[str, object]]:
    if not isinstance(document, dict) or not isinstance(document.get("groups"), list):
        raise ContractError("test ownership contract must contain groups")
    groups: dict[str, dict[str, object]] = {}
    for raw_group in document["groups"]:
        if not isinstance(raw_group, dict):
            raise ContractError("test ownership groups must be objects")
        name = raw_group.get("name")
        paths = raw_group.get("production_paths")
        owners = raw_group.get("owners")
        if (
            not isinstance(name, str)
            or not name
            or not isinstance(paths, list)
            or not all(isinstance(path, str) and path for path in paths)
            or not isinstance(owners, dict)
            or not owners
        ):
            raise ContractError("test ownership group is malformed")
        if name in groups:
            raise ContractError(f"duplicate test ownership group: {name}")
        if not owners.get("package_archive"):
            raise ContractError(f"owner group lacks package/archive coverage: {name}")
        groups[name] = raw_group
    return groups


def _matching_owner_groups(
    path: str,
    owner_groups: Mapping[str, Mapping[str, object]],
) -> tuple[str, ...]:
    matches: list[str] = []
    for name, group in owner_groups.items():
        for prefix in group["production_paths"]:
            if (prefix.endswith("/") and path.startswith(prefix)) or path == prefix:
                matches.append(name)
                break
    return tuple(sorted(matches))


def _size_exception_records(document: object) -> dict[str, dict[str, object]]:
    if not isinstance(document, dict):
        raise ContractError("size ledger must be an object")
    modules = document.get("module_exceptions")
    functions = document.get("function_exceptions")
    if not isinstance(modules, list) or not isinstance(functions, list):
        raise ContractError("size ledger exception lists are missing")
    records: dict[str, dict[str, object]] = {}
    for raw in modules:
        if not isinstance(raw, dict) or not isinstance(raw.get("path"), str):
            raise ContractError("module size exception is malformed")
        exception_id = f"module:{raw['path']}"
        records[exception_id] = raw
    for raw in functions:
        if (
            not isinstance(raw, dict)
            or not isinstance(raw.get("path"), str)
            or not isinstance(raw.get("qualified_name"), str)
        ):
            raise ContractError("function size exception is malformed")
        exception_id = f"function:{raw['path']}::{raw['qualified_name']}"
        records[exception_id] = raw
    if len(records) != len(modules) + len(functions):
        raise ContractError("size exception IDs must be unique")
    return records


def _validate_target(
    raw_target: object,
    *,
    owner_groups: Mapping[str, Mapping[str, object]],
) -> dict[str, str]:
    if not isinstance(raw_target, dict) or set(raw_target) != {
        "owner_group",
        "path",
        "role",
    }:
        raise ContractError("target keys must be owner_group, path and role")
    path = raw_target["path"]
    role = raw_target["role"]
    owner_group = raw_target["owner_group"]
    if not isinstance(path, str) or not path.endswith(".py"):
        raise ContractError("target path must be a production Python path")
    if not isinstance(role, str) or len(role.strip()) < 4:
        raise ContractError(f"target role is not concrete: {path}")
    if not isinstance(owner_group, str) or not owner_group:
        raise ContractError(f"target owner_group is missing: {path}")
    if owner_group not in SPECIAL_OWNER_GROUPS:
        matches = _matching_owner_groups(path, owner_groups)
        if matches != (owner_group,):
            raise ContractError(
                f"target owner mismatch: {path} declares {owner_group}, matches {matches}"
            )
    elif owner_group == "package" and path != "easyuse_anima/__init__.py":
        raise ContractError("package owner is reserved for easyuse_anima/__init__.py")
    elif owner_group == "entrypoint" and path != "__init__.py":
        raise ContractError("entrypoint owner is reserved for root __init__.py")
    elif owner_group == "compatibility" and (
        path.startswith("easyuse_anima/") or path == "__init__.py"
    ):
        raise ContractError(f"canonical path cannot use compatibility owner: {path}")
    return {"owner_group": owner_group, "path": path, "role": role}


def _validate_entry_owner(
    path: str,
    owner_group: str,
    owner_groups: Mapping[str, Mapping[str, object]],
) -> None:
    if owner_group not in SPECIAL_OWNER_GROUPS:
        matches = _matching_owner_groups(path, owner_groups)
        if matches != (owner_group,):
            raise ContractError(
                f"entry owner mismatch: {path} declares {owner_group}, matches {matches}"
            )
    elif owner_group == "package" and path != "easyuse_anima/__init__.py":
        raise ContractError("package owner is reserved for easyuse_anima/__init__.py")
    elif owner_group == "entrypoint" and path != "__init__.py":
        raise ContractError("entrypoint owner is reserved for root __init__.py")
    elif owner_group == "compatibility" and (
        path.startswith("easyuse_anima/") or path == "__init__.py"
    ):
        raise ContractError(f"canonical path cannot use compatibility owner: {path}")


def validate_contract(
    document: object,
    *,
    owner_document: object,
    size_document: object,
    compatibility_text: str,
    repository_root: Path = REPOSITORY_ROOT,
) -> dict[str, object]:
    """Validate and normalize the static disposition document."""

    expected_keys = {
        "allowed_dispositions",
        "allowed_statuses",
        "baseline_commit",
        "entries",
        "inventory_owner",
        "linked_contracts",
        "schema_version",
    }
    if not isinstance(document, dict) or set(document) != expected_keys:
        raise ContractError("contract keys do not match the PTC-01 schema")
    if document["schema_version"] != CONTRACT_SCHEMA_VERSION:
        raise ContractError("unsupported disposition contract schema_version")
    baseline_commit = document["baseline_commit"]
    if not isinstance(baseline_commit, str) or not re.fullmatch(
        r"[0-9a-f]{40}", baseline_commit
    ):
        raise ContractError("baseline_commit must be a full Git SHA")
    if tuple(document["allowed_dispositions"]) != EXPECTED_DISPOSITIONS:
        raise ContractError("allowed dispositions must remain the reviewed PTC set")
    if tuple(document["allowed_statuses"]) != EXPECTED_STATUSES:
        raise ContractError("allowed statuses must remain complete/planned")
    if document["linked_contracts"] != EXPECTED_LINKED_CONTRACTS:
        raise ContractError("linked contracts must reuse the authoritative owners")

    inventory_owner = document["inventory_owner"]
    if not isinstance(inventory_owner, dict) or set(inventory_owner) != {
        "expected_baseline_files",
        "expected_target_files",
        "path",
    }:
        raise ContractError("inventory_owner keys do not match the PTC-01 schema")
    if inventory_owner["path"] != "tests/fixtures/python_backend_baseline.json":
        raise ContractError("inventory must reuse python_backend_baseline.json")
    expected_baseline_files = inventory_owner["expected_baseline_files"]
    expected_target_files = inventory_owner["expected_target_files"]
    if (
        type(expected_baseline_files) is not int
        or expected_baseline_files <= 0
        or type(expected_target_files) is not int
        or expected_target_files <= 0
    ):
        raise ContractError("inventory counts must be positive and monotonic")

    owner_groups = _load_owner_groups(owner_document)
    size_records = _size_exception_records(size_document)
    entries = document["entries"]
    if not isinstance(entries, list):
        raise ContractError("entries must be a list")
    normalized_entries: list[dict[str, object]] = []
    entry_paths: list[str] = []
    target_paths: list[str] = []
    linked_size_ids: list[str] = []

    for raw_entry in entries:
        if not isinstance(raw_entry, dict) or set(raw_entry) != {
            "compatibility_registry_key",
            "direct_contracts",
            "disposition",
            "owner_group",
            "path",
            "role",
            "rollback_unit",
            "replacement_owner",
            "size_exception_verdicts",
            "status",
            "targets",
            "task_id",
        }:
            raise ContractError("entry keys do not match the PTC-01 schema")
        path = raw_entry["path"]
        role = raw_entry["role"]
        owner_group = raw_entry["owner_group"]
        disposition = raw_entry["disposition"]
        status = raw_entry["status"]
        if not isinstance(path, str) or not path.endswith(".py"):
            raise ContractError("entry path must be a production Python path")
        if not isinstance(role, str) or len(role.strip()) < 4:
            raise ContractError(f"entry role is not concrete: {path}")
        if not isinstance(owner_group, str) or not owner_group:
            raise ContractError(f"entry owner_group is missing: {path}")
        _validate_entry_owner(path, owner_group, owner_groups)
        if disposition not in EXPECTED_DISPOSITIONS:
            raise ContractError(f"unknown disposition: {path}")
        if status not in EXPECTED_STATUSES:
            raise ContractError(f"unknown disposition status: {path}")

        target_values = raw_entry["targets"]
        if not isinstance(target_values, list):
            raise ContractError(f"entry targets must be a list: {path}")
        targets = [
            _validate_target(target, owner_groups=owner_groups)
            for target in target_values
        ]
        if len({target["path"] for target in targets}) != len(targets):
            raise ContractError(f"targets must be unique: {path}")
        if disposition != "delete":
            if not targets:
                raise ContractError(f"retained entry must declare targets: {path}")
            source_targets = [target for target in targets if target["path"] == path]
            if len(source_targets) != 1 or (
                owner_group != source_targets[0]["owner_group"]
                or role != source_targets[0]["role"]
            ):
                raise ContractError(
                    f"one target must preserve the current owner/role: {path}"
                )

        direct_contracts = _require_sorted_unique_strings(
            raw_entry["direct_contracts"], field=f"{path}.direct_contracts"
        )
        for contract in direct_contracts:
            if not (repository_root / contract).is_file():
                raise ContractError(f"direct contract does not exist: {contract}")

        registry_key = raw_entry["compatibility_registry_key"]
        compatibility_surface = owner_group == "compatibility" or disposition == (
            "permanent_entrypoint"
        )
        if compatibility_surface:
            if not isinstance(registry_key, str) or not registry_key:
                raise ContractError(f"compatibility registry key is missing: {path}")
            if f"`{registry_key}`" not in compatibility_text:
                raise ContractError(
                    f"compatibility registry key is not authoritative: {registry_key}"
                )
        elif registry_key is not None:
            raise ContractError(f"canonical entry cannot cite compatibility key: {path}")

        task_id = raw_entry["task_id"]
        rollback_unit = raw_entry["rollback_unit"]
        replacement_owner = raw_entry["replacement_owner"]
        if disposition in {"delete", "merge", "move", "split"}:
            if not isinstance(task_id, str) or not task_id:
                raise ContractError(f"structural disposition lacks task_id: {path}")
            if not isinstance(rollback_unit, str) or len(rollback_unit.strip()) < 12:
                raise ContractError(f"structural disposition lacks rollback unit: {path}")
            if not direct_contracts:
                raise ContractError(f"structural disposition lacks direct tests: {path}")
        elif task_id is not None or rollback_unit is not None:
            raise ContractError(f"retained entry must not invent a structural task: {path}")

        if disposition == "delete":
            if targets:
                raise ContractError(f"delete must have no final target path: {path}")
            if (
                not isinstance(replacement_owner, str)
                or not replacement_owner.startswith("easyuse_anima/")
                or not replacement_owner.endswith(".py")
            ):
                raise ContractError(
                    f"delete must name a canonical replacement owner: {path}"
                )
        elif replacement_owner is not None:
            raise ContractError(f"non-delete entry cannot name replacement_owner: {path}")

        if disposition == "split":
            if len(targets) < 2 or path not in {target["path"] for target in targets}:
                raise ContractError(f"split must retain a facade and add targets: {path}")
        elif disposition in {
            "cohesive_retain",
            "permanent_entrypoint",
        }:
            if len(targets) != 1 or targets[0]["path"] != path:
                raise ContractError(f"retained entry must keep one exact target: {path}")
            if status != "complete":
                raise ContractError(f"retained entry must already be complete: {path}")

        size_values = raw_entry["size_exception_verdicts"]
        if not isinstance(size_values, list):
            raise ContractError(f"size_exception_verdicts must be a list: {path}")
        size_ids: list[str] = []
        for size_value in size_values:
            if not isinstance(size_value, dict) or set(size_value) != {
                "final_owner",
                "id",
                "verdict",
            }:
                raise ContractError(f"size verdict keys are malformed: {path}")
            size_id = size_value["id"]
            verdict = size_value["verdict"]
            final_owner = size_value["final_owner"]
            if size_id not in size_records:
                raise ContractError(f"unknown size exception ID: {size_id}")
            size_path = size_records[size_id]["path"]
            allowed_final_owners = {target["path"] for target in targets}
            allowed_size_paths = allowed_final_owners if disposition == "split" else {path}
            if size_path not in allowed_size_paths:
                raise ContractError(f"size exception linked to wrong path: {size_id}")
            if verdict not in SIZE_VERDICTS:
                raise ContractError(f"unknown size exception verdict: {size_id}")
            if disposition == "delete":
                allowed_final_owners.add(replacement_owner)
            if final_owner not in allowed_final_owners:
                raise ContractError(f"size final owner is not a target: {size_id}")
            if status == "complete" and size_path != final_owner:
                raise ContractError(f"completed size exception is not at final owner: {size_id}")
            size_ids.append(size_id)
        if size_ids != sorted(set(size_ids)):
            raise ContractError(f"size verdicts must be sorted and unique: {path}")
        if size_values and disposition != "split" and not direct_contracts:
            raise ContractError(f"large retain lacks an executable contract: {path}")

        entry_paths.append(path)
        target_paths.extend(target["path"] for target in targets)
        linked_size_ids.extend(size_ids)
        normalized_entries.append(dict(raw_entry))

    if entry_paths != sorted(set(entry_paths)):
        raise ContractError("entries must be sorted and unique by path")
    if len(entry_paths) != expected_baseline_files:
        raise ContractError("entry count does not match expected_baseline_files")
    if len(set(target_paths)) != len(target_paths):
        raise ContractError("target paths collide across disposition entries")
    if len(target_paths) != expected_target_files:
        raise ContractError("target count does not match expected_target_files")
    if sorted(linked_size_ids) != sorted(size_records):
        raise ContractError("size ledger is not classified exactly once")

    baseline_paths = set(entry_paths)
    final_target_paths = set(target_paths)
    for entry in normalized_entries:
        replacement_owner = entry["replacement_owner"]
        if replacement_owner is not None and replacement_owner not in final_target_paths:
            raise ContractError(
                f"replacement owner is not in the final target tree: {replacement_owner}"
            )
    for target_path in target_paths:
        if target_path not in baseline_paths and GENERIC_TARGET_STEM.fullmatch(
            Path(target_path).stem
        ):
            raise ContractError(f"generic target module is forbidden: {target_path}")

    return {
        "baseline_paths": tuple(entry_paths),
        "entries": tuple(normalized_entries),
        "expected_baseline_files": expected_baseline_files,
        "expected_target_files": expected_target_files,
        "owner_groups": owner_groups,
        "target_paths": tuple(target_paths),
    }


def check_current_inventory(
    inventory_document: object,
    contract: Mapping[str, object],
) -> list[dict[str, object]]:
    """Compare planned/complete targets with the current analyzer inventory."""

    if (
        not isinstance(inventory_document, dict)
        or not isinstance(inventory_document.get("inventory"), dict)
        or not isinstance(inventory_document["inventory"].get("modules"), list)
    ):
        raise ContractError("analyzer inventory is malformed")
    current_paths = {
        module["path"]
        for module in inventory_document["inventory"]["modules"]
        if isinstance(module, dict) and isinstance(module.get("path"), str)
    }
    if len(current_paths) != len(inventory_document["inventory"]["modules"]):
        raise ContractError("analyzer inventory contains duplicate or malformed paths")

    expected_current = set(contract["baseline_paths"])
    violations: list[dict[str, object]] = []
    for entry in contract["entries"]:
        path = entry["path"]
        new_targets = {
            target["path"] for target in entry["targets"] if target["path"] != path
        }
        if entry["disposition"] == "delete":
            if entry["status"] == "complete":
                expected_current.discard(path)
            continue
        if entry["status"] == "complete":
            expected_current.update(new_targets)
        else:
            present = sorted(new_targets & current_paths)
            if present:
                violations.append(
                    {
                        "rule": "planned-target-already-present",
                        "path": path,
                        "targets": present,
                    }
                )
    for path in sorted(expected_current - current_paths):
        violations.append({"rule": "classified-path-missing", "path": path})
    for path in sorted(current_paths - expected_current):
        violations.append({"rule": "unclassified-production-path", "path": path})
    return sorted(violations, key=lambda item: (str(item["path"]), item["rule"]))


def check_repository(
    root: Path = REPOSITORY_ROOT,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
) -> list[dict[str, object]]:
    document = _load_json(contract_path)
    linked = document["linked_contracts"] if isinstance(document, dict) else {}
    owner_document = _load_json(root / str(linked.get("import_owner_map", "")))
    size_document = _load_json(root / str(linked.get("size_ledger", "")))
    compatibility_text = (root / str(linked.get("compatibility_registry", ""))).read_text(
        encoding="utf-8"
    )
    contract = validate_contract(
        document,
        owner_document=owner_document,
        size_document=size_document,
        compatibility_text=compatibility_text,
        repository_root=root,
    )
    inventory_path = root / document["inventory_owner"]["path"]
    return check_current_inventory(_load_json(inventory_path), contract)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT_PATH)
    args = parser.parse_args(argv)
    try:
        violations = check_repository(args.root.resolve(), args.contract.resolve())
    except (ContractError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Python file-disposition contract error: {error}", file=sys.stderr)
        return 2
    if violations:
        for violation in violations:
            print(json.dumps(violation, sort_keys=True), file=sys.stderr)
        return 1
    print("Python file-disposition contract passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
