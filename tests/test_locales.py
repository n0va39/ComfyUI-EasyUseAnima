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
    def test_sam3_convenience_nodes_are_not_public(self):
        removed_node_ids = {
            "EasyUseAnimaSAM3Context",
            "EasyUseAnimaSAM3Detailer",
        }
        public_nodes = exposed_node_ids()

        self.assertFalse(removed_node_ids & public_nodes)

        for locale_code in LOCALE_CODES:
            data = json.loads((ROOT / "locales" / locale_code / "nodeDefs.json").read_text(encoding="utf-8"))
            with self.subTest(locale=locale_code):
                self.assertFalse(removed_node_ids & set(data))

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

    def test_wildcard_tooltips_cover_syntax_and_mode_lifecycle(self):
        standalone_reproduce_terms = {
            "ko": ("와일드카드 엔진", "파일 와일드카드", "그대로 출력"),
            "ja": ("ワイルドカードエンジン", "ファイルワイルドカード", "そのまま出力"),
            "zh": ("萬用字元引擎", "檔案萬用字元", "原樣輸出"),
            "zh-CN": ("通配符引擎", "文件通配符", "原样输出"),
        }
        for locale_code in LOCALE_CODES:
            data = json.loads(
                (ROOT / "locales" / locale_code / "nodeDefs.json").read_text(
                    encoding="utf-8"
                )
            )
            with self.subTest(locale=locale_code, node="EasyUseAnimaWildcard"):
                inputs = data["EasyUseAnimaWildcard"]["inputs"]
                for syntax in (
                    "__name__",
                    "{a|b|c}",
                    "N::weight",
                    "{n$$...}",
                    "{min-max$$separator$$...}",
                    "N#__name__",
                    "* glob",
                    "#",
                ):
                    self.assertIn(syntax, inputs["text"]["tooltip"])
                self.assertGreater(len(inputs["populated_text"]["tooltip"]), 50)
                self.assertIn("text", inputs["populated_text"]["tooltip"])
                self.assertGreater(len(inputs["mode"]["tooltip"]), 100)
                self.assertIn("seed", inputs["mode"]["tooltip"])
                self.assertIn("populated_text", inputs["mode"]["tooltip"])
                engine_term, file_term, stale_term = standalone_reproduce_terms[locale_code]
                self.assertIn(engine_term, inputs["populated_text"]["tooltip"])
                self.assertIn(file_term, inputs["mode"]["tooltip"])
                self.assertNotIn(stale_term, inputs["populated_text"]["tooltip"])
                self.assertNotIn(
                    "Cached expanded prompt used by fixed and reproduce modes.",
                    inputs["populated_text"]["tooltip"],
                )

            for node_id in (
                "EasyUseAnimaPromptStudioAdvanced",
                "EasyUseAnimaPromptStudioAdvancedV2",
                "EasyUseAnimaPromptStudioRegional",
            ):
                with self.subTest(locale=locale_code, node=node_id):
                    inputs = data[node_id]["inputs"]
                    self.assertGreater(len(inputs["wildcard_mode"]["tooltip"]), 50)
                    self.assertIn("seed", inputs["wildcard_mode"]["tooltip"])
                    self.assertGreater(len(inputs["wildcard_seed"]["tooltip"]), 20)
                    self.assertGreater(
                        len(inputs["wildcard_seed_after_generate"]["tooltip"]),
                        25,
                    )
                    self.assertIn(
                        "increment",
                        inputs["wildcard_seed_after_generate"]["tooltip"],
                    )

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
