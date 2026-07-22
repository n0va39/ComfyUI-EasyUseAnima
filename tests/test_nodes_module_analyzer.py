from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYZER_PATH = ROOT / "tools" / "analyze_nodes_module.py"


def load_analyzer():
    spec = importlib.util.spec_from_file_location("easyuse_anima_nodes_analyzer", ANALYZER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load analyzer: {ANALYZER_PATH.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


analyzer = load_analyzer()


class NodesModuleAnalyzerTests(unittest.TestCase):
    def test_synthetic_module_reports_definitions_locations_and_references(self):
        source = """\
import importlib
from package import helper as imported_helper

VALUE = 3

def use_value(name):
    return VALUE + getattr(importlib, name)

class ContractNode:
    marker = VALUE

def load_dynamic():
    return importlib.import_module("optional.module")
"""

        report = analyzer.analyze_source(source, source_label="synthetic.py")

        self.assertEqual(report["top_level"]["function_count"], 2)
        self.assertEqual(report["top_level"]["class_count"], 1)
        self.assertEqual(
            [item["name"] for item in report["top_level"]["globals"]],
            ["VALUE"],
        )
        self.assertIn(
            {"from": "use_value", "to": "VALUE"},
            report["reference_edges"],
        )
        self.assertEqual(
            [item["callee"] for item in report["dynamic_lookups"]],
            ["getattr", "importlib.import_module"],
        )
        self.assertEqual(
            [(item["module"], item["name"], item["scope"]) for item in report["imports"]],
            [
                ("importlib", None, "<module>"),
                ("package", "helper", "<module>"),
            ],
        )

    def test_json_and_text_rendering_are_deterministic(self):
        first_report = analyzer.analyze_path(ROOT / "nodes.py")
        second_report = analyzer.analyze_path(ROOT / "nodes.py")

        self.assertEqual(analyzer.render_json(first_report), analyzer.render_json(second_report))
        self.assertEqual(analyzer.render_text(first_report), analyzer.render_text(second_report))

    def test_current_nodes_module_shape_matches_recorded_baseline(self):
        report = analyzer.analyze_path(ROOT / "nodes.py")

        self.assertEqual(report["git_blob_sha1"], "661cde3207cde85f9f4786872255edeabcf22f24")
        # Issues #168 C168-06 and #184 preserve the typed AiO facade while
        # moving the generation normalizer behind direct root aliases.
        self.assertEqual(report["top_level"]["function_count"], 97)
        self.assertEqual(report["top_level"]["class_count"], 4)
        self.assertEqual(report["line_count"], 4_519)
        class_names = {item["name"] for item in report["top_level"]["classes"]}
        self.assertIn("EasyUseAnimaAIOGenerator", class_names)
        self.assertNotIn("EasyUseAnimaPromptStudioAdvanced", class_names)
        self.assertNotIn("EasyUseAnimaPromptStudioAdvancedV2", class_names)
        self.assertNotIn("EasyUseAnimaPromptStudioExtend", class_names)
        self.assertNotIn("EasyUseAnimaNAIARandomPrompt", class_names)
        self.assertNotIn("EasyUseAnimaWildcard", class_names)
        self.assertNotIn("EasyUseAnimaImageScaleByMultiple", class_names)
        self.assertNotIn("EasyUseAnimaDetailerAlignHook", class_names)
        self.assertNotIn("EasyUseAnimaLoraPreset", class_names)
        self.assertNotIn("EasyUseAnimaPromptCorrector", class_names)
        self.assertNotIn("EasyUseAnimaPromptCorrectorSimple", class_names)
        self.assertNotIn("EasyUseAnimaPromptBuilder", class_names)
        self.assertNotIn("EasyUseAnimaPromptStudio", class_names)
        self.assertNotIn("EasyUseAnimaPromptStudioRegional", class_names)
        self.assertNotIn("EasyUseAnimaRegionalConditioning", class_names)
        self.assertNotIn("EasyUseAnimaPromptDataUnpack", class_names)
        self.assertNotIn("EasyUseAnimaArtistMixConditioning", class_names)
        self.assertNotIn("EasyUseAnimaPromptDataConditioning", class_names)
        self.assertNotIn("EasyUseAnimaSAM3Context", class_names)
        self.assertNotIn("_EasyUseAnimaImpactDetailerDelegate", class_names)
        self.assertNotIn("EasyUseAnimaSAM3Detailer", class_names)

    def test_external_source_label_does_not_expose_parent_directories(self):
        label = analyzer._source_label(Path("Z:/private/user/data/example.py"))

        self.assertEqual(label, "example.py")


if __name__ == "__main__":
    unittest.main()
