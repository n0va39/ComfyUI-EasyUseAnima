from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT_STUDIO_ADVANCED_OUTPUTS = (
    "positive_prompt",
    "negative_prompt",
    "anima_mod_guidance_quality_tags",
    "anima_mod_guidance_negative_prompt",
    "use_anima_mod_guidance",
    "use_negative_anima_mod_guidance",
    "metadata_prompt",
    "metadata_negative_prompt",
    "width",
    "height",
)
RELEASE_WORKFLOWS = (
    ROOT / "docs" / "example_workflows" / "EasyUse_Anima_feature_test_release_ko.json",
    ROOT / "docs" / "example_workflows" / "EasyUse_Anima_feature_test_release_en.json",
    ROOT / "docs" / "example_workflows" / "Anima_AiO_v6.0_release_ko.json",
    ROOT / "docs" / "example_workflows" / "Anima_AiO_v6.0_release_en.json",
)
EXAMPLE_WORKFLOW_DIR = ROOT / "docs" / "example_workflows"
EXAMPLE_WORKFLOWS = tuple(sorted(EXAMPLE_WORKFLOW_DIR.glob("*.json")))
AIO_GENERATOR_WORKFLOW = EXAMPLE_WORKFLOW_DIR / "EasyUse_Anima_AiO_generator_release_ko.json"
MOJIBAKE_LATIN1_RE = re.compile(r"[\u0080-\u00ff]")


def load_workflow(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def link_map(workflow: dict) -> dict[int, list]:
    return {
        int(link[0]): link
        for link in workflow.get("links") or []
        if isinstance(link, list) and len(link) >= 6
    }


class ReleaseWorkflowTests(unittest.TestCase):
    def project_version(self) -> str:
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
        self.assertIsNotNone(match)
        return match.group(1)

    def test_example_workflows_parse_as_json(self):
        self.assertTrue(EXAMPLE_WORKFLOWS)
        for workflow_path in EXAMPLE_WORKFLOWS:
            with self.subTest(path=workflow_path.name):
                workflow = load_workflow(workflow_path)
                self.assertIsInstance(workflow.get("nodes"), list)
                self.assertIsInstance(workflow.get("links"), list)

    def test_release_workflows_do_not_contain_latin1_mojibake(self):
        def walk(value, path: str = ""):
            if isinstance(value, dict):
                for key, child in value.items():
                    yield from walk(child, f"{path}.{key}" if path else str(key))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    yield from walk(child, f"{path}[{index}]")
            elif isinstance(value, str) and MOJIBAKE_LATIN1_RE.search(value):
                yield path, value

        for workflow_path in EXAMPLE_WORKFLOWS:
            with self.subTest(path=workflow_path.name):
                matches = list(walk(load_workflow(workflow_path)))
                self.assertFalse(matches, matches[:5])

    def test_release_workflow_links_match_node_slots(self):
        for path in EXAMPLE_WORKFLOWS:
            with self.subTest(path=path.name):
                workflow = load_workflow(path)
                links = link_map(workflow)
                nodes = {node["id"]: node for node in workflow.get("nodes", [])}

                for node in nodes.values():
                    for output_index, output in enumerate(node.get("outputs") or []):
                        for link_id in output.get("links") or []:
                            self.assertIn(link_id, links, f"{path}: missing output link {link_id}")
                            link = links[link_id]
                            self.assertEqual(link[1:3], [node["id"], output_index], f"{path}: output link {link_id}")

                    for input_index, input_info in enumerate(node.get("inputs") or []):
                        link_id = input_info.get("link")
                        if link_id is None:
                            continue
                        self.assertIn(link_id, links, f"{path}: missing input link {link_id}")
                        link = links[link_id]
                        self.assertEqual(link[3:5], [node["id"], input_index], f"{path}: input link {link_id}")

    def test_prompt_studio_advanced_release_outputs_use_current_socket_order(self):
        for path in RELEASE_WORKFLOWS:
            with self.subTest(path=path.name):
                workflow = load_workflow(path)
                nodes = [
                    node
                    for node in workflow.get("nodes", [])
                    if node.get("type") == "EasyUseAnimaPromptStudioAdvanced"
                ]
                self.assertTrue(nodes, path)
                for node in nodes:
                    self.assertEqual(
                        tuple(output.get("name") for output in node.get("outputs") or []),
                        PROMPT_STUDIO_ADVANCED_OUTPUTS,
                        f"{path}: node {node.get('id')}",
                    )

    def test_feature_workflows_connect_negative_mod_guidance_prompt(self):
        for path in RELEASE_WORKFLOWS[:2]:
            with self.subTest(path=path.name):
                workflow = load_workflow(path)
                links = link_map(workflow)
                node = next(
                    node
                    for node in workflow.get("nodes", [])
                    if node.get("type") == "EasyUseAnimaPromptStudioAdvanced"
                )
                negative_output = node["outputs"][3]
                self.assertEqual(negative_output["name"], "anima_mod_guidance_negative_prompt")
                self.assertTrue(negative_output.get("links"), f"{path}: negative AMG output is unconnected")
                for link_id in negative_output["links"]:
                    self.assertEqual(links[link_id][1:3], [node["id"], 3])

    def test_feature_workflow_language_variants_use_same_socket_topology(self):
        def topology(path: Path) -> list[tuple[int, int, int, int, str]]:
            workflow = load_workflow(path)
            return [
                (int(link[1]), int(link[2]), int(link[3]), int(link[4]), str(link[5]))
                for link in workflow.get("links") or []
                if isinstance(link, list) and len(link) >= 6
            ]

        ko_path, en_path = RELEASE_WORKFLOWS[:2]
        self.assertEqual(topology(en_path), topology(ko_path))

    def test_example_workflow_package_versions_match_project(self):
        version = self.project_version()
        for path in EXAMPLE_WORKFLOWS:
            with self.subTest(path=path.name):
                metadata = load_workflow(path).get("extra", {}).get("easyuse_anima_workflow")
                if not isinstance(metadata, dict):
                    continue
                self.assertEqual(metadata.get("package_version"), version)

    def test_aio_generator_sample_lists_required_node_packs(self):
        workflow = load_workflow(AIO_GENERATOR_WORKFLOW)
        metadata = workflow.get("extra", {}).get("easyuse_anima_workflow")
        self.assertIsInstance(metadata, dict)
        packs = metadata.get("required_node_packs")
        self.assertIsInstance(packs, list)
        names = {str(item.get("name")) for item in packs if isinstance(item, dict)}
        self.assertIn("ComfyUI-Spectrum-KSampler", names)
        self.assertIn("ComfyUI-Image-Saver", names)
        self.assertIn("ComfyUI-Anima-DAVE", names)
        self.assertIn("ComfyUI-KJNodes", names)
        self.assertIn("ComfyUI-Impact-Pack", names)
        required = {
            str(item.get("name")): bool(item.get("required_for_sample"))
            for item in packs
            if isinstance(item, dict)
        }
        self.assertTrue(required["ComfyUI-Spectrum-KSampler"])
        self.assertTrue(required["ComfyUI-Image-Saver"])
        self.assertFalse(required["ComfyUI-Anima-DAVE"])
        self.assertFalse(required["ComfyUI-KJNodes"])
        self.assertFalse(required["ComfyUI-Impact-Pack"])
        self.assertEqual(
            metadata.get("sampler_paths"),
            ["comfy_ksampler", "spectrum_mod_guidance_advanced", "spectrum_spd_speed"],
        )


if __name__ == "__main__":
    unittest.main()
