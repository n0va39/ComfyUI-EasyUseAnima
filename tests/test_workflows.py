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
    ROOT / "example_workflows" / "EasyUse_Anima_feature_test_release_ko.json",
    ROOT / "example_workflows" / "EasyUse_Anima_feature_test_release_en.json",
    ROOT / "example_workflows" / "Anima_AiO_v6.0_release_ko.json",
    ROOT / "example_workflows" / "Anima_AiO_v6.0_release_en.json",
    ROOT / "docs" / "workflows" / "Anima_AiO_v6.0_release_ko.json",
    ROOT / "docs" / "workflows" / "Anima_AiO_v6.0_release_en.json",
)
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

        for workflow_path in RELEASE_WORKFLOWS:
            with self.subTest(path=workflow_path.name):
                matches = list(walk(load_workflow(workflow_path)))
                self.assertFalse(matches, matches[:5])

    def test_release_workflow_links_match_node_slots(self):
        for path in RELEASE_WORKFLOWS:
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


if __name__ == "__main__":
    unittest.main()
