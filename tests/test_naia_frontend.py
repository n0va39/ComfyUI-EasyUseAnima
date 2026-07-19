import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
NAIA_ENTRY = ROOT / "web" / "js" / "easyuse_anima_naia.js"
JSCONFIG = ROOT / "jsconfig.json"


class NaiaFrontendTests(unittest.TestCase):
    def test_entry_checkjs_host_boundaries_are_line_specific(self):
        entry_source = NAIA_ENTRY.read_text(encoding="utf-8")
        config = json.loads(JSCONFIG.read_text(encoding="utf-8"))

        self.assertEqual(entry_source.splitlines()[0], "// @ts-check")
        expect_error_targets = re.findall(
            r"^// @ts-expect-error[^\n]*\n([^\n]+)",
            entry_source,
            re.MULTILINE,
        )
        self.assertEqual(
            expect_error_targets,
            [
                'import { app } from "../../../scripts/app.js";',
                'import { ComfyWidgets } from "../../../scripts/widgets.js";',
            ],
        )
        for import_line in expect_error_targets:
            with self.subTest(import_line=import_line):
                self.assertIn(
                    "// @ts-expect-error ComfyUI provides this host module at runtime.\n"
                    f"{import_line}",
                    entry_source,
                )
        self.assertEqual(entry_source.count("// @ts-expect-error"), 2)
        for broad_suppression in ("@ts-ignore", "@ts-nocheck"):
            with self.subTest(broad_suppression=broad_suppression):
                self.assertNotIn(broad_suppression, entry_source)
        self.assertIn("web/js/easyuse_anima_naia.js", config["include"])

    def test_mixed_server_values_stay_unknown_until_consumers_coerce(self):
        entry_source = NAIA_ENTRY.read_text(encoding="utf-8")

        for annotation in (
            "@param {unknown} value",
            "@param {unknown} fallback",
            "@returns {unknown}",
        ):
            with self.subTest(annotation=annotation):
                self.assertIn(annotation, entry_source)
        self.assertIn(
            "return value.length > 0 ? value[0] : fallback;",
            entry_source,
        )
        self.assertIn("return value ?? fallback;", entry_source)
        for consumer in (
            "String(firstValue(message.prompt))",
            "String(firstValue(message.negative_prompt))",
            "Number(firstValue(message.width, 0))",
            "Number(firstValue(message.height, 0))",
            'String(firstValue(message.status, ""))',
            'String(firstValue(message.cached_signature, ""))',
        ):
            with self.subTest(consumer=consumer):
                self.assertIn(consumer, entry_source)

    def test_show_preview_hook_preserves_callback_length_and_forwards_arguments(self):
        entry_source = NAIA_ENTRY.read_text(encoding="utf-8")

        self.assertIn(
            "widget.callback = function (_value) {\n"
            "    const result = callback?.apply(this, arguments);",
            entry_source,
        )
        self.assertNotIn("widget.callback = function ()", entry_source)
        self.assertNotIn("widget.callback = function (value)", entry_source)


if __name__ == "__main__":
    unittest.main()
