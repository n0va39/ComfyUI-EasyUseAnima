#!/usr/bin/env python3
"""Measure autocomplete cold/warm latency and Python heap usage.

Examples:
  python tools/benchmark_autocomplete.py
  python tools/benchmark_autocomplete.py --fixture-entries 1000 --warm-runs 3
  python tools/benchmark_autocomplete.py --verify-manifest
"""

from __future__ import annotations

import argparse
import gc
import json
import platform
import statistics
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

import autocomplete_dataset as dataset


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return parsed


def _write_fixture(path: Path, entry_count: int) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        for index in range(entry_count):
            tag = "1girl" if index == 0 else f"benchmark tag {index:06d}"
            count = entry_count - index
            handle.write(f'{tag},0,{count},"[general] benchmark fixture {index}"\n')


def _clear_cached_source(path: Path) -> None:
    key = dataset._cache_key(path)
    with dataset._CACHE_LOCK:
        if any(
            inflight_key.resolved_path == key.resolved_path
            for inflight_key in dataset._INFLIGHT
        ):
            raise RuntimeError(f"autocomplete load already in flight: {key.resolved_path}")
        dataset._CACHE.pop(key.resolved_path, None)


def _benchmark(path: Path, query: str, warm_runs: int) -> dict:
    resolved_path = path.resolve(strict=False)
    _clear_cached_source(resolved_path)
    gc.collect()

    tracemalloc.start()
    try:
        baseline_heap, _ = tracemalloc.get_traced_memory()
        cold_started = time.perf_counter()
        cold_result = dataset.search_autocomplete(query, path=resolved_path)
        cold_ms = (time.perf_counter() - cold_started) * 1000
        cold_heap_current, cold_heap_peak = tracemalloc.get_traced_memory()

        warm_times = []
        warm_result = None
        for _ in range(warm_runs):
            warm_started = time.perf_counter()
            warm_result = dataset.search_autocomplete(query, path=resolved_path)
            warm_times.append((time.perf_counter() - warm_started) * 1000)

        heap_current, heap_peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    if warm_result is None or warm_result["status"] != cold_result["status"]:
        raise RuntimeError("cold and warm searches did not use the same snapshot status")

    return {
        "source_path": str(resolved_path),
        "source_exists": cold_result["status"]["exists"],
        "entry_count": cold_result["status"]["count"],
        "query": query,
        "cold_ms": round(cold_ms, 3),
        "warm_ms_median": round(statistics.median(warm_times), 3),
        "warm_ms_min": round(min(warm_times), 3),
        "warm_runs": warm_runs,
        "memory_metric": "tracemalloc_python_heap",
        "cold_heap_retained_bytes": max(0, cold_heap_current - baseline_heap),
        "cold_heap_peak_bytes": max(0, cold_heap_peak - baseline_heap),
        "overall_heap_retained_bytes": max(0, heap_current - baseline_heap),
        "overall_heap_peak_bytes": max(0, heap_peak - baseline_heap),
        "python": sys.version.replace("\n", " "),
        "platform": platform.platform(),
    }


def _verify_manifest() -> int:
    checks = []
    has_drift = False
    for source_key, source in dataset.AUTOCOMPLETE_SOURCES.items():
        path = Path(source["path"]).resolve(strict=False)
        expected_count = source.get("entry_count")
        started = time.perf_counter()
        entries = dataset._load_entries(path)
        actual_count = len(entries)
        elapsed_ms = (time.perf_counter() - started) * 1000
        matches = (
            path.is_file()
            and type(expected_count) is int
            and expected_count == actual_count
        )
        has_drift = has_drift or not matches
        checks.append(
            {
                "source": source_key,
                "source_path": str(path),
                "source_exists": path.is_file(),
                "manifest_entry_count": expected_count,
                "parser_entry_count": actual_count,
                "file_size_bytes": path.stat().st_size if path.is_file() else None,
                "elapsed_ms": round(elapsed_ms, 3),
                "matches": matches,
            }
        )
        del entries
        gc.collect()

    print(
        json.dumps(
            {
                "manifest_drift": has_drift,
                "checks": checks,
                "python": sys.version.replace("\n", " "),
                "platform": platform.platform(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if has_drift else 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--source-key",
        choices=tuple(dataset.AUTOCOMPLETE_SOURCES),
        help="benchmark a configured built-in source",
    )
    source_group.add_argument("--source", type=Path, help="benchmark an arbitrary CSV path")
    source_group.add_argument(
        "--fixture-entries",
        type=_positive_int,
        help="generate and benchmark a temporary CSV with this many entries",
    )
    parser.add_argument("--query", default="1girl", help="autocomplete query")
    parser.add_argument("--warm-runs", type=_positive_int, default=5)
    parser.add_argument(
        "--verify-manifest",
        action="store_true",
        help="verify all built-in manifest counts and exit without benchmarking",
    )
    args = parser.parse_args()
    if args.verify_manifest and (
        args.source_key is not None
        or args.source is not None
        or args.fixture_entries is not None
    ):
        parser.error("--verify-manifest cannot be combined with a source option")
    if not str(args.query).strip():
        parser.error("--query must not be empty")
    return args


def main() -> int:
    args = _parse_args()
    if args.verify_manifest:
        return _verify_manifest()

    if args.fixture_entries is not None:
        with tempfile.TemporaryDirectory(prefix="easyuse-anima-autocomplete-") as tmp:
            path = Path(tmp) / "fixture.csv"
            _write_fixture(path, args.fixture_entries)
            result = _benchmark(path, args.query, args.warm_runs)
            result["fixture_entries"] = args.fixture_entries
    elif args.source is not None:
        result = _benchmark(args.source, args.query, args.warm_runs)
    else:
        _, path = dataset.resolve_autocomplete_source(args.source_key)
        result = _benchmark(path, args.query, args.warm_runs)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
