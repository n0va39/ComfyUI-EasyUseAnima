#!/usr/bin/env python3
"""Measure the current AiO first-pass cache clone and isolation contract."""

from __future__ import annotations

import argparse
import importlib
import json
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
SCHEMA_VERSION = 1
TENSORS_PER_ENTRY = 2
DEFAULT_PAYLOAD_BYTES = 64 * 1024
DEFAULT_ITERATIONS = 25
MAX_PAYLOAD_BYTES = 4 * 1024 * 1024
MAX_ITERATIONS = 100
MAX_LOGICAL_BYTES_PER_OPERATION = 64 * 1024 * 1024


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

    def __init__(self, payload: bytearray, counters: CloneCounters):
        self.payload = payload
        self.counters = counters

    @classmethod
    def filled(
        cls,
        payload_bytes: int,
        fill: int,
        counters: CloneCounters,
    ) -> BenchmarkTensor:
        return cls(bytearray([fill]) * payload_bytes, counters)

    def detach(self) -> BenchmarkTensor:
        self.counters.detach_calls += 1
        return self

    def clone(self) -> BenchmarkTensor:
        self.counters.clone_calls += 1
        self.counters.logical_bytes_copied += len(self.payload)
        return BenchmarkTensor(bytearray(self.payload), self.counters)

    def cpu(self) -> BenchmarkTensor:
        self.counters.cpu_calls += 1
        return self

    @property
    def nbytes(self) -> int:
        return len(self.payload)

    def mutate_first_byte(self) -> None:
        self.payload[0] ^= 0xFF

    def snapshot(self) -> bytes:
        return bytes(self.payload)


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
    latent = {
        "samples": BenchmarkTensor.filled(
            payload_bytes,
            0x11,
            counters,
        )
    }
    image = BenchmarkTensor.filled(payload_bytes, 0x22, counters)
    return latent, image


def _measure(
    operation: Callable[[], object],
    counters: CloneCounters,
    iterations: int,
) -> dict[str, int]:
    counters.reset()
    tracemalloc.start()
    started_ns = time.perf_counter_ns()
    try:
        for _ in range(iterations):
            operation()
        elapsed_ns = time.perf_counter_ns() - started_ns
        _, peak_traced_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    result = asdict(counters)
    result.update(
        {
            "operation_count": iterations,
            "elapsed_ns": elapsed_ns,
            "average_ns": elapsed_ns // iterations,
            "peak_traced_bytes": peak_traced_bytes,
        }
    )
    return result


def _measure_put(
    payload_bytes: int,
    iterations: int,
) -> dict[str, int]:
    counters = CloneCounters()
    latent, image = _entry(payload_bytes, counters)
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
) -> dict[str, int]:
    counters = CloneCounters()
    latent, image = _entry(payload_bytes, counters)
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
    counters = CloneCounters()
    latent, image = _entry(payload_bytes, counters)
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


def run_benchmark(
    *,
    payload_bytes: int = DEFAULT_PAYLOAD_BYTES,
    iterations: int = DEFAULT_ITERATIONS,
) -> dict[str, object]:
    _validate_workload(payload_bytes, iterations)
    first_pass_cache._clear_aio_first_pass_cache()
    try:
        put_overwrite = _measure_put(payload_bytes, iterations)
        first_pass_cache._clear_aio_first_pass_cache()
        get_hit = _measure_get_hit(payload_bytes, iterations)
        first_pass_cache._clear_aio_first_pass_cache()
        isolation = _measure_mutation_isolation(payload_bytes)
    finally:
        first_pass_cache._clear_aio_first_pass_cache()

    return {
        "schema": SCHEMA,
        "version": SCHEMA_VERSION,
        "config": {
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
        "--payload-bytes",
        type=int,
        default=DEFAULT_PAYLOAD_BYTES,
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        report = run_benchmark(
            payload_bytes=args.payload_bytes,
            iterations=args.iterations,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
