from __future__ import annotations

import inspect
import json
import unittest
from pathlib import Path

from easyuse_anima.aio import legacy_generation
from easyuse_anima.nodes import aio_nodes

ROOT = Path(__file__).resolve().parents[1]
READ_ONLY_JSON_EVIDENCE = (
    ROOT / "tests" / "fixtures" / "aio_legacy_execution_trace.v1.json",
    ROOT / "tests" / "fixtures" / "aio_generation_settings_0_5_2.json",
    ROOT / "tests" / "fixtures" / "node_contracts_0_5_2.json",
    ROOT / "tests" / "fixtures" / "python_compatibility_surface.v1.json",
    ROOT / "tests" / "fixtures" / "comfy_host_compatibility.v1.json",
    ROOT
    / "docs"
    / "example_workflows"
    / "EasyUse_Anima_AiO_generator_release_ko.json",
)


class AIOStageIntegrationMatrixTests(unittest.TestCase):
    def test_node_and_legacy_adapters_converge_on_canonical_pipeline(self):
        node_source = inspect.getsource(aio_nodes.EasyUseAnimaAIOGenerator.generate)
        normalized_adapter_source = inspect.getsource(
            legacy_generation._run_aio_normalized_legacy_generation
        )
        legacy_adapter_source = inspect.getsource(
            legacy_generation._run_aio_legacy_generation
        )

        self.assertIn("_run_aio_generation_pipeline", node_source)
        self.assertNotIn("_run_aio_normalized_legacy_generation", node_source)
        self.assertIn("_run_aio_generation_pipeline", normalized_adapter_source)
        self.assertIn(
            "_run_aio_normalized_legacy_generation",
            legacy_adapter_source,
        )

    def test_canonical_pipeline_owns_all_stage_and_lifecycle_connections(self):
        pipeline_source = inspect.getsource(
            legacy_generation._run_aio_generation_pipeline
        )
        normalized_adapter_source = inspect.getsource(
            legacy_generation._run_aio_normalized_legacy_generation
        )

        for owner in (
            "AIOFirstPassStage",
            "AIOHighresStage",
            "AIODetailerStage",
            "AIOUpscaleStage",
            "AIOPostprocessStage",
            "AIOSaveOutputStage",
            "EphemeralModelRegistry",
            "ModelVariantResolver",
            "PreviewCollector",
        ):
            self.assertIn(owner, pipeline_source)
            self.assertNotIn(owner, normalized_adapter_source)

    def test_read_only_integration_evidence_is_valid_json(self):
        for path in READ_ONLY_JSON_EVIDENCE:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertTrue(path.is_file())
                parsed = json.loads(path.read_text(encoding="utf-8"))
                self.assertIsInstance(parsed, dict)
                self.assertTrue(parsed)

    def test_representative_workflow_contains_aio_generator_and_package_metadata(self):
        workflow = json.loads(
            READ_ONLY_JSON_EVIDENCE[-1].read_text(encoding="utf-8")
        )
        aio_nodes_in_workflow = [
            node
            for node in workflow["nodes"]
            if node.get("type") == "EasyUseAnimaAIOGenerator"
        ]

        self.assertEqual(len(aio_nodes_in_workflow), 1)
        workflow_metadata = workflow["extra"]["easyuse_anima_workflow"]
        required_node_packs = workflow_metadata["required_node_packs"]
        self.assertIn(
            "ComfyUI-EasyUseAnima",
            {node_pack["name"] for node_pack in required_node_packs},
        )
        self.assertEqual(workflow_metadata["package"], "comfyui-easyuse-anima")


if __name__ == "__main__":
    unittest.main()
