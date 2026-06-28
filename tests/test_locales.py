from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import nodes


ROOT = Path(__file__).resolve().parents[1]


def exposed_node_ids() -> set[str]:
    text = (ROOT / "__init__.py").read_text(encoding="utf-8")
    return set(re.findall(r'"(EasyUseAnima[^"]+)":', text))


class LocaleTests(unittest.TestCase):
    def test_korean_node_defs_cover_public_nodes(self):
        node_defs_path = ROOT / "locales" / "ko" / "nodeDefs.json"
        data = json.loads(node_defs_path.read_text(encoding="utf-8"))
        public_nodes = exposed_node_ids()

        self.assertTrue(public_nodes)
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


if __name__ == "__main__":
    unittest.main()
