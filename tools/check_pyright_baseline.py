from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = ROOT / "tests" / "fixtures" / "pyright_baseline.json"
DEFAULT_CONFIG = ROOT / "pyrightconfig.json"
BASELINE_SCHEMA = "easyuse_anima_pyright_diagnostic_baseline"
BASELINE_VERSION = 2
SEVERITIES = ("error", "warning", "information")
CONFIG_FIELDS = {
    "include": "include",
    "python_platform": "pythonPlatform",
    "python_version": "pythonVersion",
    "report_missing_module_source": "reportMissingModuleSource",
    "strict": "strict",
    "type_checking_mode": "typeCheckingMode",
}
STRICT_GROUP_FIELDS = frozenset({"group", "owner_issue", "paths"})


def _require_mapping(value, label: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object.")
    return value


def _require_non_negative_int(value, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer.")
    return value


def _require_non_empty_string(value, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string.")
    return value


def _require_positive_int(value, label: str) -> int:
    result = _require_non_negative_int(value, label)
    if result == 0:
        raise ValueError(f"{label} must be a positive integer.")
    return result


def _require_non_empty_string_array(value, label: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise ValueError(f"{label} must be a non-empty string array.")
    return value


def _require_strict_path(value, label: str) -> str:
    path = Path(_require_non_empty_string(value, label))
    if (
        path.is_absolute()
        or ".." in path.parts
        or path.as_posix() != value
        or len(path.parts) < 2
        or path.parts[0] != "easyuse_anima"
        or path.suffix != ".py"
    ):
        raise ValueError(
            f"{label} must be a canonical Python path under easyuse_anima."
        )
    return value


def _normalize_strict_groups(
    value,
    repo_root: Path,
) -> list[dict[str, object]]:
    if not isinstance(value, list) or not value:
        raise ValueError("Pyright baseline strict_groups must be a non-empty array.")

    normalized: list[dict[str, object]] = []
    group_ids: set[str] = set()
    owned_paths: set[str] = set()
    for index, group_value in enumerate(value):
        group = _require_mapping(group_value, f"strict_groups[{index}]")
        if set(group) != STRICT_GROUP_FIELDS:
            raise ValueError(
                f"strict_groups[{index}] fields changed: "
                f"expected {sorted(STRICT_GROUP_FIELDS)}, got {sorted(group)}"
            )
        group_id = _require_non_empty_string(
            group["group"],
            f"strict_groups[{index}].group",
        )
        owner_issue = _require_positive_int(
            group["owner_issue"],
            f"strict_groups[{index}].owner_issue",
        )
        if group_id in group_ids:
            raise ValueError(f"Duplicate Pyright strict group id: {group_id}")
        group_ids.add(group_id)

        raw_paths = _require_non_empty_string_array(
            group["paths"],
            f"strict_groups[{index}].paths",
        )
        paths = [
            _require_strict_path(path, f"strict_groups[{index}].paths[{path!r}]")
            for path in raw_paths
        ]
        if len(paths) != len(set(paths)):
            raise ValueError(
                f"strict_groups[{index}].paths must not contain duplicates."
            )
        if paths != sorted(paths):
            raise ValueError(f"strict_groups[{index}].paths must be sorted.")
        missing_paths = [path for path in paths if not (repo_root / path).is_file()]
        if missing_paths:
            raise ValueError(
                "Pyright strict paths must exist in the repository: "
                f"{missing_paths}"
            )
        duplicate_paths = owned_paths.intersection(paths)
        if duplicate_paths:
            raise ValueError(
                "Pyright strict paths must have exactly one owner: "
                f"{sorted(duplicate_paths)}"
            )
        owned_paths.update(paths)
        normalized.append(
            {"group": group_id, "owner_issue": owner_issue, "paths": paths}
        )
    return normalized


def _normalize_baseline_config(value) -> dict:
    config = _require_mapping(value, "Pyright baseline config")
    expected_fields = set(CONFIG_FIELDS)
    if set(config) != expected_fields:
        raise ValueError(
            "Pyright baseline config fields changed: "
            f"expected {sorted(expected_fields)}, got {sorted(config)}"
        )

    normalized = {
        "include": _require_non_empty_string_array(
            config["include"],
            "Pyright baseline config.include",
        ),
        "strict": _require_non_empty_string_array(
            config["strict"],
            "Pyright baseline config.strict",
        ),
    }
    for field in expected_fields - {"include", "strict"}:
        normalized[field] = _require_non_empty_string(
            config[field],
            f"Pyright baseline config.{field}",
        )
    return normalized


def _compare_config(pyright_config: dict, expected_config: dict) -> list[str]:
    config = _require_mapping(pyright_config, "Pyright config")
    expected_pyright_fields = set(CONFIG_FIELDS.values())
    failures: list[str] = []

    if set(config) != expected_pyright_fields:
        failures.append(
            "Pyright config fields changed: "
            f"expected {sorted(expected_pyright_fields)}, got {sorted(config)}"
        )

    for baseline_field, pyright_field in CONFIG_FIELDS.items():
        expected_value = expected_config[baseline_field]
        actual_value = config.get(pyright_field)
        if actual_value != expected_value:
            failures.append(
                f"Pyright config {pyright_field} changed: "
                f"expected {expected_value!r}, got {actual_value!r}"
            )
    return failures


def _relative_diagnostic_path(value, repo_root: Path) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("Pyright diagnostic file must be a non-empty string.")
    path = Path(value)
    if not path.is_absolute():
        path = repo_root / path
    try:
        relative = path.resolve().relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError(f"Pyright diagnostic is outside the repository: {value}") from exc
    return relative.as_posix()


def summarize_report(report: dict, repo_root: Path = ROOT) -> dict:
    report = _require_mapping(report, "Pyright report")
    version = report.get("version")
    if not isinstance(version, str) or not version:
        raise ValueError("Pyright report version must be a non-empty string.")

    diagnostics = report.get("generalDiagnostics")
    if not isinstance(diagnostics, list):
        raise ValueError("Pyright generalDiagnostics must be a JSON array.")

    counts: Counter[tuple[str, str, str]] = Counter()
    severity_counts: Counter[str] = Counter()
    for index, diagnostic in enumerate(diagnostics):
        diagnostic = _require_mapping(diagnostic, f"generalDiagnostics[{index}]")
        severity = diagnostic.get("severity")
        if severity not in SEVERITIES:
            raise ValueError(
                f"generalDiagnostics[{index}].severity is unsupported: {severity!r}"
            )
        rule = diagnostic.get("rule") or "<none>"
        if not isinstance(rule, str):
            raise ValueError(f"generalDiagnostics[{index}].rule must be a string.")
        path = _relative_diagnostic_path(diagnostic.get("file"), repo_root)
        counts[(path, rule, severity)] += 1
        severity_counts[severity] += 1

    report_summary = _require_mapping(report.get("summary"), "Pyright summary")
    files_analyzed = _require_non_negative_int(
        report_summary.get("filesAnalyzed"),
        "Pyright summary.filesAnalyzed",
    )
    totals = {
        severity: _require_non_negative_int(
            report_summary.get(f"{severity}Count"),
            f"Pyright summary.{severity}Count",
        )
        for severity in SEVERITIES
    }
    observed_totals = {severity: severity_counts[severity] for severity in SEVERITIES}
    if totals != observed_totals:
        raise ValueError(
            "Pyright summary totals do not match generalDiagnostics: "
            f"summary={totals}, diagnostics={observed_totals}"
        )

    return {
        "version": version,
        "files_analyzed": files_analyzed,
        "totals": totals,
        "diagnostics": [
            {
                "path": path,
                "rule": rule,
                "severity": severity,
                "count": count,
            }
            for (path, rule, severity), count in sorted(counts.items())
        ],
    }


def _baseline_counts(
    baseline: dict,
    repo_root: Path = ROOT,
) -> tuple[dict, Counter[tuple[str, str, str]]]:
    baseline = _require_mapping(baseline, "Pyright baseline")
    expected_fields = {
        "schema",
        "version",
        "tool",
        "config",
        "strict_groups",
        "totals",
        "diagnostics",
    }
    if set(baseline) != expected_fields:
        raise ValueError(
            "Pyright baseline fields changed: "
            f"expected {sorted(expected_fields)}, got {sorted(baseline)}"
        )
    if baseline.get("schema") != BASELINE_SCHEMA:
        raise ValueError(f"Unsupported Pyright baseline schema: {baseline.get('schema')!r}")
    if baseline.get("version") != BASELINE_VERSION:
        raise ValueError(f"Unsupported Pyright baseline version: {baseline.get('version')!r}")

    tool = _require_mapping(baseline.get("tool"), "Pyright baseline tool")
    if tool.get("name") != "pyright":
        raise ValueError(f"Unsupported baseline tool: {tool.get('name')!r}")
    if not isinstance(tool.get("version"), str) or not tool["version"]:
        raise ValueError("Pyright baseline tool.version must be a non-empty string.")

    normalized_config = _normalize_baseline_config(baseline.get("config"))
    strict_groups = _normalize_strict_groups(
        baseline.get("strict_groups"),
        repo_root,
    )
    strict_paths = [
        path
        for group in strict_groups
        for path in group["paths"]
    ]
    if normalized_config["strict"] != strict_paths:
        raise ValueError(
            "Pyright baseline config.strict paths do not match owned strict_groups: "
            f"config={normalized_config['strict']}, groups={strict_paths}"
        )
    strict_path_set = set(strict_paths)

    totals = _require_mapping(baseline.get("totals"), "Pyright baseline totals")
    normalized_totals = {
        severity: _require_non_negative_int(
            totals.get(severity),
            f"Pyright baseline totals.{severity}",
        )
        for severity in SEVERITIES
    }

    entries = baseline.get("diagnostics")
    if not isinstance(entries, list):
        raise ValueError("Pyright baseline diagnostics must be a JSON array.")
    counts: Counter[tuple[str, str, str]] = Counter()
    for index, entry in enumerate(entries):
        entry = _require_mapping(entry, f"baseline diagnostics[{index}]")
        path = entry.get("path")
        rule = entry.get("rule")
        severity = entry.get("severity")
        baseline_path = Path(path) if isinstance(path, str) else None
        if (
            baseline_path is None
            or not path
            or baseline_path.is_absolute()
            or ".." in baseline_path.parts
            or baseline_path.as_posix() != path
        ):
            raise ValueError(
                f"baseline diagnostics[{index}].path must be canonical repository-relative POSIX."
            )
        if not isinstance(rule, str) or not rule:
            raise ValueError(f"baseline diagnostics[{index}].rule must be non-empty.")
        if severity not in SEVERITIES:
            raise ValueError(
                f"baseline diagnostics[{index}].severity is unsupported: {severity!r}"
            )
        count = _require_non_negative_int(
            entry.get("count"),
            f"baseline diagnostics[{index}].count",
        )
        if count == 0:
            raise ValueError(f"baseline diagnostics[{index}].count must be positive.")
        if path in strict_path_set:
            raise ValueError(
                f"Strict allowlist path cannot have baseline diagnostics: {path}"
            )
        key = (path, rule, severity)
        if key in counts:
            raise ValueError(f"Duplicate Pyright baseline diagnostic group: {key}")
        counts[key] = count

    counted_totals = {
        severity: sum(
            count for (*_, entry_severity), count in counts.items()
            if entry_severity == severity
        )
        for severity in SEVERITIES
    }
    if normalized_totals != counted_totals:
        raise ValueError(
            "Pyright baseline totals do not match diagnostic groups: "
            f"totals={normalized_totals}, diagnostics={counted_totals}"
        )
    return {
        "tool": tool,
        "config": normalized_config,
        "strict_groups": strict_groups,
        "totals": normalized_totals,
    }, counts


def compare_report(
    report: dict,
    baseline: dict,
    pyright_config: dict,
    repo_root: Path = ROOT,
) -> tuple[dict, list[str]]:
    summary = summarize_report(report, repo_root)
    metadata, expected_counts = _baseline_counts(baseline, repo_root)
    failures = _compare_config(pyright_config, metadata["config"])

    if summary["version"] != metadata["tool"]["version"]:
        failures.append(
            "Pyright version changed: "
            f"expected {metadata['tool']['version']}, got {summary['version']}"
        )

    current_counts = {
        (entry["path"], entry["rule"], entry["severity"]): entry["count"]
        for entry in summary["diagnostics"]
    }
    strict_paths = {
        path
        for group in metadata["strict_groups"]
        for path in group["paths"]
    }
    for key, current_count in sorted(current_counts.items()):
        path, rule, severity = key
        if path in strict_paths:
            failures.append(
                f"{path} is strict-owned but reported {current_count} "
                f"{severity} diagnostics for {rule}"
            )
            continue
        allowed_count = expected_counts.get(key, 0)
        if current_count > allowed_count:
            failures.append(
                f"{path} {rule} {severity}: allowed {allowed_count}, got {current_count}"
            )

    for severity in SEVERITIES:
        current_total = summary["totals"][severity]
        allowed_total = metadata["totals"][severity]
        if current_total > allowed_total:
            failures.append(
                f"total {severity} diagnostics: allowed {allowed_total}, got {current_total}"
            )

    return summary, failures


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare a Pyright JSON report with the reviewed diagnostic baseline."
    )
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        report = json.load(sys.stdin)
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        pyright_config = json.loads(args.config.read_text(encoding="utf-8"))
        summary, failures = compare_report(
            report,
            baseline,
            pyright_config,
            args.repo_root,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Pyright baseline input error: {exc}", file=sys.stderr)
        return 2

    if failures:
        print("Pyright baseline ratchet failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    totals = summary["totals"]
    print(
        "Pyright baseline ratchet passed: "
        f"{summary['files_analyzed']} files, "
        f"{totals['error']} errors, {totals['warning']} warnings, "
        f"{totals['information']} information diagnostics."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
