from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

from easyuse_anima.aio import first_pass_cache

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_PATH = ROOT / "tools" / "benchmark_aio_first_pass_cache.py"


def _load_benchmark_module():
    spec = importlib.util.spec_from_file_location(
        "easyuse_anima_aio_first_pass_cache_benchmark",
        BENCHMARK_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load benchmark: {BENCHMARK_PATH.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


benchmark = _load_benchmark_module()


class AIOFirstPassCacheBenchmarkTests(unittest.TestCase):
    def setUp(self):
        first_pass_cache._set_aio_first_pass_cache_enabled(True)
        first_pass_cache._clear_aio_first_pass_cache()
        first_pass_cache._reset_aio_first_pass_cache_metrics()

    def tearDown(self):
        first_pass_cache._set_aio_first_pass_cache_enabled(True)
        first_pass_cache._clear_aio_first_pass_cache()
        first_pass_cache._reset_aio_first_pass_cache_metrics()

    def test_fake_tensor_exposes_deterministic_payload_bytes(self):
        tensor = benchmark.BenchmarkTensor.filled(
            32,
            0x11,
            benchmark.CloneCounters(),
        )

        self.assertEqual(tensor.nbytes, 32)

    def test_report_freezes_clone_cost_and_bidirectional_isolation(self):
        report = benchmark.run_benchmark(
            payload_bytes=32,
            iterations=3,
        )

        self.assertEqual(
            (report["schema"], report["version"]),
            (
                "easyuse_anima_aio_first_pass_cache_benchmark",
                1,
            ),
        )
        self.assertEqual(
            report["config"],
            {
                "payload_bytes": 32,
                "iterations": 3,
                "tensors_per_entry": 2,
                "max_logical_bytes_per_operation": 64 * 1024 * 1024,
            },
        )
        for operation_name in ("put_overwrite", "get_hit"):
            with self.subTest(operation=operation_name):
                operation = report["operations"][operation_name]
                self.assertEqual(operation["operation_count"], 3)
                self.assertEqual(operation["detach_calls"], 6)
                self.assertEqual(operation["clone_calls"], 6)
                self.assertEqual(operation["cpu_calls"], 6)
                self.assertEqual(operation["logical_bytes_copied"], 192)
                self.assertGreaterEqual(operation["elapsed_ns"], 0)
                self.assertGreaterEqual(operation["average_ns"], 0)
                self.assertGreaterEqual(operation["peak_traced_bytes"], 0)

        self.assertEqual(
            report["isolation"],
            {
                "source_after_put": True,
                "returned_hit": True,
            },
        )
        self.assertEqual(first_pass_cache._AIO_FIRST_PASS_CACHE, {})
        self.assertEqual(first_pass_cache._AIO_FIRST_PASS_CACHE_ORDER, [])

    def test_workload_guard_bounds_each_axis_and_total_copy_volume(self):
        invalid_workloads = (
            (0, 1),
            (benchmark.MAX_PAYLOAD_BYTES + 1, 1),
            (1, 0),
            (1, benchmark.MAX_ITERATIONS + 1),
            (benchmark.MAX_PAYLOAD_BYTES, benchmark.MAX_ITERATIONS),
        )

        for payload_bytes, iterations in invalid_workloads:
            with (
                self.subTest(
                    payload_bytes=payload_bytes,
                    iterations=iterations,
                ),
                self.assertRaises(ValueError),
            ):
                benchmark.run_benchmark(
                    payload_bytes=payload_bytes,
                    iterations=iterations,
                )

    def test_cli_emits_valid_json_with_deterministic_contract_fields(self):
        result = subprocess.run(
            [
                sys.executable,
                str(BENCHMARK_PATH),
                "--payload-bytes",
                "16",
                "--iterations",
                "2",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )

        report = json.loads(result.stdout)
        self.assertEqual(report["config"]["payload_bytes"], 16)
        self.assertEqual(report["config"]["iterations"], 2)
        self.assertEqual(
            report["operations"]["put_overwrite"]["clone_calls"],
            4,
        )
        self.assertEqual(
            report["operations"]["get_hit"]["logical_bytes_copied"],
            64,
        )
        self.assertTrue(all(report["isolation"].values()))


if __name__ == "__main__":
    unittest.main()
