#!/usr/bin/env python3
"""Enforce the reviewed Python size and function-line growth ratchet.

The checker consumes metrics from ``analyze_python_backend.py`` and a compact
ledger of current threshold overages.  It does not maintain a second source
inventory, import production modules, invoke Git, or write repository state.
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
    / "python_size_complexity_contract.v1.json"
)
CONTRACT_SCHEMA_VERSION = 1
EXPECTED_THRESHOLDS = {
    "adapter_module_lines": 400,
    "function_lines": 120,
    "module_lines": 800,
}
EXPECTED_ADAPTER_EXACT_PATHS = (
    "__init__.py",
    "api.py",
    "easyuse_anima/bootstrap.py",
    "easyuse_anima/registration.py",
    "nodes.py",
)
EXPECTED_ADAPTER_PREFIXES = (
    "easyuse_anima/api/",
    "easyuse_anima/infrastructure/",
    "easyuse_anima/nodes/",
)


class ContractError(ValueError):
    """The checked-in size ledger is invalid or weaker than G-05A."""


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


def _require_sorted_unique_strings(values: object, *, field: str) -> tuple[str, ...]:
    if not isinstance(values, list) or not all(
        isinstance(value, str) and value for value in values
    ):
        raise ContractError(f"{field} must be a list of non-empty strings")
    if values != sorted(set(values)):
        raise ContractError(f"{field} must be sorted and unique")
    return tuple(values)


def _is_adapter_path(
    path: str,
    *,
    exact_paths: Sequence[str],
    prefixes: Sequence[str],
) -> bool:
    return path in exact_paths or path.startswith(tuple(prefixes))


def _validate_exception_record(
    record: object,
    *,
    function: bool,
) -> dict[str, object]:
    expected_keys = {
        "baseline_loc",
        "decomposition_boundary",
        "owner_issue",
        "path",
    }
    if function:
        expected_keys.add("qualified_name")
    if not isinstance(record, dict) or set(record) != expected_keys:
        label = "function" if function else "module"
        raise ContractError(f"{label} exception keys do not match the contract")

    path = record["path"]
    if not isinstance(path, str) or not path.endswith(".py"):
        raise ContractError("exception path must be a production Python path")
    if function:
        qualified_name = record["qualified_name"]
        if not isinstance(qualified_name, str) or not qualified_name:
            raise ContractError("qualified_name must be a non-empty string")
    baseline_loc = record["baseline_loc"]
    if type(baseline_loc) is not int or baseline_loc <= 0:
        raise ContractError("baseline_loc must be a positive integer")
    owner_issue = record["owner_issue"]
    if type(owner_issue) is not int or owner_issue <= 0:
        raise ContractError("owner_issue must be a positive integer")
    boundary = record["decomposition_boundary"]
    if not isinstance(boundary, str) or len(boundary.strip()) < 20:
        raise ContractError("decomposition_boundary must name a concrete boundary")
    return dict(record)


def validate_contract(document: object) -> dict[str, object]:
    """Validate and normalize the reviewed G-05A ledger."""

    expected_keys = {
        "adapter_paths",
        "function_exceptions",
        "module_exceptions",
        "schema_version",
        "thresholds",
    }
    if not isinstance(document, dict) or set(document) != expected_keys:
        raise ContractError("contract keys do not match the G-05A schema")
    if (
        type(document["schema_version"]) is not int
        or document["schema_version"] != CONTRACT_SCHEMA_VERSION
    ):
        raise ContractError("unsupported size contract schema_version")
    thresholds = document["thresholds"]
    if (
        not isinstance(thresholds, dict)
        or any(type(value) is not int for value in thresholds.values())
        or thresholds != EXPECTED_THRESHOLDS
    ):
        raise ContractError("size thresholds must remain 800/400/120 review triggers")

    adapter_paths = document["adapter_paths"]
    if not isinstance(adapter_paths, dict) or set(adapter_paths) != {
        "exact",
        "prefixes",
    }:
        raise ContractError("adapter_paths keys must be exactly exact and prefixes")
    exact_paths = _require_sorted_unique_strings(
        adapter_paths["exact"],
        field="adapter_paths.exact",
    )
    prefixes = _require_sorted_unique_strings(
        adapter_paths["prefixes"],
        field="adapter_paths.prefixes",
    )
    if any(not path.endswith(".py") for path in exact_paths):
        raise ContractError("adapter exact paths must end in .py")
    if any(not prefix.endswith("/") for prefix in prefixes):
        raise ContractError("adapter prefixes must end in /")
    if any(path.startswith(tuple(prefixes)) for path in exact_paths):
        raise ContractError("adapter exact paths must not duplicate a prefix")
    if (
        exact_paths != EXPECTED_ADAPTER_EXACT_PATHS
        or prefixes != EXPECTED_ADAPTER_PREFIXES
    ):
        raise ContractError("adapter classification must match the reviewed G-05A set")

    module_records = document["module_exceptions"]
    function_records = document["function_exceptions"]
    if not isinstance(module_records, list) or not isinstance(function_records, list):
        raise ContractError("exception ledgers must be lists")
    modules = [
        _validate_exception_record(record, function=False)
        for record in module_records
    ]
    functions = [
        _validate_exception_record(record, function=True)
        for record in function_records
    ]
    module_keys = [str(record["path"]) for record in modules]
    function_keys = [
        (str(record["path"]), str(record["qualified_name"]))
        for record in functions
    ]
    if module_keys != sorted(set(module_keys)):
        raise ContractError("module exceptions must be sorted and unique by path")
    if function_keys != sorted(set(function_keys)):
        raise ContractError(
            "function exceptions must be sorted and unique by path and qualified_name"
        )

    for record in modules:
        path = str(record["path"])
        threshold = (
            EXPECTED_THRESHOLDS["adapter_module_lines"]
            if _is_adapter_path(path, exact_paths=exact_paths, prefixes=prefixes)
            else EXPECTED_THRESHOLDS["module_lines"]
        )
        if int(record["baseline_loc"]) <= threshold:
            raise ContractError("module exceptions must exceed their review threshold")
    if any(
        int(record["baseline_loc"]) <= EXPECTED_THRESHOLDS["function_lines"]
        for record in functions
    ):
        raise ContractError("function exceptions must exceed the function threshold")

    return {
        "adapter_paths": {"exact": exact_paths, "prefixes": prefixes},
        "function_exceptions": tuple(functions),
        "module_exceptions": tuple(modules),
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "thresholds": dict(EXPECTED_THRESHOLDS),
    }


def check_report(
    report: Mapping[str, object],
    contract: Mapping[str, object],
) -> list[dict[str, object]]:
    """Return deterministic overage-growth and stale-ledger violations."""

    adapter_paths = contract["adapter_paths"]
    exact_paths = tuple(adapter_paths["exact"])
    prefixes = tuple(adapter_paths["prefixes"])
    module_exceptions = {
        str(record["path"]): record
        for record in contract["module_exceptions"]
    }
    function_exceptions = {
        (str(record["path"]), str(record["qualified_name"])): record
        for record in contract["function_exceptions"]
    }
    modules = report["inventory"]["modules"]
    modules_by_path = {str(module["path"]): module for module in modules}
    functions_by_key = {
        (str(module["path"]), str(function["qualified_name"])): function
        for module in modules
        for function in module["functions"]
    }
    violations: list[dict[str, object]] = []

    for path, exception in module_exceptions.items():
        if path not in modules_by_path:
            violations.append(
                {
                    "rule": "stale-module-exception",
                    "path": path,
                    "symbol": "<module>",
                    "current_loc": None,
                    "baseline_loc": exception["baseline_loc"],
                }
            )
    for key, exception in function_exceptions.items():
        if key not in functions_by_key:
            violations.append(
                {
                    "rule": "stale-function-exception",
                    "path": key[0],
                    "symbol": key[1],
                    "current_loc": None,
                    "baseline_loc": exception["baseline_loc"],
                }
            )

    for path, module in modules_by_path.items():
        threshold = (
            EXPECTED_THRESHOLDS["adapter_module_lines"]
            if _is_adapter_path(path, exact_paths=exact_paths, prefixes=prefixes)
            else EXPECTED_THRESHOLDS["module_lines"]
        )
        current_loc = int(module["loc"])
        if current_loc <= threshold:
            continue
        exception = module_exceptions.get(path)
        if exception is None:
            violations.append(
                {
                    "rule": "unreviewed-module-overage",
                    "path": path,
                    "symbol": "<module>",
                    "current_loc": current_loc,
                    "baseline_loc": threshold,
                }
            )
        elif current_loc > int(exception["baseline_loc"]):
            violations.append(
                {
                    "rule": "module-overage-growth",
                    "path": path,
                    "symbol": "<module>",
                    "current_loc": current_loc,
                    "baseline_loc": exception["baseline_loc"],
                }
            )

    function_threshold = EXPECTED_THRESHOLDS["function_lines"]
    for (path, qualified_name), function in functions_by_key.items():
        current_loc = int(function["loc"])
        if current_loc <= function_threshold:
            continue
        exception = function_exceptions.get((path, qualified_name))
        if exception is None:
            violations.append(
                {
                    "rule": "unreviewed-function-overage",
                    "path": path,
                    "symbol": qualified_name,
                    "current_loc": current_loc,
                    "baseline_loc": function_threshold,
                }
            )
        elif current_loc > int(exception["baseline_loc"]):
            violations.append(
                {
                    "rule": "function-overage-growth",
                    "path": path,
                    "symbol": qualified_name,
                    "current_loc": current_loc,
                    "baseline_loc": exception["baseline_loc"],
                }
            )

    return sorted(
        violations,
        key=lambda item: (str(item["path"]), str(item["symbol"]), str(item["rule"])),
    )


def check_repository(
    root: Path = REPOSITORY_ROOT,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
) -> list[dict[str, object]]:
    document = json.loads(contract_path.read_text(encoding="utf-8"))
    contract = validate_contract(document)
    return check_report(analyzer.analyze_repository(root), contract)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT_PATH)
    args = parser.parse_args(argv)

    try:
        violations = check_repository(args.root.resolve(), args.contract.resolve())
    except (ContractError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Python size/complexity contract error: {error}", file=sys.stderr)
        return 2
    if violations:
        for violation in violations:
            print(
                f"{violation['rule']}: {violation['path']}::"
                f"{violation['symbol']} current={violation['current_loc']} "
                f"baseline={violation['baseline_loc']}",
                file=sys.stderr,
            )
        return 1
    print("Python size/complexity ratchet passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
