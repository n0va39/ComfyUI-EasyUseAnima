#!/usr/bin/env python3
"""Fail on reviewed import-boundary regressions in completed packages.

The checker consumes the deterministic report produced by
``analyze_python_backend.py``.  It does not import production modules, execute
repository code, access the network, or write repository state.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ANALYZER_PATH = Path(__file__).with_name("analyze_python_backend.py")
DEFAULT_CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "tests"
    / "fixtures"
    / "python_import_boundary_contract.v1.json"
)
CONTRACT_SCHEMA_VERSION = 1
EXPECTED_GROUPS = (
    ("autocomplete", 162, "easyuse_anima/autocomplete/", "feature"),
    ("common", 184, "easyuse_anima/common/", "common"),
    ("image", 184, "easyuse_anima/image/", "feature"),
    (
        "infrastructure-comfy",
        184,
        "easyuse_anima/infrastructure/comfy/",
        "infrastructure",
    ),
    (
        "infrastructure-filesystem",
        186,
        "easyuse_anima/infrastructure/filesystem/",
        "infrastructure",
    ),
    ("lora", 184, "easyuse_anima/lora/", "feature"),
    ("naia", 184, "easyuse_anima/naia/", "feature"),
    ("profiles", 163, "easyuse_anima/profiles/", "feature"),
    ("settings", 186, "easyuse_anima/settings/", "feature"),
    ("translation", 186, "easyuse_anima/translation/", "feature"),
)
ALLOWED_ROLES = frozenset({"common", "feature", "infrastructure"})
BACK_REFERENCE_PREFIXES_BY_ROLE = {
    role: (
        "easyuse_anima/api/routes/",
        "easyuse_anima/nodes/",
    )
    for role in ALLOWED_ROLES
}
BACK_REFERENCE_EXACT = frozenset(
    {
        "easyuse_anima/bootstrap.py",
        "easyuse_anima/registration.py",
    }
)
REGISTRATION_SIDE_EFFECT_KINDS = frozenset(
    {"route_registration", "route_registry_creation"}
)
MAPPING_MUTATION_METHODS = frozenset(
    {"clear", "pop", "popitem", "setdefault", "update"}
)


class ContractError(ValueError):
    """The checked-in boundary ledger is invalid or weaker than expected."""


def _load_analyzer():
    spec = importlib.util.spec_from_file_location(
        "easyuse_anima_python_backend_analyzer",
        ANALYZER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load analyzer: {ANALYZER_PATH.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


analyzer = _load_analyzer()


def validate_contract(document: object) -> tuple[dict[str, object], ...]:
    """Validate the ledger and return its immutable ordered group records."""

    if not isinstance(document, dict):
        raise ContractError("contract must be a JSON object")
    if set(document) != {"schema_version", "groups"}:
        raise ContractError("contract keys must be exactly: groups, schema_version")
    if type(document["schema_version"]) is not int:
        raise ContractError("schema_version must be an integer")
    if document["schema_version"] != CONTRACT_SCHEMA_VERSION:
        raise ContractError(
            f"schema_version must be {CONTRACT_SCHEMA_VERSION}"
        )

    raw_groups = document["groups"]
    if not isinstance(raw_groups, list) or not raw_groups:
        raise ContractError("groups must be a non-empty array")

    groups: list[dict[str, object]] = []
    expected_keys = {"group", "owner_issue", "prefix", "role"}
    for index, raw_group in enumerate(raw_groups):
        if not isinstance(raw_group, dict):
            raise ContractError(f"groups[{index}] must be an object")
        if set(raw_group) != expected_keys:
            raise ContractError(
                f"groups[{index}] keys must be exactly: "
                "group, owner_issue, prefix, role"
            )
        group = raw_group["group"]
        owner_issue = raw_group["owner_issue"]
        prefix = raw_group["prefix"]
        role = raw_group["role"]
        if not isinstance(group, str) or not group.strip():
            raise ContractError(f"groups[{index}].group must be non-empty")
        if type(owner_issue) is not int or owner_issue <= 0:
            raise ContractError(
                f"groups[{index}].owner_issue must be a positive integer"
            )
        if (
            not isinstance(prefix, str)
            or not prefix.startswith("easyuse_anima/")
            or not prefix.endswith("/")
        ):
            raise ContractError(
                f"groups[{index}].prefix must be a canonical package prefix"
            )
        if role not in ALLOWED_ROLES:
            raise ContractError(
                f"groups[{index}].role must be one of: "
                f"{', '.join(sorted(ALLOWED_ROLES))}"
            )
        groups.append(
            {
                "group": group,
                "owner_issue": owner_issue,
                "prefix": prefix,
                "role": role,
            }
        )

    group_ids = [str(group["group"]) for group in groups]
    prefixes = [str(group["prefix"]) for group in groups]
    if group_ids != sorted(group_ids):
        raise ContractError("groups must be sorted by group id")
    if len(group_ids) != len(set(group_ids)):
        raise ContractError("group ids must be unique")
    if len(prefixes) != len(set(prefixes)):
        raise ContractError("group prefixes must be unique")

    actual = tuple(
        (
            str(group["group"]),
            int(group["owner_issue"]),
            str(group["prefix"]),
            str(group["role"]),
        )
        for group in groups
    )
    if actual != EXPECTED_GROUPS:
        raise ContractError(
            "groups must exactly match the reviewed completed-package set"
        )
    return tuple(groups)


def load_contract(path: Path = DEFAULT_CONTRACT_PATH) -> tuple[dict[str, object], ...]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"could not read contract {path}: {exc}") from exc
    return validate_contract(document)


def _source_group(
    path: str,
    groups: Sequence[Mapping[str, object]],
) -> Mapping[str, object] | None:
    return next(
        (
            group
            for group in groups
            if path.startswith(str(group["prefix"]))
        ),
        None,
    )


def _module_path_index(report: Mapping[str, object]) -> dict[str, str]:
    inventory = report["inventory"]
    return {
        str(module["module"]): str(module["path"])
        for module in inventory["modules"]
    }


def _local_target(
    edge: Mapping[str, object],
    module_paths: Mapping[str, str],
) -> str | None:
    target = edge.get("target")
    if isinstance(target, str):
        return target

    requested = edge.get("requested")
    if not isinstance(requested, str) or not requested or requested.startswith("."):
        return None
    options = []
    imported_name = edge.get("name")
    if isinstance(imported_name, str) and imported_name != "*":
        options.append(f"{requested}.{imported_name}")
    options.append(requested)
    return next(
        (module_paths[option] for option in options if option in module_paths),
        None,
    )


def _local_sccs(
    report: Mapping[str, object],
    module_paths: Mapping[str, str],
) -> list[dict[str, object]]:
    """Complete the analyzer runtime graph with exact absolute local targets."""

    shipped_paths = sorted(set(module_paths.values()))
    shipped_set = set(shipped_paths)
    imports = report["imports"]
    graph_edges = sorted(
        {
            (str(edge["source"]), target)
            for edge in imports["edges"]
            if analyzer._is_runtime_relevant_edge(edge)
            for target in [_local_target(edge, module_paths)]
            if target is not None
            and str(edge["source"]) in shipped_set
            and target in shipped_set
        }
    )
    return analyzer._strongly_connected_components(
        shipped_paths,
        [
            {"from": source, "to": target}
            for source, target in graph_edges
        ],
    )


def _is_role_back_reference(role: str, target: str) -> bool:
    return target in BACK_REFERENCE_EXACT or target.startswith(
        BACK_REFERENCE_PREFIXES_BY_ROLE[role]
    )


def _is_registration_side_effect(candidate: Mapping[str, object]) -> bool:
    if candidate.get("kind") in REGISTRATION_SIDE_EFFECT_KINDS:
        return True
    callee = str(candidate.get("callee", ""))
    tail = callee.rsplit(".", 1)[-1].lower()
    if tail == "register" or tail.startswith("register_") or tail.endswith("_register"):
        return True
    owner, separator, method = callee.rpartition(".")
    owner_tail = owner.rsplit(".", 1)[-1]
    return bool(
        separator
        and method.lower() in MAPPING_MUTATION_METHODS
        and owner_tail.isupper()
        and (
            owner_tail in {"MAPPINGS", "REGISTRY"}
            or owner_tail.endswith(("_MAPPINGS", "_REGISTRY"))
        )
    )


def _violation(
    *,
    source: str,
    line: int,
    rule: str,
    target: str,
    group: Mapping[str, object],
) -> dict[str, object]:
    return {
        "source": source,
        "line": line,
        "rule": rule,
        "target": target,
        "group": group["group"],
        "owner_issue": group["owner_issue"],
    }


def check_report(
    report: Mapping[str, object],
    groups: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Return deterministic completed-package boundary violations."""

    violations: list[dict[str, object]] = []
    module_paths = _module_path_index(report)
    imports = report["imports"]
    for edge in imports["edges"]:
        source = str(edge["source"])
        group = _source_group(source, groups)
        if group is None:
            continue
        target = _local_target(edge, module_paths)
        if target is not None and not target.startswith("easyuse_anima/"):
            violations.append(
                _violation(
                    source=source,
                    line=int(edge["line"]),
                    rule="canonical-imports-root",
                    target=target,
                    group=group,
                )
            )
        if target is not None and _is_role_back_reference(
            str(group["role"]),
            target,
        ):
            violations.append(
                _violation(
                    source=source,
                    line=int(edge["line"]),
                    rule="role-back-reference",
                    target=target,
                    group=group,
                )
            )
        if edge.get("role") == "compatibility_fallback":
            violations.append(
                _violation(
                    source=source,
                    line=int(edge["line"]),
                    rule="compatibility-fallback",
                    target=target or str(edge.get("imported", "<unknown>")),
                    group=group,
                )
            )

    for component in _local_sccs(report, module_paths):
        if not component.get("cyclic"):
            continue
        members = [str(member) for member in component["modules"]]
        cycle_target = " -> ".join((*members, members[0]))
        for source in members:
            group = _source_group(source, groups)
            if group is not None:
                violations.append(
                    _violation(
                        source=source,
                        line=0,
                        rule="cyclic-runtime-scc",
                        target=cycle_target,
                        group=group,
                    )
                )

    side_effects = report["side_effects"]
    for candidate in side_effects["candidates"]:
        source = str(candidate["module"])
        group = _source_group(source, groups)
        if group is None or not _is_registration_side_effect(candidate):
            continue
        violations.append(
            _violation(
                source=source,
                line=int(candidate["line"]),
                rule="registration-side-effect",
                target=str(candidate["callee"]),
                group=group,
            )
        )

    violations.sort(
        key=lambda item: (
            str(item["source"]),
            int(item["line"]),
            str(item["rule"]),
            str(item["target"]),
        )
    )
    return violations


def check_repository(
    root: Path = REPOSITORY_ROOT,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
) -> list[dict[str, object]]:
    groups = load_contract(contract_path)
    report = analyzer.analyze_repository(root)
    return check_report(report, groups)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT_PATH)
    args = parser.parse_args(argv)

    try:
        groups = load_contract(args.contract)
        report = analyzer.analyze_repository(args.root)
        violations = check_report(report, groups)
    except (ContractError, OSError, SyntaxError, ValueError, KeyError, TypeError) as exc:
        print(f"python-import-boundary: checker-error: {exc}", file=sys.stderr)
        return 2

    if violations:
        for violation in violations:
            line = violation["line"] or "scc"
            print(
                f"{violation['source']}:{line}: rule={violation['rule']} "
                f"target={violation['target']} group={violation['group']} "
                f"owner=#{violation['owner_issue']}",
                file=sys.stderr,
            )
        print(
            f"Python import boundary gate failed: {len(violations)} violation(s).",
            file=sys.stderr,
        )
        return 1

    print(
        "Python import boundary gate passed: "
        f"{len(groups)} completed package groups, 0 violations."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
