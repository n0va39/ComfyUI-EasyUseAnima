from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
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


def git_paths(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
    )
    return {line for line in result.stdout.splitlines() if line}


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

    def test_literal_dynamic_aliases_do_not_leak_between_lexical_scopes(self):
        sources = {
            "__init__.py": """\
from importlib import import_module as module_load

def dynamic_loader():
    from importlib import import_module as load
    return load(".plugin", __package__)

def parameter_loader(load):
    return load("not.a.dynamic.import")

def assigned_loader():
    load = user_loader
    return load("also.not.dynamic")

def lexical_late_shadow():
    value = module_load("still.not.dynamic")
    module_load = user_loader
    return value
""",
            "plugin.py": "VALUE = 1\n",
        }

        report = analyzer.analyze_source_set(sources)
        dynamic_edges = [
            edge
            for edge in report["imports"]["edges"]
            if edge["kind"] == "literal_dynamic"
        ]

        self.assertEqual(
            [(edge["scope"], edge["imported"], edge.get("target")) for edge in dynamic_edges],
            [("dynamic_loader", ".plugin", "plugin.py")],
        )

    def test_lambda_arguments_shadow_aliases_but_defaults_use_outer_scope(self):
        sources = {
            "__init__.py": """\
from importlib import import_module as load
module_value = load(".plugin", __package__)
posonly = lambda load, /: load("not.posonly")
regular = lambda load: load("not.regular")
kwonly = lambda *, load: load("not.kwonly")
vararg = lambda *load: load("not.vararg")
kwarg = lambda **load: load("not.kwarg")
defaulted = lambda value=load(".plugin", __package__): value
closure = lambda: load(".plugin", __package__)
""",
            "plugin.py": "VALUE = 1\n",
        }

        report = analyzer.analyze_source_set(sources)
        dynamic_edges = [
            edge
            for edge in report["imports"]["edges"]
            if edge["kind"] == "literal_dynamic"
        ]

        self.assertEqual(
            [(edge["scope"], edge["imported"]) for edge in dynamic_edges],
            [
                ("<module>", ".plugin"),
                ("<module>", ".plugin"),
                ("<lambda>@9", ".plugin"),
            ],
        )

    def test_method_lookup_skips_class_alias_scope_but_definitions_use_it(self):
        sources = {
            "__init__.py": """\
from importlib import import_module as load

class UsesModuleAlias:
    load = custom_loader

    def method(self):
        return load(".plugin", __package__)

class UsesClassAlias:
    from importlib import import_module as class_load
    class_value = class_load(".class_body", __package__)

    def method(
        self,
        value: class_load(".annotation", __package__) = class_load(".default", __package__),
    ):
        return class_load("not.a.dynamic.import")
""",
            "annotation.py": "VALUE = 1\n",
            "class_body.py": "VALUE = 1\n",
            "default.py": "VALUE = 1\n",
            "plugin.py": "VALUE = 1\n",
        }

        report = analyzer.analyze_source_set(sources)
        dynamic_edges = [
            edge
            for edge in report["imports"]["edges"]
            if edge["kind"] == "literal_dynamic"
        ]

        self.assertEqual(
            {(edge["scope"], edge["imported"]) for edge in dynamic_edges},
            {
                ("UsesClassAlias", ".annotation"),
                ("UsesClassAlias", ".class_body"),
                ("UsesClassAlias", ".default"),
                ("UsesModuleAlias.method", ".plugin"),
            },
        )

    def test_try_branch_context_and_compatibility_fallback_taxonomy(self):
        sources = {
            "__init__.py": """\
try:
    from .runtime import VALUE
except ImportError:
    from runtime import VALUE

try:
    import optional_dependency
except ImportError:
    optional_dependency = None
else:
    import else_dependency
finally:
    import final_dependency
""",
            "runtime.py": "VALUE = 1\n",
            "nodes.py": """\
def comfy_runtime():
    try:
        import nodes as comfy_nodes
    except Exception:
        return None
    return comfy_nodes
""",
        }

        report = analyzer.analyze_source_set(sources)
        root_edges = import_edges(report)
        primary = next(edge for edge in root_edges if edge["imported"] == ".runtime:VALUE")
        fallback = next(edge for edge in root_edges if edge["imported"] == "runtime:VALUE")
        optional = next(edge for edge in root_edges if edge["imported"] == "optional_dependency")
        else_edge = next(edge for edge in root_edges if edge["imported"] == "else_dependency")
        finally_edge = next(edge for edge in root_edges if edge["imported"] == "final_dependency")
        comfy_nodes = next(
            edge
            for edge in import_edges(report, source="nodes.py")
            if edge["imported"] == "nodes"
        )

        self.assertEqual(primary["classification"], "internal")
        self.assertEqual(primary["role"], "compatibility_primary")
        self.assertFalse(primary["optional"])
        self.assertEqual(primary["branch_context"][-1]["branch"], "body")
        self.assertEqual(fallback["classification"], "compatibility_fallback")
        self.assertEqual(fallback["target"], "runtime.py")
        self.assertEqual(fallback["role"], "compatibility_fallback")
        self.assertTrue(fallback["conditional"])
        self.assertFalse(fallback["optional"])
        self.assertEqual(fallback["branch_context"][-1]["branch"], "except")
        self.assertEqual(
            fallback["branch_context"][-1]["exceptions"],
            ["ImportError"],
        )
        self.assertEqual(optional["role"], "optional_dependency")
        self.assertTrue(optional["optional"])
        self.assertEqual(else_edge["branch_context"][-1]["branch"], "else")
        self.assertEqual(finally_edge["branch_context"][-1]["branch"], "finally")
        self.assertEqual(comfy_nodes["classification"], "external")
        self.assertNotEqual(comfy_nodes["role"], "compatibility_fallback")
        self.assertEqual(
            report["imports"]["module_graph"],
            [{"from": "__init__.py", "to": "runtime.py"}],
        )
        self.assertEqual(
            report["imports"]["module_graph_policy"]["duplicate_policy"],
            "collapse by source and target path",
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

    def test_module_control_flow_mutables_and_extended_constructors_are_stable(self):
        lf_source = """\
from collections import OrderedDict, defaultdict, deque

if ENABLED:
    IF_CACHE = {}
try:
    TRY_VALUES = []
except Exception:
    FALLBACK_SET = set()
with manager():
    WITH_CACHE = OrderedDict()
match mode:
    case "queue":
        MATCH_QUEUE = deque()
    case _:
        MATCH_MAP = defaultdict(list)

def ignored_function():
    LOCAL_CACHE = {}

class IgnoredClass:
    CLASS_CACHE = {}
"""
        lf_report = analyzer.analyze_source_set({"__init__.py": lf_source})
        crlf_report = analyzer.analyze_source_set(
            {"__init__.py": lf_source.replace("\n", "\r\n")}
        )
        mutable = [
            (item["name"], item["line"], item["kind"])
            for item in lf_report["state"]["mutable_globals"]
        ]

        self.assertEqual(lf_report, crlf_report)
        self.assertEqual(
            mutable,
            [
                ("FALLBACK_SET", 8, "set"),
                ("IF_CACHE", 4, "dict"),
                ("MATCH_MAP", 15, "dict"),
                ("MATCH_QUEUE", 13, "list"),
                ("TRY_VALUES", 6, "list"),
                ("WITH_CACHE", 10, "dict"),
            ],
        )
        self.assertNotIn("LOCAL_CACHE", {item[0] for item in mutable})
        self.assertNotIn("CLASS_CACHE", {item[0] for item in mutable})

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

    def test_type_checking_edges_are_preserved_but_excluded_from_runtime_views(self):
        sources = {
            "__init__.py": """\
from typing import TYPE_CHECKING
from .runtime import VALUE

if TYPE_CHECKING:
    from .typing_only import T
    from .missing_type import M
""",
            "runtime.py": "VALUE = 1\n",
            "typing_only.py": "T = object\n",
        }

        report = analyzer.analyze_source_set(sources)
        reversed_report = analyzer.analyze_source_set(
            dict(reversed(list(sources.items())))
        )
        type_edges = {
            edge["imported"]: edge
            for edge in import_edges(report)
            if edge["imported"] in {".typing_only:T", ".missing_type:M"}
        }

        self.assertEqual(report, reversed_report)
        self.assertEqual(set(type_edges), {".typing_only:T", ".missing_type:M"})
        for edge in type_edges.values():
            self.assertTrue(edge["conditional"])
            self.assertTrue(edge["optional"])
            self.assertEqual(
                edge["branch_context"][-1],
                {
                    "kind": "if",
                    "line": 4,
                    "branch": "body",
                    "type_checking": True,
                },
            )
        self.assertEqual(type_edges[".typing_only:T"]["classification"], "internal")
        self.assertEqual(type_edges[".typing_only:T"]["target"], "typing_only.py")
        self.assertEqual(
            type_edges[".missing_type:M"]["classification"],
            "missing_internal",
        )

        registry = report["registry"]
        self.assertEqual(
            report["imports"]["module_graph"],
            [{"from": "__init__.py", "to": "runtime.py"}],
        )
        self.assertEqual(
            registry["runtime_import_closure"],
            ["__init__.py", "runtime.py"],
        )
        self.assertEqual(
            registry["unreachable_shipped_python_modules"],
            ["typing_only.py"],
        )
        self.assertEqual(registry["missing_internal_imports"], [])
        self.assertFalse(
            {".typing_only:T", ".missing_type:M"}
            & {item["imported"] for item in registry["optional_imports"]}
        )
        self.assertNotIn(
            "typing_only.py",
            {
                module
                for component in report["imports"]["sccs"]
                for module in component["modules"]
            },
        )
        self.assertTrue(
            {"T", "M"}.isdisjoint(report["public_surface"]["compatibility_names"])
        )
        self.assertEqual(
            report["imports"]["module_graph_policy"]["excluded_branch_contexts"],
            [{"kind": "if", "branch": "body", "type_checking": True}],
        )

    def test_comfyignore_anchoring_slashes_negation_and_escaped_markers(self):
        sources = {
            "__init__.py": "VALUE = 1\n",
            "autocomplete/root.py": "VALUE = 1\n",
            "nested/autocomplete/keep.py": "VALUE = 1\n",
            "web_version/dev/root.py": "VALUE = 1\n",
            "nested/web_version/dev/keep.py": "VALUE = 1\n",
            "#literal.py": "VALUE = 1\n",
            "!literal.py": "VALUE = 1\n",
            "drop.tmp.py": "VALUE = 1\n",
            "keep.tmp.py": "VALUE = 1\n",
            "nested/direct.py": "VALUE = 1\n",
            "nested/deeper/direct.py": "VALUE = 1\n",
            "ignored/keep.py": "VALUE = 1\n",
        }
        ignore = r"""\
/autocomplete/
web_version/dev/
\#literal.py
\!literal.py
*.tmp.py
!keep.tmp.py
nested/*.py
ignored/
!ignored/keep.py
"""

        report = analyzer.analyze_source_set(sources, comfyignore=ignore)

        self.assertEqual(
            report["registry"]["shipped_python_modules"],
            [
                "__init__.py",
                "keep.tmp.py",
                "nested/autocomplete/keep.py",
                "nested/deeper/direct.py",
                "nested/web_version/dev/keep.py",
            ],
        )

    def test_current_registry_python_surface_matches_git_exclude_contract(self):
        report = analyzer.analyze_repository(ROOT)
        tracked = git_paths("ls-files", "--cached")
        ignored = git_paths(
            "ls-files",
            "--cached",
            "--ignored",
            "--exclude-from=.comfyignore",
        )
        expected = sorted(
            path
            for path in tracked - ignored
            if path.endswith(".py")
        )

        self.assertEqual(report["registry"]["shipped_python_modules"], expected)

    def test_analyzer_source_has_no_production_import_or_execution_escape_hatch(self):
        tree = ast.parse(ANALYZER_PATH.read_text(encoding="utf-8"))
        imported_roots = set()
        aliases = {}
        call_nodes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_roots.add(alias.name.split(".", 1)[0])
                    aliases[alias.asname or alias.name.split(".", 1)[0]] = alias.name
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".", 1)[0])
                for alias in node.names:
                    aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"
            elif isinstance(node, ast.Call):
                call_nodes.append(node)

        resolved_call_names = set()
        for node in call_nodes:
            callee = analyzer._call_name(node.func)
            root, separator, suffix = callee.partition(".")
            target = aliases.get(root)
            resolved_call_names.add(
                f"{target}.{suffix}" if target and separator else target or callee
            )

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
                    "importlib",
                    "requests",
                    "runpy",
                    "socket",
                    "subprocess",
                    "urllib",
                }
            )
        )
        self.assertTrue(
            resolved_call_names.isdisjoint(
                {
                    "__import__",
                    "builtins.eval",
                    "builtins.exec",
                    "eval",
                    "exec",
                    "importlib.import_module",
                    "os.system",
                    "runpy.run_module",
                    "runpy.run_path",
                    "subprocess.Popen",
                    "subprocess.run",
                }
            )
        )
        self.assertFalse(
            [name for name in resolved_call_names if name.startswith("subprocess.")]
        )

    def test_current_repository_fixture_matches_and_uses_real_runtime_surface(self):
        report = analyzer.analyze_repository(ROOT)
        expected_text = BASELINE_PATH.read_text(encoding="utf-8")

        self.assertEqual(analyzer.render_json(report), expected_text)
        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(report["inventory"]["module_count"], 48)
        self.assertEqual(len(report["registry"]["shipped_python_modules"]), 48)
        self.assertEqual(len(report["registry"]["runtime_import_closure"]), 47)
        self.assertEqual(report["registry"]["missing_internal_imports"], [])
        self.assertEqual(
            report["registry"]["unreachable_shipped_python_modules"],
            [
                "easyuse_anima/aio/__init__.py",
            ],
        )
        self.assertTrue(
            {
                "easyuse_anima/__init__.py",
                "easyuse_anima/aio/__init__.py",
                "easyuse_anima/common/__init__.py",
                "easyuse_anima/common/serialization.py",
                "easyuse_anima/common/values.py",
                "easyuse_anima/image/__init__.py",
                "easyuse_anima/image/detailer.py",
                "easyuse_anima/image/geometry.py",
                "easyuse_anima/image/scaling.py",
                "easyuse_anima/infrastructure/__init__.py",
                "easyuse_anima/infrastructure/comfy/__init__.py",
                "easyuse_anima/infrastructure/comfy/capabilities.py",
                "easyuse_anima/infrastructure/comfy/invocation.py",
                "easyuse_anima/infrastructure/comfy/resources.py",
                "easyuse_anima/lora/__init__.py",
                "easyuse_anima/lora/metadata.py",
                "easyuse_anima/lora/preset.py",
                "easyuse_anima/naia/__init__.py",
                "easyuse_anima/naia/client.py",
                "easyuse_anima/naia/resolution.py",
                "easyuse_anima/nodes/__init__.py",
                "easyuse_anima/nodes/image_nodes.py",
                "easyuse_anima/nodes/lora_nodes.py",
                "easyuse_anima/nodes/naia_nodes.py",
                "easyuse_anima/nodes/prompt_nodes.py",
                "easyuse_anima/nodes/wildcard_nodes.py",
                "easyuse_anima/profiles/__init__.py",
                "easyuse_anima/profiles/contract.py",
                "easyuse_anima/profiles/mutation.py",
                "easyuse_anima/prompt/__init__.py",
                "easyuse_anima/prompt/correction.py",
            }.issubset(report["registry"]["shipped_python_modules"])
        )
        self.assertIn("nodes.py", report["registry"]["shipped_python_modules"])
        self.assertIn("api.py", report["registry"]["runtime_import_closure"])
        self.assertTrue(
            {
                "easyuse_anima/common/serialization.py",
                "easyuse_anima/common/values.py",
                "easyuse_anima/image/detailer.py",
                "easyuse_anima/image/geometry.py",
                "easyuse_anima/image/scaling.py",
                "easyuse_anima/infrastructure/comfy/capabilities.py",
                "easyuse_anima/infrastructure/comfy/invocation.py",
                "easyuse_anima/infrastructure/comfy/resources.py",
                "easyuse_anima/lora/__init__.py",
                "easyuse_anima/lora/metadata.py",
                "easyuse_anima/lora/preset.py",
                "easyuse_anima/naia/__init__.py",
                "easyuse_anima/naia/client.py",
                "easyuse_anima/naia/resolution.py",
                "easyuse_anima/nodes/image_nodes.py",
                "easyuse_anima/nodes/lora_nodes.py",
                "easyuse_anima/nodes/naia_nodes.py",
                "easyuse_anima/nodes/prompt_nodes.py",
                "easyuse_anima/nodes/wildcard_nodes.py",
                "easyuse_anima/prompt/__init__.py",
                "easyuse_anima/prompt/correction.py",
                "easyuse_anima/profiles/__init__.py",
                "easyuse_anima/profiles/contract.py",
                "easyuse_anima/profiles/mutation.py",
            }.issubset(report["registry"]["runtime_import_closure"])
        )
        self.assertIn(
            "api_contract.py",
            report["registry"]["shipped_python_modules"],
        )
        self.assertIn(
            "api_contract.py",
            report["registry"]["runtime_import_closure"],
        )
        self.assertIn(
            "autocomplete_index.py",
            report["registry"]["shipped_python_modules"],
        )
        self.assertIn(
            "autocomplete_index.py",
            report["registry"]["runtime_import_closure"],
        )
        self.assertIn(
            {"from": "api.py", "to": "api_contract.py"},
            report["imports"]["module_graph"],
        )
        self.assertIn(
            {"from": "api.py", "to": "easyuse_anima/profiles/contract.py"},
            report["imports"]["module_graph"],
        )
        self.assertIn(
            {"from": "api.py", "to": "easyuse_anima/profiles/mutation.py"},
            report["imports"]["module_graph"],
        )
        self.assertNotIn(
            "tests/test_python_backend_analyzer.py",
            report["registry"]["shipped_python_modules"],
        )
        self.assertNotIn(
            "tools/analyze_python_backend.py",
            report["registry"]["shipped_python_modules"],
        )
        fallback_targets = {
            (item["source"], item["target"])
            for item in report["registry"]["compatibility_fallback_imports"]
        }
        self.assertTrue(
            {
                ("api.py", "storage.py"),
                ("api.py", "easyuse_anima/profiles/contract.py"),
                ("api.py", "easyuse_anima/profiles/mutation.py"),
                ("nodes.py", "prompt_translation.py"),
                ("nodes.py", "settings.py"),
                ("nodes.py", "wildcard_engine.py"),
                ("wildcard_engine.py", "settings.py"),
            }.issubset(fallback_targets)
        )
        self.assertFalse(
            [
                item
                for item in report["registry"]["external_imports"]
                if (item["source"], item.get("target")) in fallback_targets
            ]
        )
        mutable_by_name = {
            (item["module"], item["name"]): item["kind"]
            for item in report["state"]["mutable_globals"]
        }
        self.assertEqual(
            mutable_by_name[("wildcard_engine.py", "_SNAPSHOT_CACHE")],
            "dict",
        )
        owner_by_name = {
            (item["module"], item["name"]): set(item["categories"])
            for item in report["state"]["owner_candidates"]
        }
        self.assertIn(
            "cache",
            owner_by_name[("wildcard_engine.py", "_SNAPSHOT_CACHE")],
        )
        json.loads(expected_text)

    def test_human_render_has_module_edge_and_state_review_sections(self):
        report = analyzer.analyze_source_set(
            {
                "__init__.py": """\
try:
    from .runtime import VALUE
except ImportError:
    from runtime import VALUE
import os
CACHE = {}
""",
                "runtime.py": "VALUE = 1\n",
            }
        )

        rendered = analyzer.render_text(report)

        self.assertIn("[modules]\n", rendered)
        self.assertIn("[edges]\n", rendered)
        self.assertIn("[state.mutable_globals]\n", rendered)
        self.assertIn("[state.owner_candidates]\n", rendered)
        self.assertIn("ordinary", rendered)
        self.assertIn("compatibility_fallback", rendered)
        self.assertIn("try@", rendered)
        self.assertIn("conflicting branch aliases remain heuristic", rendered)
        self.assertIn("TYPE_CHECKING", rendered)


if __name__ == "__main__":
    unittest.main()
