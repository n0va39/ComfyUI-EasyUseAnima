from __future__ import annotations

import unittest
import uuid
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from easyuse_anima.profiles import contract


ROOT = Path(__file__).resolve().parents[1]


class ProfileContractTests(unittest.TestCase):
    def test_create_uses_uuid4_revision_one_and_preserves_payload(self):
        profile_id = uuid.UUID("12345678-1234-4234-9234-1234567890ab")

        with patch.object(contract.uuid, "uuid4", return_value=profile_id):
            document = contract.create_profile_document(
                contract.PROFILE_KIND_AIO,
                "Display",
                {"settings": {"future": {"kept": True}}},
            )

        self.assertEqual(
            document,
            {
                "version": 2,
                "profile_id": str(profile_id),
                "revision": 1,
                "name": "Display",
                "settings": {"future": {"kept": True}},
            },
        )

    def test_legacy_uuid5_is_exact_case_normalized_and_kind_scoped(self):
        self.assertEqual(
            contract.legacy_profile_id(contract.PROFILE_KIND_LORA, "Portrait"),
            "776e3a00-f7ea-57fa-b2fe-a608b3807f55",
        )
        self.assertEqual(
            contract.legacy_profile_id(contract.PROFILE_KIND_LORA, "portrait. "),
            "776e3a00-f7ea-57fa-b2fe-a608b3807f55",
        )
        self.assertEqual(
            contract.legacy_profile_id(contract.PROFILE_KIND_AIO, "Portrait"),
            "5f105f16-0eae-5d9e-894e-34243e44922b",
        )

    def test_legacy_uuid5_is_stable_across_fresh_processes(self):
        script = (
            f"import sys; sys.path.insert(0, {str(ROOT)!r}); "
            "from easyuse_anima.profiles.contract import legacy_profile_id; "
            "print(legacy_profile_id('lora', 'Portrait'))"
        )
        outputs = []
        for _ in range(2):
            result = subprocess.run(
                [sys.executable, "-I", "-B", "-c", script],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            outputs.append(result.stdout.strip())

        self.assertEqual(
            outputs,
            [
                "776e3a00-f7ea-57fa-b2fe-a608b3807f55",
                "776e3a00-f7ea-57fa-b2fe-a608b3807f55",
            ],
        )

    def test_v1_and_missing_v2_fields_are_pure_legacy_views(self):
        for document in (
            {"version": 1, "settings": {}},
            {"settings": {}},
            {"version": 2, "name": "Legacy", "settings": {}},
        ):
            with self.subTest(document=document):
                interpreted = contract.interpret_profile_document(
                    contract.PROFILE_KIND_AIO,
                    "Legacy",
                    document,
                )

                self.assertEqual(interpreted["version"], 2)
                self.assertEqual(interpreted["revision"], 0)
                self.assertEqual(
                    interpreted["profile_id"],
                    contract.legacy_profile_id(contract.PROFILE_KIND_AIO, "Legacy"),
                )
                self.assertEqual(interpreted["name"], "Legacy")

    def test_update_preserves_identity_and_advances_current_revision(self):
        current = {
            "version": 2,
            "profile_id": "12345678-1234-4234-9234-1234567890ab",
            "revision": 7,
            "name": "Current",
            "settings": {"value": "old"},
        }

        updated = contract.update_profile_document(
            contract.PROFILE_KIND_AIO,
            "Current",
            current,
            {"settings": {"value": "new"}},
        )

        self.assertEqual(updated["profile_id"], current["profile_id"])
        self.assertEqual(updated["revision"], 8)
        self.assertEqual(updated["settings"], {"value": "new"})

    def test_legacy_update_promotes_to_revision_one(self):
        updated = contract.update_profile_document(
            contract.PROFILE_KIND_LORA,
            "Legacy",
            {"version": 1, "profile_data": {}},
            {"profile_count": 1, "profile_index": 1, "profile_data": {}},
        )

        self.assertEqual(updated["revision"], 1)
        self.assertEqual(
            updated["profile_id"],
            contract.legacy_profile_id(contract.PROFILE_KIND_LORA, "Legacy"),
        )

    def test_rename_preserves_source_identity_and_content_revision(self):
        current = {
            "version": 2,
            "profile_id": "12345678-1234-4234-9234-1234567890ab",
            "revision": 4,
            "name": "Source",
            "settings": {"value": "source"},
        }

        renamed = contract.rename_profile_document(
            contract.PROFILE_KIND_AIO,
            "Source",
            "Target",
            current,
            {"settings": current["settings"]},
        )

        self.assertEqual(renamed["name"], "Target")
        self.assertEqual(renamed["profile_id"], current["profile_id"])
        self.assertEqual(renamed["revision"], 4)

    def test_invalid_complete_v2_taxonomy_is_rejected(self):
        invalid_documents = (
            {"version": True, "settings": {}},
            {"version": 2.0, "settings": {}},
            {
                "version": 3,
                "profile_id": "12345678-1234-4234-9234-1234567890ab",
                "revision": 1,
                "name": "Invalid",
            },
            {
                "version": 2,
                "profile_id": "not-a-uuid",
                "revision": 1,
                "name": "Invalid",
            },
            {
                "version": 2,
                "profile_id": "12345678-1234-4234-9234-1234567890ab",
                "revision": True,
                "name": "Invalid",
            },
            {
                "version": 2,
                "profile_id": "12345678-1234-4234-9234-1234567890ab",
                "revision": 1,
                "name": [],
            },
        )

        for document in invalid_documents:
            with self.subTest(document=document), self.assertRaises(
                contract.ProfileContractError
            ):
                contract.interpret_profile_document(
                    contract.PROFILE_KIND_AIO,
                    "Invalid",
                    document,
                )


if __name__ == "__main__":
    unittest.main()
