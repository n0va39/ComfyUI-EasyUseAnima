from __future__ import annotations

import subprocess
import sys
import types
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from easyuse_anima.seed import execution_identity


ROOT = Path(__file__).resolve().parents[1]


class SeedExecutionIdentityTests(unittest.TestCase):
    def test_comfy_context_is_loaded_only_when_the_adapter_is_called(self):
        calls: list[str] = []
        raw_context = types.SimpleNamespace(
            prompt_id=" prompt-a ",
            node_id=" 42 ",
            list_index=3,
        )
        module = types.SimpleNamespace(
            get_executing_context=lambda: raw_context,
        )

        context = execution_identity.read_comfy_execution_context(
            load_module=lambda module_name: (
                calls.append(module_name) or module
            ),
        )

        self.assertEqual(calls, ["comfy_execution.utils"])
        self.assertEqual(
            context,
            execution_identity.SeedExecutionContext(
                prompt_id="prompt-a",
                node_id="42",
                list_index=3,
            ),
        )

    def test_context_identity_is_idempotent_and_context_node_wins(self):
        context = execution_identity.SeedExecutionContext(
            prompt_id="prompt-a",
            node_id="context-node",
            list_index=2,
        )

        first = execution_identity.resolve_seed_execution_identity(
            "prompt_studio",
            unique_id="different-hidden-node",
            load_context=lambda: context,
        )
        second = execution_identity.resolve_seed_execution_identity(
            "prompt_studio",
            unique_id="different-hidden-node",
            load_context=lambda: context,
        )

        self.assertEqual(first, second)
        self.assertIsNotNone(first)
        assert first is not None
        self.assertIn('"context-node"', first.stream_id)
        self.assertNotIn("different-hidden-node", first.stream_id)
        self.assertIn('"prompt-a"', first.request_id)
        self.assertIn(",2]", first.request_id)

    def test_stream_is_stable_across_prompts_but_request_is_not(self):
        first = execution_identity.resolve_seed_execution_identity(
            "aio",
            load_context=lambda: execution_identity.SeedExecutionContext(
                prompt_id="prompt-a",
                node_id="7",
            ),
        )
        second = execution_identity.resolve_seed_execution_identity(
            "aio",
            load_context=lambda: execution_identity.SeedExecutionContext(
                prompt_id="prompt-b",
                node_id="7",
            ),
        )

        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        assert first is not None and second is not None
        self.assertEqual(first.stream_id, second.stream_id)
        self.assertNotEqual(first.request_id, second.request_id)

    def test_list_index_distinguishes_mapped_calls(self):
        identities = [
            execution_identity.resolve_seed_execution_identity(
                "aio",
                load_context=lambda index=index: (
                    execution_identity.SeedExecutionContext(
                        prompt_id="prompt-a",
                        node_id="7",
                        list_index=index,
                    )
                ),
            )
            for index in (None, 0, 1)
        ]

        self.assertEqual(len({item.request_id for item in identities if item}), 3)
        self.assertEqual(len({item.stream_id for item in identities if item}), 1)

    def test_unique_id_fallback_keeps_stream_and_refreshes_request(self):
        opaque_ids = iter(("opaque-a", "opaque-b"))

        first = execution_identity.resolve_seed_execution_identity(
            "aio",
            unique_id=[42],
            load_context=lambda: None,
            request_id_factory=lambda: next(opaque_ids),
        )
        second = execution_identity.resolve_seed_execution_identity(
            "aio",
            unique_id=(42,),
            load_context=lambda: None,
            request_id_factory=lambda: next(opaque_ids),
        )

        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        assert first is not None and second is not None
        self.assertEqual(first.stream_id, second.stream_id)
        self.assertNotEqual(first.request_id, second.request_id)
        self.assertIn('"fallback","opaque-a"', first.request_id)
        self.assertIn('"fallback","opaque-b"', second.request_id)

    def test_missing_identity_returns_none_without_allocating_request(self):
        allocations = 0

        def allocate() -> str:
            nonlocal allocations
            allocations += 1
            return "unused"

        for unique_id in (None, "", "  ", True, [], ()):
            with self.subTest(unique_id=unique_id):
                self.assertIsNone(
                    execution_identity.resolve_seed_execution_identity(
                        "aio",
                        unique_id=unique_id,
                        load_context=lambda: None,
                        request_id_factory=allocate,
                    )
                )

        self.assertEqual(allocations, 0)

    def test_host_absence_and_malformed_context_are_safe(self):
        def unavailable(_module_name: str) -> object:
            raise ImportError("host not installed")

        malformed = types.SimpleNamespace(
            get_executing_context=lambda: types.SimpleNamespace(
                prompt_id="prompt-a",
                node_id="",
                list_index=0,
            )
        )

        self.assertIsNone(
            execution_identity.read_comfy_execution_context(
                load_module=unavailable
            )
        )
        self.assertIsNone(
            execution_identity.read_comfy_execution_context(
                load_module=lambda _module_name: malformed
            )
        )

    def test_namespaced_json_encoding_avoids_delimiter_collisions(self):
        first = execution_identity.resolve_seed_execution_identity(
            "feature:a",
            load_context=lambda: execution_identity.SeedExecutionContext(
                prompt_id="prompt",
                node_id="b",
            ),
        )
        second = execution_identity.resolve_seed_execution_identity(
            "feature",
            load_context=lambda: execution_identity.SeedExecutionContext(
                prompt_id="prompt",
                node_id="a:b",
            ),
        )

        self.assertNotEqual(first, second)

    def test_contract_values_are_immutable_and_reject_invalid_parts(self):
        context = execution_identity.SeedExecutionContext(
            prompt_id="prompt",
            node_id="7",
        )
        with self.assertRaises(FrozenInstanceError):
            context.node_id = "8"

        for values in (
            {"prompt_id": "", "node_id": "7", "list_index": None},
            {"prompt_id": "prompt", "node_id": "", "list_index": None},
            {"prompt_id": "prompt", "node_id": "7", "list_index": -1},
            {"prompt_id": "prompt", "node_id": "7", "list_index": True},
        ):
            with self.subTest(values=values), self.assertRaises(
                execution_identity.SeedExecutionIdentityError
            ):
                execution_identity.SeedExecutionContext(**values)

        with self.assertRaises(execution_identity.SeedExecutionIdentityError):
            execution_identity.resolve_seed_execution_identity(
                "",
                unique_id="7",
                load_context=lambda: None,
            )
        with self.assertRaises(execution_identity.SeedExecutionIdentityError):
            execution_identity.resolve_seed_execution_identity(
                "aio",
                unique_id="7",
                load_context=lambda: None,
                request_id_factory=lambda: "",
            )
        with self.assertRaises(TypeError):
            execution_identity.resolve_seed_execution_identity(
                "aio",
                unique_id="7",
                load_context=lambda: object(),
            )

    def test_contract_import_does_not_import_comfy_in_a_fresh_process(self):
        script = (
            f"import sys; sys.path.insert(0, {str(ROOT)!r}); "
            "import easyuse_anima.seed.execution_identity; "
            "print(int('comfy_execution' in sys.modules))"
        )

        result = subprocess.run(
            [sys.executable, "-I", "-B", "-c", script],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(), "0")


if __name__ == "__main__":
    unittest.main()
