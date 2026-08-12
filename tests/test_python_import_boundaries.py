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
    ROOT / "tests" / "fixtures" / "python_import_boundary_contract.v2.json"
)
OWNER_INVENTORY_PATH = (
    ROOT / "tests" / "fixtures" / "python_test_ownership_contract.v1.json"
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

    def test_bootstrap_allows_only_the_exact_comfy_host_nodes_import(self):
        self.assertEqual(
            analyzer.find_import_boundary_violations(
                "import nodes as comfy_nodes\n",
                module_name="easyuse_anima.bootstrap",
            ),
            [],
        )
        for source in (
            "from nodes import NODE_CLASS_MAPPINGS\n",
            "import nodes.mapping\n",
        ):
            with self.subTest(source=source.strip()):
                violations = analyzer.find_import_boundary_violations(
                    source,
                    module_name="easyuse_anima.bootstrap",
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
        cls.owner_document = json.loads(
            OWNER_INVENTORY_PATH.read_text(encoding="utf-8")
        )
        cls.contract = checker.validate_contract(
            cls.contract_document,
            cls.owner_document,
        )

    def test_contract_derives_all_g06_paths_and_fixes_roles_and_overrides(self):
        owner_paths = {
            group["name"]: group["production_paths"]
            for group in self.owner_document["groups"]
        }
        contract_groups = self.contract["groups"]

        self.assertEqual(len(contract_groups), 17)
        self.assertEqual(
            {
                group["group"]: list(group["production_paths"])
                for group in contract_groups
            },
            owner_paths,
        )
        self.assertEqual(
            {
                group["group"]: group["role"]
                for group in contract_groups
            },
            {
                "aio": "feature-service",
                "api": "http-adapter",
                "autocomplete": "feature-service",
                "common": "common",
                "extensions": "common",
                "image": "feature-service",
                "infrastructure": "infrastructure-core",
                "lora": "feature-service",
                "naia": "feature-service",
                "nodes": "node-adapter",
                "profiles": "feature-service",
                "prompt": "feature-service",
                "runtime-bootstrap": "process-composition",
                "seed": "feature-service",
                "settings": "feature-service",
                "translation": "feature-service",
                "wildcard": "feature-service",
            },
        )
        self.assertEqual(
            [override["path"] for override in self.contract["path_role_overrides"]],
            [
                "easyuse_anima/api/application.py",
                "easyuse_anima/api/application_compatibility.py",
                "easyuse_anima/api/application_routes.py",
                "easyuse_anima/api/router.py",
                "easyuse_anima/extensions/aio.py",
                "easyuse_anima/infrastructure/comfy/",
                "easyuse_anima/registration.py",
                "easyuse_anima/workflow.py",
            ],
        )
        self.assertEqual(
            {
                (
                    exception["source"],
                    exception["target"],
                    exception["name"],
                )
                for exception in self.contract["edge_exceptions"]
            },
            {
                (
                    "easyuse_anima/infrastructure/comfy/wiring.py",
                    "easyuse_anima/runtime.py",
                    "get_runtime",
                ),
                (
                    "easyuse_anima/nodes/seed_adapters.py",
                    "easyuse_anima/runtime.py",
                    "get_runtime",
                ),
            },
        )

    def test_owner_matching_prefers_exact_then_longest_prefix(self):
        groups = (
            {
                "group": "broad",
                "production_paths": ("easyuse_anima/",),
            },
            {
                "group": "nested",
                "production_paths": ("easyuse_anima/settings/",),
            },
            {
                "group": "exact",
                "production_paths": ("easyuse_anima/settings/service.py",),
            },
        )

        self.assertEqual(
            checker._source_group(
                "easyuse_anima/settings/service.py",
                groups,
            )["group"],
            "exact",
        )
        self.assertEqual(
            checker._source_group(
                "easyuse_anima/settings/other.py",
                groups,
            )["group"],
            "nested",
        )

    def test_synthetic_report_rejects_all_five_universal_rules(self):
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

        violations = checker.check_report(report, self.contract)
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
        self.assertEqual(checker.check_report(report, self.contract), [])

    def test_reviewed_role_directions_and_exact_runtime_edges_are_allowed(self):
        report = analyzed(
            {
                "__init__.py": "from .easyuse_anima import bootstrap\n",
                "easyuse_anima/__init__.py": "from . import seed\n",
                "easyuse_anima/aio/__init__.py": "from . import service\n",
                "easyuse_anima/aio/service.py": (
                    "from ..common import values\n"
                    "from ..infrastructure.comfy import provider\n"
                ),
                "easyuse_anima/api/__init__.py": "",
                "easyuse_anima/api/router.py": (
                    "from .routes import endpoint\n"
                ),
                "easyuse_anima/api/routes/__init__.py": "",
                "easyuse_anima/api/routes/endpoint.py": (
                    "from ...aio import service\n"
                ),
                "easyuse_anima/bootstrap.py": (
                    "from .api.routes import endpoint\n"
                    "from . import registration, runtime\n"
                ),
                "easyuse_anima/common/__init__.py": "",
                "easyuse_anima/common/values.py": "VALUE = 1\n",
                "easyuse_anima/infrastructure/__init__.py": "",
                "easyuse_anima/infrastructure/core.py": (
                    "from ..common import values\n"
                ),
                "easyuse_anima/infrastructure/comfy/__init__.py": "",
                "easyuse_anima/infrastructure/comfy/provider.py": (
                    "from .. import core\n"
                ),
                "easyuse_anima/infrastructure/comfy/wiring.py": (
                    "from ...runtime import get_runtime\n"
                    "from . import provider\n"
                ),
                "easyuse_anima/nodes/__init__.py": "",
                "easyuse_anima/nodes/adapter.py": (
                    "from ..aio import service\n"
                ),
                "easyuse_anima/nodes/seed_adapters.py": (
                    "from ..runtime import get_runtime\n"
                ),
                "easyuse_anima/registration.py": (
                    "from .nodes import adapter\n"
                ),
                "easyuse_anima/runtime.py": "from .aio import service\n",
                "easyuse_anima/seed/__init__.py": "",
                "easyuse_anima/workflow.py": (
                    "from .common import values\n"
                    "from .nodes import adapter\n"
                ),
            }
        )

        self.assertEqual(checker.check_report(report, self.contract), [])

    def test_each_forbidden_role_direction_is_rejected(self):
        report = analyzed(
            {
                "__init__.py": "",
                "easyuse_anima/__init__.py": "",
                "easyuse_anima/aio/__init__.py": "",
                "easyuse_anima/aio/service.py": "VALUE = 1\n",
                "easyuse_anima/aio/bad.py": (
                    "from ..api.routes import view\n"
                ),
                "easyuse_anima/api/__init__.py": "",
                "easyuse_anima/api/router.py": (
                    "from ..nodes import adapter\n"
                ),
                "easyuse_anima/api/routes/__init__.py": "",
                "easyuse_anima/api/routes/view.py": "VALUE = 1\n",
                "easyuse_anima/api/routes/node_bad.py": (
                    "from ...nodes import adapter\n"
                ),
                "easyuse_anima/common/__init__.py": "",
                "easyuse_anima/common/bad.py": "from ..aio import service\n",
                "easyuse_anima/infrastructure/__init__.py": "",
                "easyuse_anima/infrastructure/bad.py": (
                    "from ..aio import service\n"
                ),
                "easyuse_anima/infrastructure/comfy/__init__.py": "",
                "easyuse_anima/infrastructure/comfy/bad.py": (
                    "from ...aio import service\n"
                ),
                "easyuse_anima/nodes/__init__.py": "",
                "easyuse_anima/nodes/adapter.py": "VALUE = 1\n",
                "easyuse_anima/nodes/api_bad.py": (
                    "from ..api.routes import view\n"
                ),
                "easyuse_anima/registration.py": (
                    "from .api.routes import view\n"
                ),
            }
        )

        violations = checker.check_report(report, self.contract)
        role_sources = {
            violation["source"]
            for violation in violations
            if violation["rule"] == "role-back-reference"
        }
        self.assertEqual(
            role_sources,
            {
                "easyuse_anima/aio/bad.py",
                "easyuse_anima/api/router.py",
                "easyuse_anima/api/routes/node_bad.py",
                "easyuse_anima/common/bad.py",
                "easyuse_anima/infrastructure/bad.py",
                "easyuse_anima/infrastructure/comfy/bad.py",
                "easyuse_anima/nodes/api_bad.py",
                "easyuse_anima/registration.py",
            },
        )

    def test_root_and_nested_package_facades_reject_cross_owner_exports(self):
        report = analyzed(
            {
                "__init__.py": "",
                "easyuse_anima/__init__.py": (
                    "from . import image, seed\n"
                ),
                "easyuse_anima/image/__init__.py": "",
                "easyuse_anima/prompt/__init__.py": (
                    "from ..settings import service\n"
                ),
                "easyuse_anima/seed/__init__.py": "",
                "easyuse_anima/settings/__init__.py": "",
                "easyuse_anima/settings/service.py": "VALUE = 1\n",
            }
        )

        violations = checker.check_report(report, self.contract)
        self.assertEqual(
            {
                (violation["source"], violation["target"])
                for violation in violations
                if violation["rule"] == "role-back-reference"
            },
            {
                (
                    "easyuse_anima/__init__.py",
                    "easyuse_anima/image/__init__.py",
                ),
                (
                    "easyuse_anima/prompt/__init__.py",
                    "easyuse_anima/settings/service.py",
                ),
            },
        )

    def test_contract_rejects_drift_and_g06_map_changes(self):
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

        changed_role = copy.deepcopy(self.contract_document)
        changed_role["groups"][0]["role"] = "unknown"
        mutations.append(changed_role)

        renamed_group = copy.deepcopy(self.contract_document)
        renamed_group["groups"][0]["group"] = "common-renamed"
        mutations.append(renamed_group)

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(checker.ContractError):
                    checker.validate_contract(mutation, self.owner_document)

        changed_owner_map = copy.deepcopy(self.owner_document)
        changed_owner_map["groups"].append(
            {
                "name": "z-new-owner",
                "owners": {},
                "production_paths": ["easyuse_anima/z_new_owner/"],
            }
        )
        with self.assertRaises(checker.ContractError):
            checker.validate_contract(
                self.contract_document,
                changed_owner_map,
            )

    def test_changed_g06_paths_immediately_change_gate_coverage(self):
        changed_owner_map = copy.deepcopy(self.owner_document)
        changed_owner_map["groups"][0]["production_paths"] = [
            "easyuse_anima/aio_v2/"
        ]
        contract = checker.validate_contract(
            self.contract_document,
            changed_owner_map,
        )
        report = analyzed(
            {
                "__init__.py": "",
                "easyuse_anima/__init__.py": "",
                "easyuse_anima/aio/__init__.py": "",
                "easyuse_anima/aio/service.py": "VALUE = 1\n",
            }
        )

        violations = checker.check_report(
            report,
            contract,
            require_complete_owner_map=True,
        )
        self.assertIn(
            (
                "easyuse_anima/aio/service.py",
                "unowned-production-path",
            ),
            {
                (violation["source"], violation["rule"])
                for violation in violations
            },
        )
        self.assertIn(
            ("easyuse_anima/aio_v2/", "owner-path-empty"),
            {
                (violation["source"], violation["rule"])
                for violation in violations
            },
        )

    def test_current_repository_has_complete_g06_coverage_and_zero_violations(self):
        self.assertEqual(checker.check_repository(ROOT, CONTRACT_PATH), [])

    def test_unowned_path_and_formerly_unenrolled_prompt_debt_block_the_gate(self):
        report = analyzed(
            {
                "__init__.py": "from .easyuse_anima.prompt import debt\n",
                "nodes.py": "VALUE = 1\n",
                "easyuse_anima/__init__.py": "",
                "easyuse_anima/prompt/__init__.py": "",
                "easyuse_anima/prompt/debt.py": "import nodes\n",
                "easyuse_anima/unowned.py": "VALUE = 1\n",
            }
        )

        violations = checker.check_report(report, self.contract)
        self.assertIn(
            (
                "easyuse_anima/prompt/debt.py",
                "canonical-imports-root",
            ),
            {
                (violation["source"], violation["rule"])
                for violation in violations
            },
        )
        self.assertIn(
            (
                "easyuse_anima/unowned.py",
                "unowned-production-path",
            ),
            {
                (violation["source"], violation["rule"])
                for violation in violations
            },
        )

    def test_quality_runner_invokes_the_checker_once_for_quick_and_full(self):
        source = (ROOT / "tools" / "check_python_quality.ps1").read_text(
            encoding="utf-8"
        )
        invocation = '(Join-Path $PSScriptRoot "check_python_import_boundaries.py")'

        self.assertEqual(source.count(invocation), 1)
        self.assertIn("Python import boundary gate failed", source)


if __name__ == "__main__":
    unittest.main()
