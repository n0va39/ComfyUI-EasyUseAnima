from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_FIXTURE = ROOT / "tests" / "fixtures" / "autocomplete_edit_contract.v1.json"


class AutocompleteEditContractTests(unittest.TestCase):
    def test_versioned_setting_keys_defaults_and_accepted_values_are_fixed(self):
        self.assertEqual(
            json.loads(CONTRACT_FIXTURE.read_text(encoding="utf-8")),
            {
                "schema_version": 1,
                "settings": {
                    "artist_prefix": {
                        "internal_key": "autocomplete.artist_prefix",
                        "comfy_key": (
                            "EasyUseAnima.Prompt.AutocompleteArtistPrefix"
                        ),
                        "default": "@",
                        "max_length": 32,
                    },
                    "commit_mode": {
                        "internal_key": "autocomplete.commit_mode",
                        "comfy_key": "EasyUseAnima.Prompt.AutocompleteCommitMode",
                        "default": "smart",
                        "accepted_values": ["smart", "insert", "replace"],
                    },
                    "selection_parenthesis_weight": {
                        "internal_key": (
                            "prompt_studio.selection_parenthesis_weight"
                        ),
                        "comfy_key": (
                            "EasyUseAnima.Prompt.SelectionParenthesisWeight"
                        ),
                        "default": "false",
                        "accepted_values": ["false", "true"],
                    },
                },
            },
        )


if __name__ == "__main__":
    unittest.main()
