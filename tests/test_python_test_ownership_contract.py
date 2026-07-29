from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT / "tests" / "fixtures" / "python_test_ownership_contract.v1.json"
)
EXPECTED_CATEGORIES = {
    "adapter_api_node_integration",
    "live_host",
    "migration_compatibility",
    "package_archive",
    "pure_service_unit",
}


class PythonTestOwnershipContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.groups = cls.contract["groups"]
        cls.matrices = {
            matrix["name"]: matrix for matrix in cls.contract["matrices"]
        }

    def test_schema_categories_and_unittest_runner_are_fixed(self):
        self.assertEqual(
            set(self.contract),
            {
                "categories",
                "groups",
                "matrices",
                "root_private_import_policy",
                "runner",
                "schema_version",
            },
        )
        self.assertEqual(self.contract["schema_version"], 1)
        self.assertEqual(
            self.contract["runner"],
            "python -m unittest discover -s tests",
        )
        self.assertEqual(
            self.contract["categories"],
            sorted(EXPECTED_CATEGORIES),
        )

        project_runner = (ROOT / "tools" / "check_project.ps1").read_text(
            encoding="utf-8"
        )
        self.assertIn("-m unittest discover -s tests", project_runner)
        self.assertNotIn("-m pytest", project_runner)

    def test_every_canonical_package_has_complete_direct_ownership(self):
        names = [group["name"] for group in self.groups]
        self.assertEqual(names, sorted(set(names)))
        canonical_packages = sorted(
            path.name
            for path in (ROOT / "easyuse_anima").iterdir()
            if path.is_dir() and not path.name.startswith("__")
        )
        mapped_packages = sorted(
            name for name in names if name != "runtime-bootstrap"
        )
        self.assertEqual(mapped_packages, canonical_packages)
        self.assertIn("runtime-bootstrap", names)

        top_level_modules = {
            path.name
            for path in (ROOT / "easyuse_anima").glob("*.py")
        }
        mapped_top_level_modules = {
            Path(relative).name
            for group in self.groups
            for relative in group["production_paths"]
            if not relative.endswith("/")
            and Path(relative).parent.as_posix() == "easyuse_anima"
        }
        self.assertEqual(
            mapped_top_level_modules | {"__init__.py"},
            top_level_modules,
        )

        for group in self.groups:
            with self.subTest(group=group["name"]):
                self.assertEqual(
                    set(group),
                    {"name", "owners", "production_paths"},
                )
                production_paths = group["production_paths"]
                self.assertEqual(production_paths, sorted(set(production_paths)))
                self.assertTrue(production_paths)
                for relative in production_paths:
                    owner_path = ROOT / relative.rstrip("/")
                    self.assertTrue(owner_path.exists(), relative)

                owners = group["owners"]
                self.assertEqual(set(owners), EXPECTED_CATEGORIES)
                for category, entries in owners.items():
                    self.assertEqual(
                        entries,
                        sorted(set(entries)),
                        (group["name"], category),
                    )
                    self.assertTrue(entries, (group["name"], category))

                for category in (
                    "pure_service_unit",
                    "adapter_api_node_integration",
                ):
                    direct_tests = [
                        entry
                        for entry in owners[category]
                        if entry.startswith("tests/test_")
                    ]
                    self.assertTrue(direct_tests, (group["name"], category))
                    for test_path in direct_tests:
                        self.assertTrue((ROOT / test_path).is_file(), test_path)

    def test_shared_matrices_have_one_owner_and_all_references_resolve(self):
        matrix_records = self.contract["matrices"]
        matrix_names = [matrix["name"] for matrix in matrix_records]
        self.assertEqual(matrix_names, sorted(set(matrix_names)))
        referenced = set()

        for matrix in matrix_records:
            with self.subTest(matrix=matrix["name"]):
                self.assertEqual(
                    set(matrix),
                    {"category", "mode", "name", "owner", "purpose"},
                )
                self.assertIn(matrix["category"], EXPECTED_CATEGORIES)
                self.assertIn(matrix["mode"], {"manual-on-trigger", "unittest"})
                self.assertTrue((ROOT / matrix["owner"]).is_file(), matrix["owner"])
                self.assertTrue(matrix["purpose"])

        for group in self.groups:
            for category, entries in group["owners"].items():
                for entry in entries:
                    if entry.startswith("@matrix:"):
                        name = entry.removeprefix("@matrix:")
                        referenced.add(name)
                        self.assertIn(name, self.matrices)
                        self.assertEqual(self.matrices[name]["category"], category)
                    else:
                        self.assertTrue((ROOT / entry).is_file(), entry)
                        self.assertTrue(entry.startswith("tests/test_"), entry)

        self.assertEqual(referenced, set(self.matrices))

    def test_root_private_imports_remain_compatibility_owned(self):
        policy = self.contract["root_private_import_policy"]
        self.assertEqual(
            policy,
            {
                "compatibility_fixture": (
                    "tests/fixtures/python_compatibility_surface.v1.json"
                ),
                "compatibility_owner": (
                    "tests/test_python_compatibility_surface.py"
                ),
                "existing_test_reclassification": "not part of G-06A",
                "new_test_imports": (
                    "canonical owner unless explicitly testing compatibility"
                ),
            },
        )
        self.assertTrue((ROOT / policy["compatibility_fixture"]).is_file())
        self.assertEqual(
            self.matrices["root-compatibility"]["owner"],
            policy["compatibility_owner"],
        )

    def test_e09_lifecycle_integration_stays_bootstrap_runtime_owned(self):
        runtime_group = next(
            group for group in self.groups if group["name"] == "runtime-bootstrap"
        )
        self.assertEqual(
            runtime_group["owners"]["pure_service_unit"],
            ["tests/test_runtime_services.py"],
        )
        self.assertEqual(
            runtime_group["owners"]["adapter_api_node_integration"],
            ["tests/test_python_bootstrap.py"],
        )
        self.assertEqual(
            runtime_group["owners"]["migration_compatibility"],
            [
                "tests/test_python_runtime_lifecycle_contract.py",
                "tests/test_python_runtime_test_isolation_contract.py",
            ],
        )

        isolation_source = (
            ROOT / "tests" / "test_python_runtime_test_isolation_contract.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "test_current_reload_and_private_mutation_inventory_is_exact",
            isolation_source,
        )
        self.assertIn(
            "test_production_reset_and_hot_reinitialize_remain_forbidden",
            isolation_source,
        )


if __name__ == "__main__":
    unittest.main()
