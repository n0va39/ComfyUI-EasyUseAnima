from __future__ import annotations

import copy
import unittest
from dataclasses import FrozenInstanceError
from unittest.mock import patch

import nodes
from easyuse_anima.aio.generation_migrations import (
    AIO_GENERATION_MIGRATION_REGISTRY,
    AIO_GENERATION_SETTINGS_CURRENT_VERSION,
    AIO_GENERATION_SETTINGS_SCHEMA,
    AIOGenerationMigrationError,
    AIOGenerationMigrationRegistry,
    AIOGenerationMigrationStep,
    detect_aio_generation_settings_version,
    migrate_aio_generation_settings,
)
from easyuse_anima.aio.generation_settings import (
    migrate_normalize_and_round_trip_aio_generation_settings,
)


def _payload(version: int = 1) -> dict[str, object]:
    return {
        "schema": AIO_GENERATION_SETTINGS_SCHEMA,
        "version": version,
        "extension": {"rows": [{"name": "original", "values": [1, 2]}]},
    }


class AIOGenerationMigrationTests(unittest.TestCase):
    def test_shipped_registry_is_empty_immutable_and_matches_root_contract(self):
        self.assertEqual(AIO_GENERATION_SETTINGS_SCHEMA, nodes.AIO_GENERATION_SETTINGS_SCHEMA)
        self.assertEqual(
            AIO_GENERATION_SETTINGS_CURRENT_VERSION,
            nodes.AIO_GENERATION_SETTINGS_VERSION,
        )
        self.assertEqual(AIO_GENERATION_MIGRATION_REGISTRY.steps, ())
        with self.assertRaises(FrozenInstanceError):
            AIO_GENERATION_MIGRATION_REGISTRY.steps = ()

    def test_current_version_is_a_deep_cloned_identity(self):
        source = _payload()
        source_before = copy.deepcopy(source)

        migrated = migrate_aio_generation_settings(source)

        self.assertEqual(migrated, source_before)
        self.assertIsNot(migrated, source)
        self.assertIsNot(migrated["extension"], source["extension"])
        migrated["extension"]["rows"][0]["name"] = "changed"
        self.assertEqual(source, source_before)

    def test_detection_and_dispatch_errors_are_explicit(self):
        self.assertEqual(detect_aio_generation_settings_version(_payload()), 1)

        for source in (
            {"version": 1},
            {"schema": "other", "version": 1},
            {"schema": AIO_GENERATION_SETTINGS_SCHEMA},
            {"schema": AIO_GENERATION_SETTINGS_SCHEMA, "version": "1"},
            {"schema": AIO_GENERATION_SETTINGS_SCHEMA, "version": True},
            {"schema": AIO_GENERATION_SETTINGS_SCHEMA, "version": 0},
        ):
            with self.subTest(source=source):
                with self.assertRaises(AIOGenerationMigrationError):
                    migrate_aio_generation_settings(source)

        with self.assertRaisesRegex(AIOGenerationMigrationError, "newer than target"):
            migrate_aio_generation_settings(_payload(2))
        with self.assertRaisesRegex(AIOGenerationMigrationError, "No AiO generation migration"):
            migrate_aio_generation_settings(_payload(), target_version=2)

    def test_test_only_registry_dispatches_consecutive_steps_in_order(self):
        calls: list[int] = []

        def advance(source, target: int):
            calls.append(target)
            result = dict(source)
            result["version"] = target
            result["trace"] = [*result.get("trace", []), target]
            return result

        registry = (
            AIOGenerationMigrationRegistry()
            .with_step(AIOGenerationMigrationStep(1, 2, lambda value: advance(value, 2)))
            .with_step(AIOGenerationMigrationStep(2, 3, lambda value: advance(value, 3)))
        )
        source = _payload()

        migrated = migrate_aio_generation_settings(
            source,
            target_version=3,
            registry=registry,
        )

        self.assertEqual(calls, [2, 3])
        self.assertEqual(migrated["version"], 3)
        self.assertEqual(migrated["trace"], [2, 3])
        self.assertEqual(source, _payload())
        self.assertEqual(AIO_GENERATION_MIGRATION_REGISTRY.steps, ())

    def test_registry_rejects_non_stepwise_duplicate_and_wrong_output(self):
        with self.assertRaisesRegex(AIOGenerationMigrationError, "exactly one version"):
            AIOGenerationMigrationStep(1, 3, lambda value: value)

        step = AIOGenerationMigrationStep(
            1,
            2,
            lambda value: {**value, "version": 2},
        )
        registry = AIOGenerationMigrationRegistry().with_step(step)
        with self.assertRaisesRegex(AIOGenerationMigrationError, "duplicate"):
            registry.with_step(step)

        wrong = AIOGenerationMigrationRegistry().with_step(
            AIOGenerationMigrationStep(
                1,
                2,
                lambda value: {**value, "version": 3},
            )
        )
        with self.assertRaisesRegex(AIOGenerationMigrationError, "returned version 3"):
            migrate_aio_generation_settings(
                _payload(),
                target_version=2,
                registry=wrong,
            )

    def test_failed_step_never_mutates_the_caller_payload(self):
        source = _payload()
        source_before = copy.deepcopy(source)

        def fail(working):
            working["extension"]["rows"][0]["name"] = "mutated working copy"
            raise RuntimeError("boom")

        registry = AIOGenerationMigrationRegistry().with_step(
            AIOGenerationMigrationStep(1, 2, fail)
        )

        with self.assertRaisesRegex(AIOGenerationMigrationError, "1->2 failed"):
            migrate_aio_generation_settings(
                source,
                target_version=2,
                registry=registry,
            )
        self.assertEqual(source, source_before)

    def test_pure_pipeline_preserves_legacy_normalizer_parity_without_runtime_wiring(self):
        legacy = {
            "schema": AIO_GENERATION_SETTINGS_SCHEMA,
            "version": 1,
            "sampler": {"dave": {"enabled": True}},
            "upscale": {"fit": {"enabled": True}},
            "save": {"filename_prefix": "legacy/path"},
        }
        legacy_before = copy.deepcopy(legacy)
        capabilities = {
            "_comfy_sampler_names": lambda: ["euler"],
            "_comfy_scheduler_names": lambda: ["simple"],
            "_impact_scheduler_names": lambda: ["sgm_uniform"],
            "_comfy_max_resolution": lambda: 16384,
        }
        with patch.multiple(nodes, **capabilities):
            expected = nodes._normalize_aio_generation_settings(legacy)
            actual = migrate_normalize_and_round_trip_aio_generation_settings(
                legacy,
                normalize=nodes._normalize_aio_generation_settings,
            )

        self.assertEqual(actual, expected)
        self.assertEqual(legacy, legacy_before)

        with patch.multiple(nodes, **capabilities):
            current_runtime = nodes._normalize_aio_generation_settings(
                {"schema": AIO_GENERATION_SETTINGS_SCHEMA, "version": 2}
            )
        self.assertEqual(current_runtime["version"], 2)
        with self.assertRaisesRegex(AIOGenerationMigrationError, "newer than target"):
            migrate_aio_generation_settings(_payload(2))


if __name__ == "__main__":
    unittest.main()
