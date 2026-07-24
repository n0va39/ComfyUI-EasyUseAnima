#!/usr/bin/env python3
"""Measure the current AiO first-pass cache clone and isolation contract."""

from __future__ import annotations

import argparse
import ctypes
import importlib
import json
import os
import sys
import time
import tracemalloc
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
first_pass_cache = importlib.import_module(
    "easyuse_anima.aio.first_pass_cache"
)

SCHEMA = "easyuse_anima_aio_first_pass_cache_benchmark"
SCHEMA_VERSION = 2
PROFILE_BOUNDED = "bounded"
PROFILE_4K_BATCH1 = "4k-batch1"
TENSORS_PER_ENTRY = 2
DEFAULT_PAYLOAD_BYTES = 64 * 1024
DEFAULT_ITERATIONS = 25
MAX_PAYLOAD_BYTES = 4 * 1024 * 1024
MAX_ITERATIONS = 100
MAX_LOGICAL_BYTES_PER_OPERATION = 64 * 1024 * 1024
FOUR_K_WIDTH = 4096
FOUR_K_HEIGHT = 4096
FOUR_K_BATCH = 1
FOUR_K_IMAGE_CHANNELS = 3
FOUR_K_IMAGE_ELEMENT_BYTES = 4
FOUR_K_LATENT_CHANNELS = 4
FOUR_K_LATENT_ELEMENT_BYTES = 4
FOUR_K_LATENT_DOWNSCALE = 8
FOUR_K_DEFAULT_ITERATIONS = 3
FOUR_K_MAX_ITERATIONS = 3
FOUR_K_MAX_MATERIALIZED_ENTRY_BYTES = 224 * 1024 * 1024
FOUR_K_MAX_LOGICAL_BYTES_PER_OPERATION = 768 * 1024 * 1024


@dataclass
class CloneCounters:
    detach_calls: int = 0
    clone_calls: int = 0
    cpu_calls: int = 0
    logical_bytes_copied: int = 0

    def reset(self) -> None:
        self.detach_calls = 0
        self.clone_calls = 0
        self.cpu_calls = 0
        self.logical_bytes_copied = 0


class BenchmarkTensor:
    """Small mutable tensor stand-in for exercising the canonical clone path."""

    def __init__(
        self,
        payload: bytearray,
        counters: CloneCounters,
        *,
        logical_nbytes: int | None = None,
    ):
        self.payload = payload
        self.counters = counters
        self.logical_nbytes = (
            len(payload)
            if logical_nbytes is None
            else int(logical_nbytes)
        )
        if self.logical_nbytes < len(payload):
            raise ValueError(
                "logical_nbytes must be at least the physical payload size"
            )

    @classmethod
    def filled(
        cls,
        payload_bytes: int,
        fill: int,
        counters: CloneCounters,
        *,
        logical_nbytes: int | None = None,
    ) -> BenchmarkTensor:
        return cls(
            bytearray([fill]) * payload_bytes,
            counters,
            logical_nbytes=logical_nbytes,
        )

    def detach(self) -> BenchmarkTensor:
        self.counters.detach_calls += 1
        return self

    def clone(self) -> BenchmarkTensor:
        self.counters.clone_calls += 1
        self.counters.logical_bytes_copied += self.logical_nbytes
        return BenchmarkTensor(
            bytearray(self.payload),
            self.counters,
            logical_nbytes=self.logical_nbytes,
        )

    def cpu(self) -> BenchmarkTensor:
        self.counters.cpu_calls += 1
        return self

    @property
    def nbytes(self) -> int:
        return self.logical_nbytes

    def mutate_first_byte(self) -> None:
        self.payload[0] ^= 0xFF

    def snapshot(self) -> bytes:
        return bytes(self.payload)


def _windows_process_memory_snapshot() -> dict[str, int | None]:
    try:
        from ctypes import wintypes

        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
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
        get_current_process = ctypes.windll.kernel32.GetCurrentProcess
        get_process_memory_info = (
            ctypes.windll.psapi.GetProcessMemoryInfo
        )
        get_current_process.argtypes = []
        get_current_process.restype = wintypes.HANDLE
        get_process_memory_info.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(ProcessMemoryCounters),
            wintypes.DWORD,
        ]
        get_process_memory_info.restype = wintypes.BOOL
        process = get_current_process()
        if not get_process_memory_info(
            process,
            ctypes.byref(counters),
            counters.cb,
        ):
            raise OSError("GetProcessMemoryInfo failed")
        return {
            "rss_bytes": int(counters.WorkingSetSize),
            "peak_rss_bytes": int(counters.PeakWorkingSetSize),
        }
    except Exception:
        return {
            "rss_bytes": None,
            "peak_rss_bytes": None,
        }


def _posix_process_memory_snapshot() -> dict[str, int | None]:
    rss_bytes = None
    peak_rss_bytes = None
    try:
        statm = Path("/proc/self/statm").read_text(
            encoding="ascii"
        ).split()
        if len(statm) >= 2:
            rss_bytes = int(statm[1]) * int(os.sysconf("SC_PAGE_SIZE"))
    except (OSError, ValueError):
        pass
    try:
        import resource

        peak = int(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        )
        peak_rss_bytes = (
            peak
            if sys.platform == "darwin"
            else peak * 1024
        )
    except (ImportError, OSError, ValueError):
        pass
    return {
        "rss_bytes": rss_bytes,
        "peak_rss_bytes": peak_rss_bytes,
    }


def _process_memory_snapshot() -> dict[str, int | None]:
    if sys.platform == "win32":
        return _windows_process_memory_snapshot()
    return _posix_process_memory_snapshot()


def _validate_workload(payload_bytes: int, iterations: int) -> None:
    if not 1 <= payload_bytes <= MAX_PAYLOAD_BYTES:
        raise ValueError(
            f"payload_bytes must be between 1 and {MAX_PAYLOAD_BYTES}"
        )
    if not 1 <= iterations <= MAX_ITERATIONS:
        raise ValueError(
            f"iterations must be between 1 and {MAX_ITERATIONS}"
        )
    logical_bytes = payload_bytes * iterations * TENSORS_PER_ENTRY
    if logical_bytes > MAX_LOGICAL_BYTES_PER_OPERATION:
        raise ValueError(
            "payload_bytes * iterations * tensors_per_entry must not exceed "
            f"{MAX_LOGICAL_BYTES_PER_OPERATION}"
        )


def _entry(
    payload_bytes: int,
    counters: CloneCounters,
) -> tuple[dict[str, Any], BenchmarkTensor]:
    return _entry_pair(
        payload_bytes,
        payload_bytes,
        counters,
    )


def _entry_pair(
    latent_bytes: int,
    image_bytes: int,
    counters: CloneCounters,
) -> tuple[dict[str, Any], BenchmarkTensor]:
    latent = {
        "samples": BenchmarkTensor.filled(
            latent_bytes,
            0x11,
            counters,
        )
    }
    image = BenchmarkTensor.filled(
        image_bytes,
        0x22,
        counters,
    )
    return latent, image


def _measure(
    operation: Callable[[], object],
    counters: CloneCounters,
    iterations: int,
) -> dict[str, int | None]:
    counters.reset()
    memory_before = _process_memory_snapshot()
    tracemalloc.start()
    started_ns = time.perf_counter_ns()
    try:
        for _ in range(iterations):
            operation()
        elapsed_ns = time.perf_counter_ns() - started_ns
        _, peak_traced_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    memory_after = _process_memory_snapshot()
    peak_before = memory_before["peak_rss_bytes"]
    peak_after = memory_after["peak_rss_bytes"]
    peak_growth = (
        None
        if peak_before is None or peak_after is None
        else max(0, peak_after - peak_before)
    )

    result = asdict(counters)
    result.update(
        {
            "operation_count": iterations,
            "elapsed_ns": elapsed_ns,
            "average_ns": elapsed_ns // iterations,
            "peak_traced_bytes": peak_traced_bytes,
            "rss_before_bytes": memory_before["rss_bytes"],
            "rss_after_bytes": memory_after["rss_bytes"],
            "peak_rss_before_bytes": peak_before,
            "peak_rss_after_bytes": peak_after,
            "peak_rss_growth_bytes": peak_growth,
        }
    )
    return result


def _measure_put(
    payload_bytes: int,
    iterations: int,
) -> dict[str, int | None]:
    return _measure_put_pair(
        payload_bytes,
        payload_bytes,
        iterations,
    )


def _measure_put_pair(
    latent_bytes: int,
    image_bytes: int,
    iterations: int,
) -> dict[str, int | None]:
    counters = CloneCounters()
    latent, image = _entry_pair(
        latent_bytes,
        image_bytes,
        counters,
    )
    return _measure(
        lambda: first_pass_cache._put_aio_first_pass_cache(
            "benchmark",
            latent,
            image,
        ),
        counters,
        iterations,
    )


def _measure_get_hit(
    payload_bytes: int,
    iterations: int,
) -> dict[str, int | None]:
    return _measure_get_hit_pair(
        payload_bytes,
        payload_bytes,
        iterations,
    )


def _measure_get_hit_pair(
    latent_bytes: int,
    image_bytes: int,
    iterations: int,
) -> dict[str, int | None]:
    counters = CloneCounters()
    latent, image = _entry_pair(
        latent_bytes,
        image_bytes,
        counters,
    )
    first_pass_cache._put_aio_first_pass_cache(
        "benchmark",
        latent,
        image,
    )
    return _measure(
        lambda: first_pass_cache._get_aio_first_pass_cache("benchmark"),
        counters,
        iterations,
    )


def _measure_mutation_isolation(payload_bytes: int) -> dict[str, bool]:
    return _measure_mutation_isolation_pair(
        payload_bytes,
        payload_bytes,
    )


def _measure_mutation_isolation_pair(
    latent_bytes: int,
    image_bytes: int,
) -> dict[str, bool]:
    counters = CloneCounters()
    latent, image = _entry_pair(
        latent_bytes,
        image_bytes,
        counters,
    )
    latent_tensor = latent["samples"]
    latent_before = latent_tensor.snapshot()
    image_before = image.snapshot()

    first_pass_cache._put_aio_first_pass_cache(
        "isolation",
        latent,
        image,
    )
    latent_tensor.mutate_first_byte()
    image.mutate_first_byte()

    first_latent, first_image = first_pass_cache._get_aio_first_pass_cache(
        "isolation"
    )
    source_after_put = (
        first_latent["samples"].snapshot() == latent_before
        and first_image.snapshot() == image_before
    )

    first_latent["samples"].mutate_first_byte()
    first_image.mutate_first_byte()
    del first_latent, first_image
    second_latent, second_image = first_pass_cache._get_aio_first_pass_cache(
        "isolation"
    )
    returned_hit = (
        second_latent["samples"].snapshot() == latent_before
        and second_image.snapshot() == image_before
    )
    return {
        "source_after_put": source_after_put,
        "returned_hit": returned_hit,
    }


def _image_workload_tensor_bytes(
    *,
    width: int,
    height: int,
    batch: int,
) -> tuple[int, int]:
    if width <= 0 or height <= 0 or batch <= 0:
        raise ValueError("width, height, and batch must be positive")
    if (
        width % FOUR_K_LATENT_DOWNSCALE
        or height % FOUR_K_LATENT_DOWNSCALE
    ):
        raise ValueError(
            "width and height must be divisible by latent downscale"
        )
    latent_bytes = (
        batch
        * (width // FOUR_K_LATENT_DOWNSCALE)
        * (height // FOUR_K_LATENT_DOWNSCALE)
        * FOUR_K_LATENT_CHANNELS
        * FOUR_K_LATENT_ELEMENT_BYTES
    )
    image_bytes = (
        batch
        * width
        * height
        * FOUR_K_IMAGE_CHANNELS
        * FOUR_K_IMAGE_ELEMENT_BYTES
    )
    return latent_bytes, image_bytes


def _measure_declared_batch_preflight(
    *,
    latent_bytes: int,
    image_bytes: int,
) -> dict[str, object]:
    counters = CloneCounters()
    latent = {
        "samples": BenchmarkTensor.filled(
            1,
            0x11,
            counters,
            logical_nbytes=latent_bytes,
        )
    }
    image = BenchmarkTensor.filled(
        1,
        0x22,
        counters,
        logical_nbytes=image_bytes,
    )
    first_pass_cache._clear_aio_first_pass_cache()
    first_pass_cache._reset_aio_first_pass_cache_metrics()
    try:
        first_pass_cache._put_aio_first_pass_cache(
            "batch-preflight",
            latent,
            image,
        )
        metrics = (
            first_pass_cache._aio_first_pass_cache_metrics_snapshot()
        )
        return {
            "latent_bytes": latent_bytes,
            "image_bytes": image_bytes,
            "entry_bytes": latent_bytes + image_bytes,
            "admitted": (
                "batch-preflight"
                in first_pass_cache._AIO_FIRST_PASS_CACHE
            ),
            "detach_calls": counters.detach_calls,
            "clone_calls": counters.clone_calls,
            "cpu_calls": counters.cpu_calls,
            "logical_bytes_copied": counters.logical_bytes_copied,
            "skip_count": metrics.skips,
        }
    finally:
        first_pass_cache._clear_aio_first_pass_cache()
        first_pass_cache._reset_aio_first_pass_cache_metrics()


def run_4k_benchmark(
    *,
    iterations: int = FOUR_K_DEFAULT_ITERATIONS,
) -> dict[str, object]:
    if not 1 <= iterations <= FOUR_K_MAX_ITERATIONS:
        raise ValueError(
            "4K iterations must be between 1 and "
            f"{FOUR_K_MAX_ITERATIONS}"
        )
    latent_bytes, image_bytes = _image_workload_tensor_bytes(
        width=FOUR_K_WIDTH,
        height=FOUR_K_HEIGHT,
        batch=FOUR_K_BATCH,
    )
    entry_bytes = latent_bytes + image_bytes
    batch2_latent_bytes, batch2_image_bytes = (
        _image_workload_tensor_bytes(
            width=FOUR_K_WIDTH,
            height=FOUR_K_HEIGHT,
            batch=FOUR_K_BATCH * 2,
        )
    )
    batch2_entry_bytes = batch2_latent_bytes + batch2_image_bytes
    single_entry_cap = (
        first_pass_cache.AIO_FIRST_PASS_CACHE_MAX_ENTRY_BYTES
    )
    if entry_bytes > single_entry_cap:
        raise ValueError(
            "4K batch-1 entry must fit the cache single-entry cap"
        )
    if batch2_entry_bytes <= single_entry_cap:
        raise ValueError(
            "4K batch-2 projection must exceed the single-entry cap"
        )
    if entry_bytes > FOUR_K_MAX_MATERIALIZED_ENTRY_BYTES:
        raise ValueError(
            "4K materialized entry exceeds the benchmark safety cap"
        )
    if (
        entry_bytes * iterations
        > FOUR_K_MAX_LOGICAL_BYTES_PER_OPERATION
    ):
        raise ValueError(
            "4K logical copy volume exceeds the benchmark safety cap"
        )

    first_pass_cache._clear_aio_first_pass_cache()
    first_pass_cache._reset_aio_first_pass_cache_metrics()
    try:
        put_overwrite = _measure_put_pair(
            latent_bytes,
            image_bytes,
            iterations,
        )
        first_pass_cache._clear_aio_first_pass_cache()
        get_hit = _measure_get_hit_pair(
            latent_bytes,
            image_bytes,
            iterations,
        )
        first_pass_cache._clear_aio_first_pass_cache()
        isolation = _measure_mutation_isolation_pair(
            latent_bytes,
            image_bytes,
        )
        batch2_preflight = _measure_declared_batch_preflight(
            latent_bytes=batch2_latent_bytes,
            image_bytes=batch2_image_bytes,
        )
    finally:
        first_pass_cache._clear_aio_first_pass_cache()
        first_pass_cache._reset_aio_first_pass_cache_metrics()

    return {
        "schema": SCHEMA,
        "version": SCHEMA_VERSION,
        "config": {
            "profile": PROFILE_4K_BATCH1,
            "width": FOUR_K_WIDTH,
            "height": FOUR_K_HEIGHT,
            "batch": FOUR_K_BATCH,
            "iterations": iterations,
            "latent_channels": FOUR_K_LATENT_CHANNELS,
            "latent_element_bytes": FOUR_K_LATENT_ELEMENT_BYTES,
            "latent_downscale": FOUR_K_LATENT_DOWNSCALE,
            "image_channels": FOUR_K_IMAGE_CHANNELS,
            "image_element_bytes": FOUR_K_IMAGE_ELEMENT_BYTES,
            "latent_bytes": latent_bytes,
            "image_bytes": image_bytes,
            "entry_bytes": entry_bytes,
            "single_entry_cap_bytes": single_entry_cap,
            "max_materialized_entry_bytes": (
                FOUR_K_MAX_MATERIALIZED_ENTRY_BYTES
            ),
            "max_logical_bytes_per_operation": (
                FOUR_K_MAX_LOGICAL_BYTES_PER_OPERATION
            ),
        },
        "operations": {
            "put_overwrite": put_overwrite,
            "get_hit": get_hit,
        },
        "batch2_preflight": batch2_preflight,
        "isolation": isolation,
    }


def run_benchmark(
    *,
    payload_bytes: int = DEFAULT_PAYLOAD_BYTES,
    iterations: int = DEFAULT_ITERATIONS,
) -> dict[str, object]:
    _validate_workload(payload_bytes, iterations)
    first_pass_cache._clear_aio_first_pass_cache()
    first_pass_cache._reset_aio_first_pass_cache_metrics()
    try:
        put_overwrite = _measure_put(payload_bytes, iterations)
        first_pass_cache._clear_aio_first_pass_cache()
        get_hit = _measure_get_hit(payload_bytes, iterations)
        first_pass_cache._clear_aio_first_pass_cache()
        isolation = _measure_mutation_isolation(payload_bytes)
    finally:
        first_pass_cache._clear_aio_first_pass_cache()
        first_pass_cache._reset_aio_first_pass_cache_metrics()

    return {
        "schema": SCHEMA,
        "version": SCHEMA_VERSION,
        "config": {
            "profile": PROFILE_BOUNDED,
            "payload_bytes": payload_bytes,
            "iterations": iterations,
            "tensors_per_entry": TENSORS_PER_ENTRY,
            "max_logical_bytes_per_operation": (
                MAX_LOGICAL_BYTES_PER_OPERATION
            ),
        },
        "operations": {
            "put_overwrite": put_overwrite,
            "get_hit": get_hit,
        },
        "isolation": isolation,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=(PROFILE_BOUNDED, PROFILE_4K_BATCH1),
        default=PROFILE_BOUNDED,
    )
    parser.add_argument(
        "--payload-bytes",
        type=int,
        default=DEFAULT_PAYLOAD_BYTES,
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=None,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.profile == PROFILE_4K_BATCH1:
            report = run_4k_benchmark(
                iterations=(
                    FOUR_K_DEFAULT_ITERATIONS
                    if args.iterations is None
                    else args.iterations
                ),
            )
        else:
            report = run_benchmark(
                payload_bytes=args.payload_bytes,
                iterations=(
                    DEFAULT_ITERATIONS
                    if args.iterations is None
                    else args.iterations
                ),
            )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
