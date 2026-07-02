from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import nodes


ROOT = Path(__file__).resolve().parents[1]
LOCALE_CODES = ("ko", "ja", "zh", "zh-CN")
HANGUL_RE = re.compile(r"[가-힣]")


def exposed_node_ids() -> set[str]:
    text = (ROOT / "__init__.py").read_text(encoding="utf-8")
    return set(re.findall(r'"(EasyUseAnima[^"]+)":', text))


class LocaleTests(unittest.TestCase):
    def test_node_defs_cover_public_nodes(self):
        public_nodes = exposed_node_ids()

        self.assertTrue(public_nodes)

        for locale_code in LOCALE_CODES:
            with self.subTest(locale=locale_code):
                node_defs_path = ROOT / "locales" / locale_code / "nodeDefs.json"
                data = json.loads(node_defs_path.read_text(encoding="utf-8"))
                self.assertFalse(public_nodes - set(data), public_nodes - set(data))

                for node_id in public_nodes:
                    node_data = data[node_id]
                    cls = getattr(nodes, node_id)
                    self.assertTrue(node_data.get("description"), node_id)
                    self.assertTrue(node_data.get("display_name"), node_id)

                    translated_inputs = node_data.get("inputs", {})
                    required_inputs = cls.INPUT_TYPES().get("required", {})
                    self.assertFalse(set(required_inputs) - set(translated_inputs), node_id)

                    translated_outputs = node_data.get("outputs", {})
                    for index in range(len(cls.RETURN_TYPES)):
                        self.assertIn(str(index), translated_outputs, node_id)

    def test_new_node_defs_do_not_fallback_to_korean(self):
        for locale_code in ("ja", "zh", "zh-CN"):
            with self.subTest(locale=locale_code):
                text = (ROOT / "locales" / locale_code / "nodeDefs.json").read_text(encoding="utf-8")
                self.assertIsNone(HANGUL_RE.search(text))

    def test_prompt_data_socket_names_are_not_localized(self):
        node_ids = (
            "EasyUseAnimaPromptStudioAdvancedV2",
            "EasyUseAnimaPromptDataUnpack",
            "EasyUseAnimaPromptDataConditioning",
        )
        for locale_code in LOCALE_CODES:
            data = json.loads((ROOT / "locales" / locale_code / "nodeDefs.json").read_text(encoding="utf-8"))
            self.assertEqual(
                data["EasyUseAnimaPromptDataUnpack"]["display_name"],
                nodes.PROMPT_DATA_TYPE,
            )
            for node_id in node_ids:
                with self.subTest(locale=locale_code, node=node_id):
                    cls = getattr(nodes, node_id)
                    outputs = data[node_id]["outputs"]
                    for index, name in enumerate(cls.RETURN_NAMES):
                        self.assertEqual(outputs[str(index)]["name"], name)

                    required_inputs = cls.INPUT_TYPES().get("required", {})
                    if nodes.PROMPT_DATA_TYPE in required_inputs:
                        prompt_data_inputs = data[node_id]["inputs"]
                        self.assertEqual(
                            prompt_data_inputs[nodes.PROMPT_DATA_TYPE]["name"],
                            nodes.PROMPT_DATA_TYPE,
                        )

    def test_easy_use_anima_input_socket_names_are_not_localized(self):
        for locale_code in LOCALE_CODES:
            data = json.loads((ROOT / "locales" / locale_code / "nodeDefs.json").read_text(encoding="utf-8"))
            self.assertEqual(
                data["EasyUseAnimaInput"]["outputs"]["0"]["name"],
                "easy use anima input",
            )
            self.assertEqual(
                data["EasyUseAnimaAIOGenerator"]["inputs"]["easy_use_anima_input"]["name"],
                "easy use anima input",
            )
            self.assertEqual(
                data["EasyUseAnimaAIOGenerator"]["outputs"]["2"]["name"],
                "metadata_json",
            )
            input_names = data["EasyUseAnimaInput"]["inputs"]
            self.assertNotIn("ckpt_name", input_names)
            for key in ("unet_name", "vae_name", "clip_name", "clip_type"):
                self.assertIn(key, input_names)


if __name__ == "__main__":
    unittest.main()
