#!/usr/bin/env python3
"""Measure autocomplete cold/warm latency and Python heap usage.

Examples:
  python tools/benchmark_autocomplete.py
  python tools/benchmark_autocomplete.py --fixture-entries 1000 --warm-runs 3
  python tools/benchmark_autocomplete.py --fixture-entries 1000 --disable-index
  python tools/benchmark_autocomplete.py --verify-manifest
"""

from __future__ import annotations

import argparse
import ctypes
import gc
import json
import os
import platform
import statistics
import sys
import tempfile
import time
import tracemalloc
from contextlib import contextmanager
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from easyuse_anima.autocomplete import dataset
from easyuse_anima.autocomplete import search as autocomplete_search


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


@contextmanager
def _using_index_root(root: Path | None):
    previous = autocomplete_search._AUTOCOMPLETE_INDEX_DIR
    autocomplete_search._AUTOCOMPLETE_INDEX_DIR = root
    try:
        yield
    finally:
        autocomplete_search._AUTOCOMPLETE_INDEX_DIR = previous


def _process_rss_bytes() -> tuple[str, int | None]:
    if os.name == "nt":
        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong),
                ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        process = kernel32.GetCurrentProcess()
        get_process_memory_info = getattr(
            kernel32,
            "K32GetProcessMemoryInfo",
            ctypes.WinDLL("psapi", use_last_error=True).GetProcessMemoryInfo,
        )
        get_process_memory_info.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ProcessMemoryCounters),
            ctypes.c_ulong,
        ]
        get_process_memory_info.restype = ctypes.c_int
        if get_process_memory_info(
            process,
            ctypes.byref(counters),
            counters.cb,
        ):
            return "windows_working_set", int(counters.WorkingSetSize)
        return "unavailable", None

    try:
        import resource
    except ImportError:
        return "unavailable", None
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    scale = 1 if sys.platform == "darwin" else 1024
    return "process_peak_rss", int(usage * scale)


def _benchmark(
    path: Path,
    query: str,
    warm_runs: int,
    *,
    index_root: Path | None,
) -> dict:
    resolved_path = path.resolve(strict=False)
    _clear_cached_source(resolved_path)
    gc.collect()

    rss_metric, baseline_rss = _process_rss_bytes()
    with _using_index_root(index_root):
        tracemalloc.start()
        try:
            baseline_heap, _ = tracemalloc.get_traced_memory()
            cold_started = time.perf_counter()
            cold_result, cold_index = autocomplete_search._search_autocomplete_with_diagnostics(
                query,
                path=resolved_path,
            )
            cold_ms = (time.perf_counter() - cold_started) * 1000
            cold_heap_current, cold_heap_peak = tracemalloc.get_traced_memory()
            _, cold_rss = _process_rss_bytes()

            warm_times = []
            warm_result = None
            warm_indexes = []
            for _ in range(warm_runs):
                warm_started = time.perf_counter()
                warm_result, warm_index = autocomplete_search._search_autocomplete_with_diagnostics(
                    query,
                    path=resolved_path,
                )
                warm_times.append((time.perf_counter() - warm_started) * 1000)
                warm_indexes.append(warm_index)

            heap_current, heap_peak = tracemalloc.get_traced_memory()
            _, warm_rss = _process_rss_bytes()
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
        "rss_metric": rss_metric,
        "baseline_rss_bytes": baseline_rss,
        "cold_rss_bytes": cold_rss,
        "cold_rss_delta_bytes": (
            None
            if baseline_rss is None or cold_rss is None
            else cold_rss - baseline_rss
        ),
        "warm_rss_bytes": warm_rss,
        "warm_rss_delta_bytes": (
            None
            if baseline_rss is None or warm_rss is None
            else warm_rss - baseline_rss
        ),
        "index_cold_outcome": cold_index.outcome,
        "index_cold_reason": cold_index.reason,
        "index_warm_outcomes": [item.outcome for item in warm_indexes],
        "index_warm_reasons": [item.reason for item in warm_indexes],
        "index_backend": cold_index.backend,
        "index_source_revision": cold_index.source_revision,
        "index_file_size_bytes": (
            cold_index.index_path.stat().st_size
            if cold_index.index_path is not None and cold_index.index_path.is_file()
            else None
        ),
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
        "--disable-index",
        action="store_true",
        help="measure the exact Python snapshot fallback instead of the SQLite index",
    )
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
        or args.disable_index
    ):
        parser.error("--verify-manifest cannot be combined with a source option")
    if not str(args.query).strip():
        parser.error("--query must not be empty")
    return args


def main() -> int:
    args = _parse_args()
    if args.verify_manifest:
        return _verify_manifest()

    with tempfile.TemporaryDirectory(prefix="easyuse-anima-autocomplete-") as tmp:
        temporary_root = Path(tmp)
        index_root = None if args.disable_index else temporary_root / "index"
        if args.fixture_entries is not None:
            path = temporary_root / "fixture.csv"
            _write_fixture(path, args.fixture_entries)
            result = _benchmark(
                path,
                args.query,
                args.warm_runs,
                index_root=index_root,
            )
            result["fixture_entries"] = args.fixture_entries
        elif args.source is not None:
            result = _benchmark(
                args.source,
                args.query,
                args.warm_runs,
                index_root=index_root,
            )
        else:
            _, path = dataset.resolve_autocomplete_source(args.source_key)
            result = _benchmark(
                path,
                args.query,
                args.warm_runs,
                index_root=index_root,
            )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
