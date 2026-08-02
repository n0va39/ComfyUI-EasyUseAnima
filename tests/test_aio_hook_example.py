from __future__ import annotations

import ast
import unittest
from pathlib import Path
from types import SimpleNamespace

from easyuse_anima.extensions.aio import (
    EASYUSE_ANIMA_AIO_HOOK_TYPE,
    AioHookPatch,
    AioStage,
    AioStagePhase,
)
from examples.third_party_aio_hook import ExampleEasyUseAnimaBrightnessHook


class _Image:
    shape = (1, 8, 8, 3)

    def __init__(self, operations=()):
        self.operations = operations

    def mul(self, value):
        return _Image((*self.operations, ("mul", value)))

    def clamp(self, low, high):
        return _Image((*self.operations, ("clamp", low, high)))


class _Services:
    def __init__(self):
        self.previews = []

    def emit_preview(self, stage, image, label=None):
        self.previews.append((stage, image, label))

    def register_cleanup(self, callback):
        del callback


class AioHookExampleTests(unittest.TestCase):
    def test_copyable_example_defers_public_import_until_node_execution(self):
        example_path = (
            Path(__file__).resolve().parents[1]
            / "examples"
            / "third_party_aio_hook"
            / "__init__.py"
        )
        module = ast.parse(example_path.read_text(encoding="utf-8"))
        public_imports = [
            node
            for node in module.body
            if isinstance(node, ast.ImportFrom)
            and (node.module or "").startswith("easyuse_anima")
        ]

        self.assertEqual(public_imports, [])

    def test_copyable_example_builds_a_stable_public_definition(self):
        node = ExampleEasyUseAnimaBrightnessHook()
        definition = node.build(0.75, True)[0]
        descriptor = definition.describe()

        self.assertEqual(
            ExampleEasyUseAnimaBrightnessHook.RETURN_TYPES,
            (EASYUSE_ANIMA_AIO_HOOK_TYPE,),
        )
        self.assertEqual(descriptor.hook_id, "example.brightness")
        self.assertEqual(
            descriptor.fingerprint,
            {
                "strength": 0.75,
                "emit_preview": True,
                "algorithm": "multiply-clamp-v1",
            },
        )

    def test_copyable_example_uses_out_of_place_image_patch_and_preview(self):
        services = _Services()
        definition = ExampleEasyUseAnimaBrightnessHook().build(0.75, True)[0]
        session = definition.create_session(SimpleNamespace(services=services))
        source = _Image()
        event = SimpleNamespace(
            stage=AioStage.POSTPROCESS,
            phase=AioStagePhase.AFTER,
            state=SimpleNamespace(image=source),
        )

        patch = session.after_stage(event)

        self.assertIsInstance(patch, AioHookPatch)
        self.assertIsNot(patch.image, source)
        self.assertEqual(
            patch.image.operations,
            (("mul", 0.75), ("clamp", 0.0, 1.0)),
        )
        self.assertEqual(patch.metadata["strength"], 0.75)
        self.assertEqual(services.previews[0][2], "brightness")


if __name__ == "__main__":
    unittest.main()
