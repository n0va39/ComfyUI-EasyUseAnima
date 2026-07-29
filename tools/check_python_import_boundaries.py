#!/usr/bin/env python3
"""Fail on canonical owner-boundary regressions.

The checker consumes the deterministic report produced by
``analyze_python_backend.py`` and derives its production-path inventory from
the G-06 test-ownership contract. It does not import production modules,
execute repository code, access the network, or write repository state.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ANALYZER_PATH = Path(__file__).with_name("analyze_python_backend.py")
DEFAULT_CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "tests"
    / "fixtures"
    / "python_import_boundary_contract.v2.json"
)
DEFAULT_OWNER_INVENTORY_PATH = (
    REPOSITORY_ROOT
    / "tests"
    / "fixtures"
    / "python_test_ownership_contract.v1.json"
)
OWNER_INVENTORY_REFERENCE = (
    "tests/fixtures/python_test_ownership_contract.v1.json"
)
CONTRACT_SCHEMA_VERSION = 2
OWNER_INVENTORY_SCHEMA_VERSION = 1
BOUNDARY_OWNER_ISSUE = 593

ROLE_ALLOWED_TARGETS = {
    "common": frozenset({"common"}),
    "infrastructure-core": frozenset(
        {"common", "infrastructure-core"}
    ),
    "comfy-host-adapter": frozenset(
        {"common", "infrastructure-core", "comfy-host-adapter"}
    ),
    "feature-service": frozenset(
        {
            "common",
            "infrastructure-core",
            "comfy-host-adapter",
            "feature-service",
        }
    ),
    "http-adapter": frozenset(
        {
            "common",
            "infrastructure-core",
            "comfy-host-adapter",
            "feature-service",
            "http-adapter",
        }
    ),
    "node-adapter": frozenset(
        {
            "common",
            "infrastructure-core",
            "comfy-host-adapter",
            "feature-service",
            "node-adapter",
        }
    ),
    "registration-adapter": frozenset(),
    "process-composition": frozenset(
        {
            "common",
            "infrastructure-core",
            "comfy-host-adapter",
            "feature-service",
            "http-adapter",
            "node-adapter",
            "registration-adapter",
            "process-composition",
        }
    ),
}
ALLOWED_ROLES = frozenset(ROLE_ALLOWED_TARGETS)
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


def _is_canonical_selector(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("easyuse_anima/"):
        return False
    return value.endswith("/") or value.endswith(".py")


def validate_owner_inventory(
    document: object,
) -> tuple[dict[str, object], ...]:
    """Return the ordered G-06 group names and production-path selectors."""

    if not isinstance(document, dict):
        raise ContractError("owner inventory must be a JSON object")
    if document.get("schema_version") != OWNER_INVENTORY_SCHEMA_VERSION:
        raise ContractError(
            "owner inventory schema_version must be "
            f"{OWNER_INVENTORY_SCHEMA_VERSION}"
        )
    raw_groups = document.get("groups")
    if not isinstance(raw_groups, list) or not raw_groups:
        raise ContractError("owner inventory groups must be a non-empty array")

    groups: list[dict[str, object]] = []
    for index, raw_group in enumerate(raw_groups):
        if not isinstance(raw_group, dict):
            raise ContractError(f"owner groups[{index}] must be an object")
        if set(raw_group) != {"name", "owners", "production_paths"}:
            raise ContractError(
                f"owner groups[{index}] keys must be exactly: "
                "name, owners, production_paths"
            )
        name = raw_group["name"]
        production_paths = raw_group["production_paths"]
        if not isinstance(name, str) or not name.strip():
            raise ContractError(f"owner groups[{index}].name must be non-empty")
        if not isinstance(production_paths, list) or not production_paths:
            raise ContractError(
                f"owner groups[{index}].production_paths must be non-empty"
            )
        if not all(_is_canonical_selector(path) for path in production_paths):
            raise ContractError(
                f"owner groups[{index}].production_paths must be canonical paths"
            )
        if production_paths != sorted(set(production_paths)):
            raise ContractError(
                f"owner groups[{index}].production_paths must be sorted and unique"
            )
        groups.append(
            {
                "group": name,
                "production_paths": tuple(production_paths),
            }
        )

    names = [str(group["group"]) for group in groups]
    if names != sorted(set(names)):
        raise ContractError("owner inventory group names must be sorted and unique")
    return tuple(groups)


def _path_matches(path: str, selector: str) -> bool:
    if selector.endswith("/"):
        return path.startswith(selector)
    return path == selector


def _matching_groups(
    path: str,
    groups: Sequence[Mapping[str, object]],
) -> tuple[Mapping[str, object], ...]:
    candidates = [
        (group, str(selector))
        for group in groups
        for selector in cast(Sequence[object], group["production_paths"])
        if _path_matches(path, str(selector))
    ]
    if not candidates:
        return ()
    exact = [group for group, selector in candidates if selector == path]
    if exact:
        return tuple(exact)
    longest = max(len(selector) for _group, selector in candidates)
    return tuple(
        group
        for group, selector in candidates
        if len(selector) == longest
    )


def _source_group(
    path: str,
    groups: Sequence[Mapping[str, object]],
) -> Mapping[str, object] | None:
    matches = _matching_groups(path, groups)
    return matches[0] if len(matches) == 1 else None


def validate_contract(
    document: object,
    owner_inventory: object,
) -> dict[str, object]:
    """Validate v2 and attach G-06 production paths to its role records."""

    if not isinstance(document, dict):
        raise ContractError("contract must be a JSON object")
    expected_keys = {
        "edge_exceptions",
        "groups",
        "owner_inventory",
        "package_facades",
        "path_role_overrides",
        "schema_version",
    }
    if set(document) != expected_keys:
        raise ContractError(
            "contract keys must be exactly: edge_exceptions, groups, "
            "owner_inventory, package_facades, path_role_overrides, "
            "schema_version"
        )
    if type(document["schema_version"]) is not int:
        raise ContractError("schema_version must be an integer")
    if document["schema_version"] != CONTRACT_SCHEMA_VERSION:
        raise ContractError(
            f"schema_version must be {CONTRACT_SCHEMA_VERSION}"
        )

    inventory_ref = document["owner_inventory"]
    if inventory_ref != {
        "path": OWNER_INVENTORY_REFERENCE,
        "schema_version": OWNER_INVENTORY_SCHEMA_VERSION,
    }:
        raise ContractError(
            "owner_inventory must reference the exact G-06 v1 contract"
        )
    inventory_groups = validate_owner_inventory(owner_inventory)
    inventory_by_name = {
        str(group["group"]): group for group in inventory_groups
    }

    raw_groups = document["groups"]
    if not isinstance(raw_groups, list) or not raw_groups:
        raise ContractError("groups must be a non-empty array")
    groups: list[dict[str, object]] = []
    for index, raw_group in enumerate(raw_groups):
        if not isinstance(raw_group, dict):
            raise ContractError(f"groups[{index}] must be an object")
        if set(raw_group) != {"group", "role"}:
            raise ContractError(
                f"groups[{index}] keys must be exactly: group, role"
            )
        group = raw_group["group"]
        role = raw_group["role"]
        if not isinstance(group, str) or not group.strip():
            raise ContractError(f"groups[{index}].group must be non-empty")
        if role not in ALLOWED_ROLES:
            raise ContractError(
                f"groups[{index}].role must be one of: "
                f"{', '.join(sorted(ALLOWED_ROLES))}"
            )
        owner_group = inventory_by_name.get(group)
        if owner_group is None:
            raise ContractError(f"groups[{index}].group is not G-06-owned")
        groups.append(
            {
                "group": group,
                "owner_issue": BOUNDARY_OWNER_ISSUE,
                "production_paths": owner_group["production_paths"],
                "role": role,
            }
        )

    group_names = [str(group["group"]) for group in groups]
    if group_names != sorted(set(group_names)):
        raise ContractError("groups must be sorted and unique")
    if group_names != list(inventory_by_name):
        raise ContractError("groups must exactly match the G-06 owner map")

    raw_overrides = document["path_role_overrides"]
    if not isinstance(raw_overrides, list):
        raise ContractError("path_role_overrides must be an array")
    overrides: list[dict[str, object]] = []
    for index, raw_override in enumerate(raw_overrides):
        if not isinstance(raw_override, dict):
            raise ContractError(
                f"path_role_overrides[{index}] must be an object"
            )
        allowed_keys = {"allowed_target_roles", "path", "role"}
        if set(raw_override) not in ({"path", "role"}, allowed_keys):
            raise ContractError(
                f"path_role_overrides[{index}] has invalid keys"
            )
        path = raw_override["path"]
        role = raw_override["role"]
        if not _is_canonical_selector(path):
            raise ContractError(
                f"path_role_overrides[{index}].path must be canonical"
            )
        if role not in ALLOWED_ROLES:
            raise ContractError(
                f"path_role_overrides[{index}].role is invalid"
            )
        if _source_group(str(path).rstrip("/") + ("/x.py" if str(path).endswith("/") else ""), groups) is None:
            raise ContractError(
                f"path_role_overrides[{index}].path is not G-06-owned"
            )
        override: dict[str, object] = {"path": path, "role": role}
        if "allowed_target_roles" in raw_override:
            allowed_targets = raw_override["allowed_target_roles"]
            if (
                not isinstance(allowed_targets, list)
                or not allowed_targets
                or allowed_targets != sorted(set(allowed_targets))
                or not all(target in ALLOWED_ROLES for target in allowed_targets)
            ):
                raise ContractError(
                    f"path_role_overrides[{index}].allowed_target_roles "
                    "must be a sorted non-empty role set"
                )
            override["allowed_target_roles"] = tuple(allowed_targets)
        overrides.append(override)
    override_paths = [str(override["path"]) for override in overrides]
    if override_paths != sorted(set(override_paths)):
        raise ContractError("path_role_overrides must be sorted and unique")

    package_facades = document["package_facades"]
    if package_facades != {
        "nested": {
            "path_suffix": "/__init__.py",
            "rule": "same-group-only",
        },
        "root": {
            "allowed_target_groups": ["seed"],
            "path": "easyuse_anima/__init__.py",
        },
    }:
        raise ContractError("package_facades must match the reviewed exact rules")

    raw_exceptions = document["edge_exceptions"]
    if not isinstance(raw_exceptions, list):
        raise ContractError("edge_exceptions must be an array")
    exceptions: list[dict[str, str]] = []
    for index, raw_exception in enumerate(raw_exceptions):
        if not isinstance(raw_exception, dict) or set(raw_exception) != {
            "name",
            "source",
            "target",
        }:
            raise ContractError(
                f"edge_exceptions[{index}] keys must be exactly: "
                "name, source, target"
            )
        source = raw_exception["source"]
        target = raw_exception["target"]
        name = raw_exception["name"]
        if (
            not isinstance(source, str)
            or not source.startswith("easyuse_anima/")
            or not source.endswith(".py")
            or _source_group(source, groups) is None
        ):
            raise ContractError(
                f"edge_exceptions[{index}].source must be an owned module"
            )
        if (
            not isinstance(target, str)
            or not target.startswith("easyuse_anima/")
            or not target.endswith(".py")
        ):
            raise ContractError(
                f"edge_exceptions[{index}].target must be canonical"
            )
        if not isinstance(name, str) or not name.strip():
            raise ContractError(
                f"edge_exceptions[{index}].name must be non-empty"
            )
        exceptions.append({"source": source, "target": target, "name": name})
    exception_keys = [
        (exception["source"], exception["target"], exception["name"])
        for exception in exceptions
    ]
    if exception_keys != sorted(set(exception_keys)):
        raise ContractError("edge_exceptions must be sorted and unique")

    return {
        "edge_exceptions": tuple(exceptions),
        "groups": tuple(groups),
        "package_facades": package_facades,
        "path_role_overrides": tuple(overrides),
    }


def load_contract(
    path: Path = DEFAULT_CONTRACT_PATH,
    owner_inventory_path: Path = DEFAULT_OWNER_INVENTORY_PATH,
) -> dict[str, object]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        owner_inventory = json.loads(
            owner_inventory_path.read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"could not read boundary contract: {exc}") from exc
    return validate_contract(document, owner_inventory)


def _groups(contract: Mapping[str, object]) -> tuple[dict[str, object], ...]:
    return cast(tuple[dict[str, object], ...], contract["groups"])


def _overrides(contract: Mapping[str, object]) -> tuple[dict[str, object], ...]:
    return cast(
        tuple[dict[str, object], ...],
        contract["path_role_overrides"],
    )


def _module_path_index(report: Mapping[str, object]) -> dict[str, str]:
    inventory = cast(Mapping[str, object], report["inventory"])
    modules = cast(Sequence[Mapping[str, object]], inventory["modules"])
    return {
        str(module["module"]): str(module["path"])
        for module in modules
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
    imports = cast(Mapping[str, object], report["imports"])
    edges = cast(Sequence[Mapping[str, object]], imports["edges"])
    graph_edges = sorted(
        {
            (str(edge["source"]), target)
            for edge in edges
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


def _matching_override(
    path: str,
    contract: Mapping[str, object],
) -> Mapping[str, object] | None:
    candidates = [
        override
        for override in _overrides(contract)
        if _path_matches(path, str(override["path"]))
    ]
    if not candidates:
        return None
    exact = [override for override in candidates if override["path"] == path]
    if exact:
        return exact[0]
    return max(candidates, key=lambda override: len(str(override["path"])))


def _path_role(
    path: str,
    contract: Mapping[str, object],
) -> str | None:
    override = _matching_override(path, contract)
    if override is not None:
        return str(override["role"])
    group = _source_group(path, _groups(contract))
    return None if group is None else str(group["role"])


def _allowed_target_roles(
    source: str,
    contract: Mapping[str, object],
) -> frozenset[str]:
    override = _matching_override(source, contract)
    if override is not None and "allowed_target_roles" in override:
        return frozenset(
            cast(Sequence[str], override["allowed_target_roles"])
        )
    role = _path_role(source, contract)
    return ROLE_ALLOWED_TARGETS.get(role or "", frozenset())


def _is_exact_edge_exception(
    edge: Mapping[str, object],
    source: str,
    target: str,
    contract: Mapping[str, object],
) -> bool:
    exceptions = cast(
        Sequence[Mapping[str, object]],
        contract["edge_exceptions"],
    )
    return any(
        exception["source"] == source
        and exception["target"] == target
        and exception["name"] == edge.get("name")
        for exception in exceptions
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
    group: Mapping[str, object] | None,
) -> dict[str, object]:
    return {
        "source": source,
        "line": line,
        "rule": rule,
        "target": target,
        "group": "unowned" if group is None else group["group"],
        "owner_issue": (
            BOUNDARY_OWNER_ISSUE
            if group is None
            else group.get("owner_issue", BOUNDARY_OWNER_ISSUE)
        ),
    }


def _group_for_violation(
    path: str,
    contract: Mapping[str, object],
) -> Mapping[str, object] | None:
    group = _source_group(path, _groups(contract))
    if group is not None:
        return group
    root_rule = cast(
        Mapping[str, object],
        cast(Mapping[str, object], contract["package_facades"])["root"],
    )
    if path == root_rule["path"]:
        return {
            "group": "package-facade",
            "owner_issue": BOUNDARY_OWNER_ISSUE,
        }
    return None


def _owner_map_violations(
    report: Mapping[str, object],
    contract: Mapping[str, object],
    *,
    require_complete_owner_map: bool,
) -> list[dict[str, object]]:
    violations: list[dict[str, object]] = []
    module_paths = _module_path_index(report)
    paths = sorted(
        path for path in module_paths.values() if path.startswith("easyuse_anima/")
    )
    package_facades = cast(Mapping[str, object], contract["package_facades"])
    root_rule = cast(Mapping[str, object], package_facades["root"])
    root_path = str(root_rule["path"])

    for path in paths:
        if path == root_path:
            continue
        matches = _matching_groups(path, _groups(contract))
        if not matches:
            violations.append(
                _violation(
                    source=path,
                    line=0,
                    rule="unowned-production-path",
                    target=path,
                    group=None,
                )
            )
        elif len(matches) > 1:
            violations.append(
                _violation(
                    source=path,
                    line=0,
                    rule="ambiguous-production-owner",
                    target=",".join(str(group["group"]) for group in matches),
                    group=None,
                )
            )

    if not require_complete_owner_map:
        return violations

    if root_path not in paths:
        violations.append(
            _violation(
                source=root_path,
                line=0,
                rule="package-facade-contract-drift",
                target="missing-root-facade",
                group=None,
            )
        )
    for group in _groups(contract):
        for selector in cast(Sequence[object], group["production_paths"]):
            selector_text = str(selector)
            if not any(_path_matches(path, selector_text) for path in paths):
                violations.append(
                    _violation(
                        source=selector_text,
                        line=0,
                        rule="owner-path-empty",
                        target=selector_text,
                        group=group,
                    )
                )
    return violations


def _package_facade_allows(
    source: str,
    target: str,
    contract: Mapping[str, object],
) -> bool | None:
    package_facades = cast(Mapping[str, object], contract["package_facades"])
    root_rule = cast(Mapping[str, object], package_facades["root"])
    nested_rule = cast(Mapping[str, object], package_facades["nested"])
    target_group = _source_group(target, _groups(contract))
    if source == root_rule["path"]:
        return target_group is not None and target_group["group"] in cast(
            Sequence[str], root_rule["allowed_target_groups"]
        )
    if not source.endswith(str(nested_rule["path_suffix"])):
        return None
    source_group = _source_group(source, _groups(contract))
    return (
        source_group is not None
        and target_group is not None
        and source_group["group"] == target_group["group"]
    )


def check_report(
    report: Mapping[str, object],
    contract: Mapping[str, object],
    *,
    require_complete_owner_map: bool = False,
) -> list[dict[str, object]]:
    """Return deterministic complete-owner boundary violations."""

    violations = _owner_map_violations(
        report,
        contract,
        require_complete_owner_map=require_complete_owner_map,
    )
    module_paths = _module_path_index(report)
    imports = cast(Mapping[str, object], report["imports"])
    edges = cast(Sequence[Mapping[str, object]], imports["edges"])
    seen_exceptions: set[tuple[str, str, str]] = set()

    for edge in edges:
        source = str(edge["source"])
        if not source.startswith("easyuse_anima/"):
            continue
        source_group = _source_group(source, _groups(contract))
        facade_rule = source.endswith("/__init__.py")
        if source_group is None and not facade_rule:
            continue
        target = _local_target(edge, module_paths)
        if target is not None and not target.startswith("easyuse_anima/"):
            violations.append(
                _violation(
                    source=source,
                    line=int(edge["line"]),
                    rule="canonical-imports-root",
                    target=target,
                    group=_group_for_violation(source, contract),
                )
            )
        elif target is not None:
            facade_allowed = _package_facade_allows(source, target, contract)
            if facade_allowed is False:
                violations.append(
                    _violation(
                        source=source,
                        line=int(edge["line"]),
                        rule="role-back-reference",
                        target=target,
                        group=_group_for_violation(source, contract),
                    )
                )
            elif facade_allowed is None:
                target_role = _path_role(target, contract)
                exception = _is_exact_edge_exception(
                    edge,
                    source,
                    target,
                    contract,
                )
                if exception:
                    seen_exceptions.add(
                        (source, target, str(edge.get("name", "")))
                    )
                if (
                    target_role is None
                    or (
                        target_role not in _allowed_target_roles(source, contract)
                        and not exception
                    )
                ):
                    violations.append(
                        _violation(
                            source=source,
                            line=int(edge["line"]),
                            rule="role-back-reference",
                            target=target,
                            group=_group_for_violation(source, contract),
                        )
                    )
        if edge.get("role") == "compatibility_fallback":
            violations.append(
                _violation(
                    source=source,
                    line=int(edge["line"]),
                    rule="compatibility-fallback",
                    target=target or str(edge.get("imported", "<unknown>")),
                    group=_group_for_violation(source, contract),
                )
            )

    if require_complete_owner_map:
        exceptions = cast(
            Sequence[Mapping[str, object]],
            contract["edge_exceptions"],
        )
        for exception in exceptions:
            key = (
                str(exception["source"]),
                str(exception["target"]),
                str(exception["name"]),
            )
            if key not in seen_exceptions:
                violations.append(
                    _violation(
                        source=key[0],
                        line=0,
                        rule="edge-exception-unused",
                        target=f"{key[1]}:{key[2]}",
                        group=_group_for_violation(key[0], contract),
                    )
                )

    for component in _local_sccs(report, module_paths):
        if not component.get("cyclic"):
            continue
        members = [str(member) for member in component["modules"]]
        cycle_target = " -> ".join((*members, members[0]))
        for source in members:
            if not source.startswith("easyuse_anima/"):
                continue
            violations.append(
                _violation(
                    source=source,
                    line=0,
                    rule="cyclic-runtime-scc",
                    target=cycle_target,
                    group=_group_for_violation(source, contract),
                )
            )

    side_effects = cast(Mapping[str, object], report["side_effects"])
    candidates = cast(
        Sequence[Mapping[str, object]],
        side_effects["candidates"],
    )
    for candidate in candidates:
        source = str(candidate["module"])
        if (
            not source.startswith("easyuse_anima/")
            or not _is_registration_side_effect(candidate)
        ):
            continue
        violations.append(
            _violation(
                source=source,
                line=int(candidate["line"]),
                rule="registration-side-effect",
                target=str(candidate["callee"]),
                group=_group_for_violation(source, contract),
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
    owner_inventory_path: Path = DEFAULT_OWNER_INVENTORY_PATH,
) -> list[dict[str, object]]:
    contract = load_contract(contract_path, owner_inventory_path)
    report = analyzer.analyze_repository(root)
    return check_report(report, contract, require_complete_owner_map=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT_PATH)
    parser.add_argument(
        "--owner-inventory",
        type=Path,
        default=DEFAULT_OWNER_INVENTORY_PATH,
    )
    args = parser.parse_args(argv)

    try:
        contract = load_contract(args.contract, args.owner_inventory)
        report = analyzer.analyze_repository(args.root)
        violations = check_report(
            report,
            contract,
            require_complete_owner_map=True,
        )
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
        f"{len(_groups(contract))} canonical owner groups, 0 violations."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
