from __future__ import annotations

import ast
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYZER_PATH = ROOT / "tools" / "analyze_python_backend.py"
BASELINE_PATH = ROOT / "tests" / "fixtures" / "python_backend_baseline.json"


def load_analyzer():
    spec = importlib.util.spec_from_file_location(
        "easyuse_anima_python_backend_analyzer",
        ANALYZER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load analyzer: {ANALYZER_PATH.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


analyzer = load_analyzer()


def import_edges(report, *, source="__init__.py"):
    return [edge for edge in report["imports"]["edges"] if edge["source"] == source]


class PythonBackendAnalyzerTests(unittest.TestCase):
    def test_fixture_generation_twice_is_byte_identical(self):
        first = analyzer.render_json(analyzer.analyze_repository(ROOT)).encode("utf-8")
        second = analyzer.render_json(analyzer.analyze_repository(ROOT)).encode("utf-8")

        self.assertEqual(first, second)

    def test_crlf_and_lf_sources_have_identical_reports(self):
        lf_sources = {
            "__init__.py": b"from .runtime import VALUE\nRESULT = build(VALUE)\n",
            "runtime.py": b"VALUE = []\n",
        }
        crlf_sources = {
            path: source.replace(b"\n", b"\r\n")
            for path, source in lf_sources.items()
        }

        lf_report = analyzer.analyze_source_set(lf_sources, comfyignore=b"tests/\n")
        crlf_report = analyzer.analyze_source_set(crlf_sources, comfyignore=b"tests/\r\n")

        self.assertEqual(lf_report, crlf_report)

    def test_alias_static_relative_and_literal_dynamic_import_edges(self):
        sources = {
            "__init__.py": """\
from . import alias_target as aliased
from .pkg import helper as helper_alias
import importlib as il
from importlib import import_module as load

first = il.import_module(".literal", __package__)
second = load("external.plugin")
""",
            "alias_target.py": "VALUE = 1\n",
            "literal.py": "VALUE = 2\n",
            "pkg/__init__.py": "from .helper import VALUE\n",
            "pkg/helper.py": "VALUE = 3\n",
        }

        report = analyzer.analyze_source_set(sources)
        edges = import_edges(report)
        edge_keys = {
            (
                edge["kind"],
                edge["imported"],
                edge["classification"],
                edge.get("target"),
                edge["alias"],
            )
            for edge in edges
        }

        self.assertIn(
            ("static_from", ".:alias_target", "internal", "alias_target.py", "aliased"),
            edge_keys,
        )
        self.assertIn(
            ("static_from", ".pkg:helper", "internal", "pkg/helper.py", "helper_alias"),
            edge_keys,
        )
        self.assertIn(
            ("literal_dynamic", ".literal", "internal", "literal.py", None),
            edge_keys,
        )
        self.assertIn(
            ("literal_dynamic", "external.plugin", "external", None, None),
            edge_keys,
        )

    def test_scc_ordering_is_stable(self):
        sources = {
            "__init__.py": "from . import a\n",
            "a.py": "from . import b\n",
            "b.py": "from . import c\n",
            "c.py": "from . import a\n",
            "z.py": "VALUE = 1\n",
        }

        first = analyzer.analyze_source_set(sources)
        second = analyzer.analyze_source_set(dict(reversed(list(sources.items()))))

        self.assertEqual(first["imports"]["sccs"], second["imports"]["sccs"])
        self.assertIn(
            {"modules": ["a.py", "b.py", "c.py"], "cyclic": True},
            first["imports"]["sccs"],
        )

    def test_mutable_globals_and_state_owner_candidates_are_classified(self):
        sources = {
            "__init__.py": """\
import threading
from concurrent.futures import Future, ThreadPoolExecutor

CACHE = {}
VALUES = []
SEEN = set()
LOCK = threading.RLock()
INFLIGHT: dict[str, Future] = {}
EXECUTOR = ThreadPoolExecutor()
CLIENT = ApiClient()
""",
        }

        report = analyzer.analyze_source_set(sources)
        mutable = {
            (item["name"], item["kind"])
            for item in report["state"]["mutable_globals"]
        }
        owners = {
            item["name"]: set(item["categories"])
            for item in report["state"]["owner_candidates"]
        }

        self.assertEqual(
            mutable,
            {
                ("CACHE", "dict"),
                ("INFLIGHT", "dict"),
                ("SEEN", "set"),
                ("VALUES", "list"),
            },
        )
        self.assertIn("cache", owners["CACHE"])
        self.assertIn("lock", owners["LOCK"])
        self.assertIn("future", owners["INFLIGHT"])
        self.assertIn("single_flight", owners["INFLIGHT"])
        self.assertIn("executor", owners["EXECUTOR"])
        self.assertIn("client", owners["CLIENT"])

    def test_import_time_side_effect_candidates_exclude_function_bodies(self):
        sources = {
            "__init__.py": """\
routes = build_routes()
ROOT.mkdir(parents=True)

@routes.get("/inventory")
def inventory_route():
    hidden_client = ApiClient()
    HIDDEN.mkdir()
    return hidden_client

def lazy_operation():
    return requests.get("https://example.invalid")
""",
        }

        report = analyzer.analyze_source_set(sources)
        candidates = report["side_effects"]["candidates"]
        by_callee = {item["callee"]: item["kind"] for item in candidates}

        self.assertEqual(by_callee["build_routes"], "route_registry_creation")
        self.assertEqual(by_callee["ROOT.mkdir"], "directory_creation")
        self.assertEqual(by_callee["routes.get"], "route_registration")
        self.assertNotIn("ApiClient", by_callee)
        self.assertNotIn("HIDDEN.mkdir", by_callee)
        self.assertNotIn("requests.get", by_callee)

    def test_registry_closure_separates_shipped_missing_external_and_optional(self):
        sources = {
            "__init__.py": """\
from .runtime import run
from .missing import unavailable
try:
    import optional_dependency
except ImportError:
    optional_dependency = None
""",
            "runtime.py": "def run():\n    return 1\n",
            "tests/test_runtime.py": "import runtime\n",
            "tools/dev_helper.py": "import runtime\n",
        }

        report = analyzer.analyze_source_set(
            sources,
            comfyignore="tests/\ntools/\n",
        )
        registry = report["registry"]

        self.assertEqual(
            registry["shipped_python_modules"],
            ["__init__.py", "runtime.py"],
        )
        self.assertEqual(
            registry["runtime_import_closure"],
            ["__init__.py", "runtime.py"],
        )
        self.assertEqual(len(registry["missing_internal_imports"]), 1)
        self.assertEqual(
            registry["missing_internal_imports"][0]["imported"],
            ".missing:unavailable",
        )
        self.assertIn(
            "optional_dependency",
            {item["imported"] for item in registry["external_imports"]},
        )
        self.assertEqual(
            [item["imported"] for item in registry["optional_imports"]],
            ["optional_dependency"],
        )

    def test_analyzer_source_has_no_production_import_or_execution_escape_hatch(self):
        tree = ast.parse(ANALYZER_PATH.read_text(encoding="utf-8"))
        imported_roots = set()
        call_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".", 1)[0])
            elif isinstance(node, ast.Call):
                call_names.add(analyzer._call_name(node.func))

        self.assertTrue(
            imported_roots.isdisjoint(
                {
                    "api",
                    "autocomplete_dataset",
                    "nodes",
                    "prompt_translation",
                    "settings",
                    "storage",
                    "wildcard_engine",
                    "requests",
                    "socket",
                    "subprocess",
                    "urllib",
                }
            )
        )
        self.assertTrue(
            call_names.isdisjoint(
                {
                    "__import__",
                    "eval",
                    "exec",
                    "os.system",
                    "subprocess.Popen",
                    "subprocess.run",
                }
            )
        )

    def test_current_repository_fixture_matches_and_uses_real_runtime_surface(self):
        report = analyzer.analyze_repository(ROOT)
        expected_text = BASELINE_PATH.read_text(encoding="utf-8")

        self.assertEqual(analyzer.render_json(report), expected_text)
        self.assertGreaterEqual(report["inventory"]["module_count"], 10)
        self.assertIn("nodes.py", report["registry"]["shipped_python_modules"])
        self.assertIn("api.py", report["registry"]["runtime_import_closure"])
        self.assertNotIn(
            "tests/test_python_backend_analyzer.py",
            report["registry"]["shipped_python_modules"],
        )
        self.assertNotIn(
            "tools/analyze_python_backend.py",
            report["registry"]["shipped_python_modules"],
        )
        json.loads(expected_text)

    def test_human_render_has_module_edge_and_state_review_sections(self):
        report = analyzer.analyze_source_set(
            {
                "__init__.py": "from .runtime import VALUE\nCACHE = {}\n",
                "runtime.py": "VALUE = 1\n",
            }
        )

        rendered = analyzer.render_text(report)

        self.assertIn("[modules]\n", rendered)
        self.assertIn("[edges]\n", rendered)
        self.assertIn("[state.mutable_globals]\n", rendered)
        self.assertIn("[state.owner_candidates]\n", rendered)


if __name__ == "__main__":
    unittest.main()
