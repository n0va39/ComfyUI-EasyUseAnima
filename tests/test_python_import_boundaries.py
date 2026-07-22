from __future__ import annotations

import ast
import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYZER_PATH = ROOT / "tools" / "analyze_nodes_module.py"
INTERNAL_PACKAGE = ROOT / "easyuse_anima"
REGISTRATION_PATH = INTERNAL_PACKAGE / "registration.py"
CHECKER_PATH = ROOT / "tools" / "check_python_import_boundaries.py"
CONTRACT_PATH = (
    ROOT / "tests" / "fixtures" / "python_import_boundary_contract.v1.json"
)


def load_analyzer():
    spec = importlib.util.spec_from_file_location("easyuse_anima_import_analyzer", ANALYZER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load analyzer: {ANALYZER_PATH.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_checker():
    spec = importlib.util.spec_from_file_location(
        "easyuse_anima_import_boundary_checker",
        CHECKER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load checker: {CHECKER_PATH.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


analyzer = load_analyzer()
checker = load_checker()


def analyzed(sources: dict[str, str]):
    return checker.analyzer.analyze_source_set(sources)


def synthetic_root(*module_imports: str) -> str:
    return "\n".join(module_imports) + "\n"


class PythonImportBoundarySeedTests(unittest.TestCase):
    def test_registration_is_pure_literal_mapping_composition(self):
        source = REGISTRATION_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=REGISTRATION_PATH.name)

        self.assertEqual(
            analyzer.find_import_boundary_violations(
                source,
                module_name="easyuse_anima.registration",
            ),
            [],
        )
        self.assertEqual(
            [node for node in ast.walk(tree) if isinstance(node, ast.Call)],
            [],
        )
        imports = [node for node in tree.body if isinstance(node, ast.ImportFrom)]
        self.assertTrue(imports)
        self.assertTrue(
            all(
                node.level == 1
                and node.module is not None
                and node.module.startswith("nodes.")
                for node in imports
            )
        )
        assignments = {
            target.id: statement.value
            for statement in tree.body
            if isinstance(statement, ast.Assign)
            for target in statement.targets
            if isinstance(target, ast.Name)
        }
        self.assertEqual(
            set(assignments),
            {"NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "__all__"},
        )
        self.assertIsInstance(assignments["NODE_CLASS_MAPPINGS"], ast.Dict)
        self.assertIsInstance(assignments["NODE_DISPLAY_NAME_MAPPINGS"], ast.Dict)
        self.assertIsInstance(assignments["__all__"], ast.List)

    def test_future_internal_package_never_imports_root_nodes(self):
        violations = analyzer.scan_internal_package(INTERNAL_PACKAGE)

        self.assertFalse(
            [
                violation
                for violation in violations
                if violation["rule"] == "internal-imports-root-nodes"
            ]
        )

    def test_future_inner_layers_never_import_outer_layers(self):
        violations = analyzer.scan_internal_package(INTERNAL_PACKAGE)

        self.assertFalse(
            [
                violation
                for violation in violations
                if violation["rule"] == "inner-layer-imports-outer-layer"
            ]
        )

    def test_comfy_infrastructure_does_not_back_reference_feature_schema(self):
        comfy_root = INTERNAL_PACKAGE / "infrastructure" / "comfy"
        for path in sorted(comfy_root.glob("*.py")):
            source = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertNotIn("ANIMA_", source)
                self.assertNotIn("from nodes", source)
                self.assertNotIn("import nodes", source)

    def test_profile_contract_has_no_http_storage_or_outer_layer_imports(self):
        contract_path = INTERNAL_PACKAGE / "profiles" / "contract.py"
        source = contract_path.read_text(encoding="utf-8")
        violations = analyzer.find_import_boundary_violations(
            source,
            module_name="easyuse_anima.profiles.contract",
        )
        tree = ast.parse(source)
        imported_roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(
                    alias.name.split(".", 1)[0]
                    for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".", 1)[0])

        self.assertEqual(violations, [])
        self.assertTrue(
            imported_roots.isdisjoint(
                {
                    "aiohttp",
                    "api_contract",
                    "folder_paths",
                    "server",
                    "storage",
                }
            )
        )
        self.assertNotIn("AtomicJsonStore", source)

    def test_synthetic_allowed_imports_have_no_violations(self):
        sources = {
            "easyuse_anima.domain.models": "from easyuse_anima.domain import values\n",
            "easyuse_anima.services.prompt": "from easyuse_anima.domain import models\n",
            "easyuse_anima.adapters.comfy": "from easyuse_anima.services import prompt\n",
            "easyuse_anima.registration": "from easyuse_anima.adapters import comfy\n",
        }

        for module_name, source in sources.items():
            with self.subTest(module=module_name):
                self.assertEqual(
                    analyzer.find_import_boundary_violations(source, module_name=module_name),
                    [],
                )

    def test_synthetic_internal_import_of_root_nodes_is_rejected(self):
        sources = (
            "import nodes\n",
            "import nodes as root_nodes\n",
            "from nodes import NODE_CLASS_MAPPINGS\n",
            "import importlib\nimportlib.import_module('nodes')\n",
        )

        for source in sources:
            with self.subTest(source=source.strip()):
                violations = analyzer.find_import_boundary_violations(
                    source,
                    module_name="easyuse_anima.services.prompt",
                )
                self.assertIn(
                    "internal-imports-root-nodes",
                    {violation["rule"] for violation in violations},
                )

    def test_literal_dynamic_import_aliases_are_rejected(self):
        sources = (
            "import importlib as il\nil.import_module('nodes')\n",
            "from importlib import import_module as load\nload('nodes')\n",
        )

        for source in sources:
            with self.subTest(source=source.strip()):
                violations = analyzer.find_import_boundary_violations(
                    source,
                    module_name="easyuse_anima.prompt.service",
                )
                self.assertIn(
                    "internal-imports-root-nodes",
                    {violation["rule"] for violation in violations},
                )

    def test_vertical_service_static_import_alias_is_rejected(self):
        sources = (
            "from .. import registration as reg\n",
            (
                "import importlib as il\n"
                "il.import_module('..registration', __package__)\n"
            ),
        )

        for source in sources:
            with self.subTest(source=source.strip()):
                violations = analyzer.find_import_boundary_violations(
                    source,
                    module_name="easyuse_anima.prompt.service",
                )
                self.assertIn(
                    "inner-layer-imports-outer-layer",
                    {violation["rule"] for violation in violations},
                )

    def test_synthetic_inner_to_outer_back_references_are_rejected(self):
        sources = {
            "easyuse_anima.domain.models": (
                "from easyuse_anima.adapters import comfy\n"
            ),
            "easyuse_anima.services.prompt": (
                "from ..registration import register_nodes\n"
            ),
            "easyuse_anima.service.catalog": (
                "import easyuse_anima.bootstrap.runtime\n"
            ),
            "easyuse_anima.prompt.service": (
                "from easyuse_anima import registration\n"
            ),
            "easyuse_anima.prompt.domain.model": (
                "from easyuse_anima.api import routes\n"
            ),
            "easyuse_anima.regional.services.layout": (
                "from easyuse_anima import nodes\n"
            ),
        }

        for module_name, source in sources.items():
            with self.subTest(module=module_name):
                violations = analyzer.find_import_boundary_violations(
                    source,
                    module_name=module_name,
                )
                self.assertIn(
                    "inner-layer-imports-outer-layer",
                    {violation["rule"] for violation in violations},
                )


class CompletedPackageImportBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract_document = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.groups = checker.validate_contract(cls.contract_document)

    def test_synthetic_report_rejects_all_five_boundary_rules(self):
        report = analyzed(
            {
                "__init__.py": synthetic_root(
                    "from .easyuse_anima.common import root_ref",
                    "from .easyuse_anima.image import backref",
                    "from .easyuse_anima.lora import cycle_a",
                    "from .easyuse_anima.naia import fallback",
                    "from .easyuse_anima.profiles import registration",
                ),
                "nodes.py": "VALUE = 1\n",
                "easyuse_anima/__init__.py": "",
                "easyuse_anima/common/__init__.py": "",
                "easyuse_anima/common/root_ref.py": "import nodes\n",
                "easyuse_anima/image/__init__.py": "",
                "easyuse_anima/image/backref.py": (
                    "from ..nodes import image_nodes\n"
                ),
                "easyuse_anima/nodes/__init__.py": "",
                "easyuse_anima/nodes/image_nodes.py": "VALUE = 1\n",
                "easyuse_anima/lora/__init__.py": "",
                "easyuse_anima/lora/cycle_a.py": (
                    "import easyuse_anima.lora.cycle_b\n"
                ),
                "easyuse_anima/lora/cycle_b.py": "from . import cycle_a\n",
                "easyuse_anima/naia/__init__.py": "",
                "easyuse_anima/naia/dep.py": "VALUE = 1\n",
                "easyuse_anima/naia/fallback.py": (
                    "try:\n"
                    "    from .dep import VALUE\n"
                    "except ImportError:\n"
                    "    from easyuse_anima.naia.dep import VALUE\n"
                ),
                "easyuse_anima/profiles/__init__.py": "",
                "easyuse_anima/profiles/registration.py": (
                    "NODE_CLASS_MAPPINGS = {}\n"
                    "NODE_CLASS_MAPPINGS.update({})\n"
                    "REGISTRY = {}\n"
                    "REGISTRY.update({})\n"
                    "MAPPINGS = {}\n"
                    "MAPPINGS.update({})\n"
                ),
            }
        )

        root_edge = next(
            edge
            for edge in report["imports"]["edges"]
            if edge["source"] == "easyuse_anima/common/root_ref.py"
        )
        self.assertEqual(root_edge["classification"], "external")
        self.assertNotIn("target", root_edge)

        violations = checker.check_report(report, self.groups)
        self.assertEqual(
            {violation["rule"] for violation in violations},
            {
                "canonical-imports-root",
                "compatibility-fallback",
                "cyclic-runtime-scc",
                "registration-side-effect",
                "role-back-reference",
            },
        )
        self.assertTrue(
            all(violation["source"] and violation["target"] for violation in violations)
        )
        registration_targets = {
            violation["target"]
            for violation in violations
            if violation["rule"] == "registration-side-effect"
        }
        self.assertTrue(
            {
                "MAPPINGS.update",
                "NODE_CLASS_MAPPINGS.update",
                "REGISTRY.update",
            }.issubset(registration_targets)
        )

    def test_external_target_none_and_optional_external_imports_are_allowed(self):
        report = analyzed(
            {
                "__init__.py": "from .easyuse_anima.image import optional\n",
                "easyuse_anima/__init__.py": "",
                "easyuse_anima/image/__init__.py": "",
                "easyuse_anima/image/optional.py": (
                    "import json\n"
                    "try:\n"
                    "    import optional_runtime\n"
                    "except ImportError:\n"
                    "    optional_runtime = None\n"
                ),
            }
        )

        external_edges = [
            edge
            for edge in report["imports"]["edges"]
            if edge["source"] == "easyuse_anima/image/optional.py"
        ]
        self.assertTrue(external_edges)
        self.assertTrue(all("target" not in edge for edge in external_edges))
        self.assertEqual(checker.check_report(report, self.groups), [])

    def test_contract_rejects_missing_duplicate_unsorted_empty_and_changed_groups(self):
        mutations = []

        missing = copy.deepcopy(self.contract_document)
        missing["groups"].pop()
        mutations.append(missing)

        duplicate = copy.deepcopy(self.contract_document)
        duplicate["groups"].insert(1, copy.deepcopy(duplicate["groups"][0]))
        mutations.append(duplicate)

        unsorted = copy.deepcopy(self.contract_document)
        unsorted["groups"].reverse()
        mutations.append(unsorted)

        empty_prefix = copy.deepcopy(self.contract_document)
        empty_prefix["groups"][0]["prefix"] = ""
        mutations.append(empty_prefix)

        changed_owner = copy.deepcopy(self.contract_document)
        changed_owner["groups"][0]["owner_issue"] = 188
        mutations.append(changed_owner)

        changed_role = copy.deepcopy(self.contract_document)
        changed_role["groups"][1]["role"] = "common"
        mutations.append(changed_role)

        renamed_group = copy.deepcopy(self.contract_document)
        renamed_group["groups"][0]["group"] = "common-renamed"
        mutations.append(renamed_group)

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(checker.ContractError):
                    checker.validate_contract(mutation)

    def test_current_repository_has_zero_enrolled_violations(self):
        self.assertEqual(checker.check_repository(ROOT, CONTRACT_PATH), [])

    def test_unenrolled_legacy_debt_does_not_block_the_gate(self):
        report = analyzed(
            {
                "__init__.py": "from .easyuse_anima.prompt import debt\n",
                "nodes.py": "VALUE = 1\n",
                "easyuse_anima/__init__.py": "",
                "easyuse_anima/prompt/__init__.py": "",
                "easyuse_anima/prompt/debt.py": "import nodes\n",
            }
        )

        self.assertEqual(checker.check_report(report, self.groups), [])

    def test_quality_runner_invokes_the_checker_once_for_quick_and_full(self):
        source = (ROOT / "tools" / "check_python_quality.ps1").read_text(
            encoding="utf-8"
        )
        invocation = '(Join-Path $PSScriptRoot "check_python_import_boundaries.py")'

        self.assertEqual(source.count(invocation), 1)
        self.assertIn("Python import boundary gate failed", source)


if __name__ == "__main__":
    unittest.main()
