from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_process_memory_snapshot_is_supported_on_windows(self):
        snapshot = benchmark._process_memory_snapshot()

        self.assertEqual(
            set(snapshot),
            {"rss_bytes", "peak_rss_bytes"},
        )
        for value in snapshot.values():
            if sys.platform == "win32":
                self.assertIsInstance(value, int)
            if value is not None:
                self.assertGreaterEqual(value, 0)

    def test_report_freezes_clone_cost_and_bidirectional_isolation(self):
        report = benchmark.run_benchmark(
            payload_bytes=32,
            iterations=3,
        )

        self.assertEqual(
            (report["schema"], report["version"]),
            (
                "easyuse_anima_aio_first_pass_cache_benchmark",
                2,
            ),
        )
        self.assertEqual(
            report["config"],
            {
                "profile": "bounded",
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
                for memory_name in (
                    "rss_before_bytes",
                    "rss_after_bytes",
                    "peak_rss_before_bytes",
                    "peak_rss_after_bytes",
                    "peak_rss_growth_bytes",
                ):
                    memory_value = operation[memory_name]
                    if memory_value is not None:
                        self.assertGreaterEqual(memory_value, 0)

        self.assertEqual(
            report["isolation"],
            {
                "source_after_put": True,
                "returned_hit": True,
            },
        )
        self.assertEqual(first_pass_cache._AIO_FIRST_PASS_CACHE, {})
        self.assertEqual(first_pass_cache._AIO_FIRST_PASS_CACHE_ORDER, [])

    def test_4k_workload_math_matches_batch1_and_batch2_cap_contract(self):
        latent_bytes, image_bytes = benchmark._image_workload_tensor_bytes(
            width=4096,
            height=4096,
            batch=1,
        )
        batch2_latent, batch2_image = (
            benchmark._image_workload_tensor_bytes(
                width=4096,
                height=4096,
                batch=2,
            )
        )

        self.assertEqual(latent_bytes, 4 * 1024 * 1024)
        self.assertEqual(image_bytes, 192 * 1024 * 1024)
        self.assertEqual(
            latent_bytes + image_bytes,
            196 * 1024 * 1024,
        )
        self.assertEqual(
            batch2_latent + batch2_image,
            392 * 1024 * 1024,
        )
        self.assertLessEqual(
            latent_bytes + image_bytes,
            first_pass_cache.AIO_FIRST_PASS_CACHE_MAX_ENTRY_BYTES,
        )
        self.assertGreater(
            batch2_latent + batch2_image,
            first_pass_cache.AIO_FIRST_PASS_CACHE_MAX_ENTRY_BYTES,
        )

    def test_4k_profile_uses_small_patched_buffers_and_clone_zero_batch2_guard(self):
        with (
            patch.object(benchmark, "FOUR_K_WIDTH", 16),
            patch.object(benchmark, "FOUR_K_HEIGHT", 16),
            patch.object(
                first_pass_cache,
                "AIO_FIRST_PASS_CACHE_MAX_ENTRY_BYTES",
                4000,
            ),
        ):
            report = benchmark.run_4k_benchmark(iterations=2)

        self.assertEqual(
            (report["schema"], report["version"]),
            (
                "easyuse_anima_aio_first_pass_cache_benchmark",
                2,
            ),
        )
        config = report["config"]
        self.assertEqual(config["profile"], "4k-batch1")
        self.assertEqual(
            (
                config["width"],
                config["height"],
                config["batch"],
                config["latent_bytes"],
                config["image_bytes"],
                config["entry_bytes"],
                config["single_entry_cap_bytes"],
            ),
            (16, 16, 1, 64, 3072, 3136, 4000),
        )
        for operation_name in ("put_overwrite", "get_hit"):
            operation = report["operations"][operation_name]
            self.assertEqual(operation["operation_count"], 2)
            self.assertEqual(operation["clone_calls"], 4)
            self.assertEqual(operation["logical_bytes_copied"], 6272)
        self.assertEqual(
            report["batch2_preflight"],
            {
                "latent_bytes": 128,
                "image_bytes": 6144,
                "entry_bytes": 6272,
                "admitted": False,
                "detach_calls": 0,
                "clone_calls": 0,
                "cpu_calls": 0,
                "logical_bytes_copied": 0,
                "skip_count": 1,
            },
        )
        self.assertEqual(
            report["isolation"],
            {
                "source_after_put": True,
                "returned_hit": True,
            },
        )
        self.assertEqual(first_pass_cache._AIO_FIRST_PASS_CACHE, {})
        self.assertEqual(first_pass_cache._AIO_FIRST_PASS_CACHE_ORDER, [])
        self.assertEqual(
            first_pass_cache._aio_first_pass_cache_metrics_snapshot(),
            first_pass_cache._AIOFirstPassCacheMetrics(0, 0, 0, 0),
        )

    def test_4k_profile_iteration_and_dimension_guards_are_bounded(self):
        for iterations in (0, benchmark.FOUR_K_MAX_ITERATIONS + 1):
            with self.subTest(iterations=iterations), self.assertRaises(
                ValueError
            ):
                benchmark.run_4k_benchmark(iterations=iterations)

        for values in (
            {"width": 0, "height": 16, "batch": 1},
            {"width": 15, "height": 16, "batch": 1},
            {"width": 16, "height": 16, "batch": 0},
        ):
            with self.subTest(values=values), self.assertRaises(ValueError):
                benchmark._image_workload_tensor_bytes(**values)

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
        self.assertEqual(report["version"], 2)
        self.assertEqual(report["config"]["profile"], "bounded")
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
