from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYZER_PATH = ROOT / "tools" / "analyze_nodes_module.py"
INTERNAL_PACKAGE = ROOT / "easyuse_anima"


def load_analyzer():
    spec = importlib.util.spec_from_file_location("easyuse_anima_import_analyzer", ANALYZER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load analyzer: {ANALYZER_PATH.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


analyzer = load_analyzer()


class PythonImportBoundaryTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
