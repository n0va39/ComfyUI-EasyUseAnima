#!/usr/bin/env python3
"""Synchronize Comfy Registry node and version metadata from a checked-in file."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


API_BASE = "https://api.comfy.org"


def _json_request(
    method: str,
    path: str,
    *,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
) -> Any:
    url = path if path.startswith("https://") else f"{API_BASE}{path}"
    body = None
    headers = {
        "Accept": "application/json",
        "User-Agent": "ComfyUI-EasyUseAnima registry metadata sync",
    }
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"{method} {url} failed with HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{method} {url} failed: {exc}") from exc

    return json.loads(text) if text else None


def _load_metadata(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    for key in ("publisher_id", "node_id", "node", "versions"):
        if key not in data:
            raise ValueError(f"Missing required metadata key: {key}")
    if not isinstance(data["versions"], list):
        raise ValueError("metadata.versions must be a list")
    for item in data["versions"]:
        if not isinstance(item, dict):
            continue
        changelog_file = item.get("changelog_file")
        if not isinstance(changelog_file, str) or not changelog_file.strip():
            continue
        file_path = Path(changelog_file)
        if not file_path.is_absolute():
            file_path = path.parent / file_path
        item["changelog"] = file_path.read_text(encoding="utf-8").strip()
    return data


def _bool_arg(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {value}")


def _compact(value: Any, *, max_len: int = 90) -> str:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return rendered if len(rendered) <= max_len else f"{rendered[: max_len - 3]}..."


def _fetch_node(node_id: str) -> dict[str, Any]:
    query = urllib.parse.urlencode({"node_id": node_id, "latest": "true"})
    data = _json_request("GET", f"/nodes?{query}")
    nodes = data.get("nodes", []) if isinstance(data, dict) else []
    if len(nodes) != 1:
        raise RuntimeError(f"Expected one Registry node for {node_id}, found {len(nodes)}")
    return nodes[0]


def _fetch_versions(node_id: str) -> dict[str, dict[str, Any]]:
    safe_node_id = urllib.parse.quote(node_id, safe="")
    rows = _json_request("GET", f"/nodes/{safe_node_id}/versions?include_status_reason=true")
    if not isinstance(rows, list):
        raise RuntimeError("Registry versions response was not a list")
    return {str(row["version"]): row for row in rows}


def _diff_fields(current: dict[str, Any], desired: dict[str, Any]) -> dict[str, tuple[Any, Any]]:
    diff: dict[str, tuple[Any, Any]] = {}
    for key, desired_value in desired.items():
        current_value = current.get(key)
        if current_value != desired_value:
            diff[key] = (current_value, desired_value)
    return diff


def sync(metadata: dict[str, Any], *, token: str | None, dry_run: bool) -> int:
    publisher_id = str(metadata["publisher_id"])
    node_id = str(metadata["node_id"])
    safe_publisher_id = urllib.parse.quote(publisher_id, safe="")
    safe_node_id = urllib.parse.quote(node_id, safe="")

    current_node = _fetch_node(node_id)
    current_versions = _fetch_versions(node_id)

    if not dry_run and not token:
        raise RuntimeError("REGISTRY_ACCESS_TOKEN is required when dry_run is false")

    node_diff = _diff_fields(current_node, metadata["node"])
    if node_diff:
        print(f"Node metadata changes for {node_id}:")
        for key, (before, after) in node_diff.items():
            print(f"  - {key}: {_compact(before)} -> {_compact(after)}")
        if not dry_run:
            _json_request(
                "PUT",
                f"/publishers/{safe_publisher_id}/nodes/{safe_node_id}",
                token=token,
                payload=metadata["node"],
            )
            print("  applied node metadata")
    else:
        print(f"Node metadata already matches {node_id}")

    missing_versions: list[str] = []
    flagged_versions: list[str] = []
    for desired in metadata["versions"]:
        version = str(desired["version"])
        current = current_versions.get(version)
        if current is None:
            missing_versions.append(version)
            print(f"Version {version}: not found in Registry; skipped")
            continue

        if current.get("status") != "NodeVersionStatusActive":
            flagged_versions.append(f"{version} ({current.get('status')})")

        version_payload = {
            "changelog": desired.get("changelog", ""),
            "deprecated": bool(desired.get("deprecated", False)),
        }
        version_diff = _diff_fields(current, version_payload)
        if version_diff:
            print(f"Version {version} metadata changes:")
            for key, (before, after) in version_diff.items():
                print(f"  - {key}: {_compact(before)} -> {_compact(after)}")
            if not dry_run:
                version_id = urllib.parse.quote(str(current["id"]), safe="")
                _json_request(
                    "PUT",
                    f"/publishers/{safe_publisher_id}/nodes/{safe_node_id}/versions/{version_id}",
                    token=token,
                    payload=version_payload,
                )
                print(f"  applied version {version} metadata")
        else:
            print(f"Version {version}: metadata already matches")

    if flagged_versions:
        print("Registry status note: these versions are not active and still need Registry/admin approval:")
        for item in flagged_versions:
            print(f"  - {item}")
    if missing_versions:
        print("Missing versions were skipped:")
        for version in missing_versions:
            print(f"  - {version}")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--metadata",
        type=Path,
        default=Path(".github/registry/metadata.json"),
        help="Path to Registry metadata JSON.",
    )
    parser.add_argument(
        "--dry-run",
        type=_bool_arg,
        default=True,
        help="Print planned changes without writing to the Registry.",
    )
    args = parser.parse_args(argv)

    metadata = _load_metadata(args.metadata)
    token = os.environ.get("REGISTRY_ACCESS_TOKEN") or os.environ.get("COMFY_REGISTRY_TOKEN")
    return sync(metadata, token=token, dry_run=args.dry_run)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
