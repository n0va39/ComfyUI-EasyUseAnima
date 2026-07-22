from __future__ import annotations

import ast
import json
import sys
import unittest
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT_PATH = ROOT / "__init__.py"
NODES_PATH = ROOT / "nodes.py"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "python_compatibility_surface.v1.json"

SCHEMA_VERSION = 1
BASE_COMMIT = "44d338bbc4ea6322edc83ab03928e8d14b5d8775"
CLASSIFICATIONS = (
    "permanent_entrypoint",
    "supported_public_reexport",
    "transitional_private_seam",
    "unsupported_test_only",
)
TARGET_STATES = ("canonical", "legacy_owner", "unassigned")
IDENTITY_REQUIREMENTS = ("stable_entrypoint", "required", "not_applicable")
BINDING_SHAPES = ("entrypoint", "direct_import", "root_definition")
LIFECYCLE_STATES = ("permanent", "supported", "transitional", "unsupported")
LEGACY_MODULE_OWNERS = {
    "anima_prompt": "#184/#186",
    "prompt_translation": "#164/#186",
    "settings": "#163/#186",
    "wildcard_engine": "#184/#186",
}
DOCUMENTED_TRANSITIONAL_ALIASES = {
    "EasyUseAnimaSAM3Context": {
        "consumer": "historical SAM3 convenience-node compatibility",
        "evidence": "docs/version-plans/0.1.6-Detailer.md",
    },
}
RUNTIME_LOOKUP_CALLS = {
    "_runtime_helper",
    "_runtime_object",
    "runtime_helper",
    "runtime_object",
    "_runtime_proxy",
    "runtime_proxy",
}
PREAMBLE_IMPLEMENTATION_BINDINGS = {
    "Any": "typing:Any",
    "ceil": "math:ceil",
    "json": "json:json",
    "logging": "logging:logging",
    "random": "random:random",
    "re": "re:re",
    "sqrt": "math:sqrt",
}
RETIRED_PRIVATE_BINDINGS = {
    "_image_scale_by_multiple_size": {
        "canonical_target": (
            "easyuse_anima.image.scaling:_image_scale_by_multiple_size"
        ),
        "owner": "#184/#188 B-10b6",
        "reason": "canonical image adapter imports the owner directly",
    },
    "_max_long_edge_value": {
        "canonical_target": "easyuse_anima.image.scaling:_max_long_edge_value",
        "owner": "#184/#188 B-10b6",
        "reason": "canonical scaling policy calls the owner directly",
    },
    "_normalize_image_scale_options": {
        "canonical_target": (
            "easyuse_anima.image.scaling:_normalize_image_scale_options"
        ),
        "owner": "#184/#188 B-10b6",
        "reason": "canonical image adapter imports the owner directly",
    },
    "_scale_by_value": {
        "canonical_target": "easyuse_anima.image.scaling:_scale_by_value",
        "owner": "#184/#188 B-10b6",
        "reason": "canonical scaling policy calls the owner directly",
    },
    "_align_up": {
        "canonical_target": "easyuse_anima.image.geometry:_align_up",
        "owner": "#184/#188 B-10b5",
        "reason": "canonical geometry and Detailer consumers import the owner directly",
    },
    "_aligned_size_near_scale": {
        "canonical_target": (
            "easyuse_anima.image.geometry:_aligned_size_near_scale"
        ),
        "owner": "#184/#188 B-10b5",
        "reason": "canonical image scaling imports the owner directly",
    },
    "_alignment_value": {
        "canonical_target": "easyuse_anima.image.geometry:_alignment_value",
        "owner": "#184/#188 B-10b5",
        "reason": "canonical image and Impact adapters import the owner directly",
    },
    "_impact_core_module": {
        "canonical_target": (
            "easyuse_anima.infrastructure.comfy.capabilities:_impact_core_module"
        ),
        "owner": "#184/#188 B-10b4",
        "reason": "scheduler lookup calls the canonical owner directly",
    },
    "_EasyUseAnimaImpactDetailerDelegate": {
        "canonical_target": (
            "easyuse_anima.nodes.impact_detailer_nodes:"
            "_EasyUseAnimaImpactDetailerDelegate"
        ),
        "owner": "#184/#188 B-10b3",
        "reason": "SAM3 production adapter imports the canonical owner directly",
    },
    "_EasyUseAnimaAlignedDetailerHook": {
        "canonical_target": (
            "easyuse_anima.image.detailer:_EasyUseAnimaAlignedDetailerHook"
        ),
        "owner": "#184/#188 B-10b2",
        "reason": "image and Impact Detailer adapters import the canonical owner",
    },
    "_comfy_checkpoint_names": {
        "canonical_target": (
            "easyuse_anima.infrastructure.comfy.resources:_comfy_checkpoint_names"
        ),
        "owner": "#184/#188 B-10b1",
        "reason": "production SAM3 consumer already imports the canonical owner",
    },
}


def _read_tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=path.name)


def _literal_string_list(node: ast.AST) -> list[str]:
    value = ast.literal_eval(node)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise AssertionError("expected a literal list of strings")
    return value


def _named_assignment(tree: ast.Module, name: str) -> ast.AST:
    matches: list[ast.AST] = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            matches.append(node.value)
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
        ):
            matches.append(node.value)
    if len(matches) != 1 or matches[0] is None:
        raise AssertionError(f"expected exactly one assignment for {name}")
    return matches[0]


def _literal_mapping(tree: ast.Module, name: str) -> dict[str, str]:
    node = _named_assignment(tree, name)
    if not isinstance(node, ast.Dict):
        raise AssertionError(f"{name} must remain a literal dictionary")
    result: dict[str, str] = {}
    for key, value in zip(node.keys, node.values, strict=True):
        if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
            raise AssertionError(f"{name} keys must remain literal strings")
        if isinstance(value, ast.Name):
            result[key.value] = value.id
        elif isinstance(value, ast.Constant) and isinstance(value.value, str):
            result[key.value] = value.value
        else:
            raise AssertionError(f"{name} values must remain names or literal strings")
    return result


def _root_import_try(tree: ast.Module) -> ast.Try:
    matches = []
    for node in tree.body:
        if not isinstance(node, ast.Try):
            continue
        imports = [item for item in node.body if isinstance(item, ast.ImportFrom)]
        if any(item.module and item.module.startswith("easyuse_anima") for item in imports):
            matches.append(node)
    if len(matches) != 1:
        raise AssertionError("nodes.py must have one relative/flat compatibility import try")
    node = matches[0]
    if len(node.handlers) != 1 or node.handlers[0].type is None:
        raise AssertionError("compatibility import try must have one ImportError fallback")
    exception = node.handlers[0].type
    if not isinstance(exception, ast.Name) or exception.id != "ImportError":
        raise AssertionError("compatibility import fallback must catch ImportError")
    if node.orelse or node.finalbody:
        raise AssertionError("compatibility import try cannot have else/finally branches")
    return node


def _branch_bindings(
    statements: list[ast.stmt],
    *,
    expected_level: int,
) -> tuple[dict[str, str], dict[str, str]]:
    canonical: dict[str, str] = {}
    legacy: dict[str, str] = {}
    for node in statements:
        if not isinstance(node, ast.ImportFrom) or not node.module:
            raise AssertionError(
                "compatibility import branches may contain only from-imports"
            )
        root = node.module.split(".", 1)[0]
        if root == "easyuse_anima":
            bucket = canonical
        elif root in LEGACY_MODULE_OWNERS:
            bucket = legacy
        else:
            raise AssertionError(
                f"unregistered compatibility import root in nodes.py: {root}"
            )
        if node.level != expected_level:
            raise AssertionError(
                f"{node.module} has import level {node.level}; expected {expected_level}"
            )
        for alias in node.names:
            local = alias.asname or alias.name
            if local in bucket:
                raise AssertionError(f"duplicate compatibility binding: {local}")
            bucket[local] = f"{node.module}:{alias.name}"
    return dict(sorted(canonical.items())), dict(sorted(legacy.items()))


def _preamble_implementation_bindings(
    tree: ast.Module,
    import_try: ast.Try,
) -> dict[str, str]:
    bindings: dict[str, str] = {}
    for node in tree.body:
        if node is import_try:
            break
        if isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name.split(".", 1)[0]
                bindings[local] = f"{alias.name}:{alias.name}"
        elif (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module not in {None, "__future__"}
        ):
            for alias in node.names:
                local = alias.asname or alias.name
                bindings[local] = f"{node.module}:{alias.name}"
    return dict(sorted(bindings.items()))


def _runtime_loads(tree: ast.Module, import_try: ast.Try) -> set[str]:
    remainder = ast.Module(
        body=[node for node in tree.body if node is not import_try],
        type_ignores=[],
    )
    return {
        node.id
        for node in ast.walk(remainder)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _runtime_binder_targets(
    tree: ast.Module,
    canonical_bindings: dict[str, str],
) -> dict[str, str]:
    targets: dict[str, str] = {}
    for binder in _runtime_binders(tree):
        target = canonical_bindings.get(binder)
        if target is None:
            raise AssertionError(f"runtime binder has no canonical import: {binder}")
        module, imported = target.split(":", 1)
        if imported != binder:
            raise AssertionError(
                f"runtime binder import must preserve its name: {binder} -> {target}"
            )
        targets[binder] = module
    return targets


def _module_path(module: str) -> Path:
    parts = module.split(".")
    path = ROOT.joinpath(*parts)
    package_path = path / "__init__.py"
    module_path = path.with_suffix(".py")
    if package_path.is_file():
        return package_path
    if module_path.is_file():
        return module_path
    raise AssertionError(f"canonical runtime binder module is missing: {module}")


def _resolver_names_from_module(module: str, available: set[str]) -> set[str]:
    tree = _read_tree(_module_path(module))
    names: set[str] = set()
    assignment_values: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignment_values[target.id] = node.value
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.value is not None
        ):
            assignment_values[node.target.id] = node.value

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        if _call_name(node.func) not in RUNTIME_LOOKUP_CALLS:
            continue
        first = node.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            names.add(first.value)

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not (node.name.startswith("_bind_") and node.name.endswith("_runtime")):
            continue
        referenced_assignments = {
            value.id
            for value in ast.walk(node)
            if isinstance(value, ast.Name) and isinstance(value.ctx, ast.Load)
        }
        names.update(
            value.value
            for value in ast.walk(node)
            if isinstance(value, ast.Constant) and isinstance(value.value, str)
        )
        for referenced in referenced_assignments:
            assigned = assignment_values.get(referenced)
            if assigned is None:
                continue
            names.update(
                value.value
                for value in ast.walk(assigned)
                if isinstance(value, ast.Constant) and isinstance(value.value, str)
            )
    return names.intersection(available)


def _runtime_resolver_consumers(
    tree: ast.Module,
    canonical_bindings: dict[str, str],
    available: set[str],
) -> dict[str, list[str]]:
    consumers: dict[str, set[str]] = defaultdict(set)
    for module in sorted(set(_runtime_binder_targets(tree, canonical_bindings).values())):
        for name in _resolver_names_from_module(module, available):
            consumers[name].add(module)
    return {
        name: sorted(modules)
        for name, modules in sorted(consumers.items())
    }


def _root_residuals(tree: ast.Module) -> dict[str, list[str]]:
    functions = sorted(
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )
    classes = sorted(node.name for node in tree.body if isinstance(node, ast.ClassDef))
    globals_: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    globals_.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            globals_.add(node.target.id)
    return {
        "functions": functions,
        "classes": classes,
        "globals": sorted(globals_),
    }


def _runtime_binders(tree: ast.Module) -> list[str]:
    binders = []
    for node in tree.body:
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        function = node.value.func
        if (
            isinstance(function, ast.Name)
            and function.id.startswith("_bind_")
            and function.id.endswith("_runtime")
        ):
            binders.append(function.id)
    return binders


def _direct_nodes_import_test_files() -> list[str]:
    consumers = []
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        tree = _read_tree(path)
        has_direct_import = any(
            (
                isinstance(node, ast.Import)
                and any(alias.name == "nodes" for alias in node.names)
            )
            or (isinstance(node, ast.ImportFrom) and node.module == "nodes")
            for node in ast.walk(tree)
        )
        if has_direct_import:
            consumers.append(path.relative_to(ROOT).as_posix())
    return consumers


def _metadata(
    *,
    classification: str,
    current_target: str,
    canonical_target: str | None,
    target_state: str,
    identity_requirement: str,
    binding_shape: str,
    import_target: str | None,
    owner: str,
) -> dict[str, Any]:
    if classification == "permanent_entrypoint":
        consumers = ["ComfyUI package loader"]
        evidence = ["__init__.py:__all__", "node contract fixture"]
        removal_gates = ["not removable; B-11 must preserve the entrypoint objects"]
        lifecycle_state = "permanent"
    elif classification == "supported_public_reexport":
        consumers = ["root package node mappings", "saved workflows"]
        evidence = ["__init__.py:NODE_CLASS_MAPPINGS", "0.5.2 node contract fixture"]
        removal_gates = [
            "separate breaking-change decision",
            "N+1 release evidence",
            "mapping, workflow, and direct identity parity",
        ]
        lifecycle_state = "supported"
    elif classification == "transitional_private_seam":
        consumers = ["nodes.py residual runtime"]
        evidence = ["AST:nodes.py runtime load"]
        removal_gates = [
            "canonical production consumer migration",
            "focused monkeypatch and identity contract review",
            "separate B-10b or B-11 rollback unit",
        ]
        lifecycle_state = "transitional"
    else:
        consumers = ["repository tests may import this root name"]
        evidence = [
            "AST:no nodes.py runtime load",
            "test-only consumption is not public support evidence",
        ]
        removal_gates = [
            "test imports migrate to canonical targets",
            "no production consumer evidence",
            "separate B-10b removal review",
        ]
        lifecycle_state = "unsupported"
    return {
        "classification": classification,
        "current_target": current_target,
        "canonical_target": canonical_target,
        "target_state": target_state,
        "identity_requirement": identity_requirement,
        "binding_shape": binding_shape,
        "import_target": import_target,
        "owner": owner,
        "first_release": None,
        "known_consumers": consumers,
        "evidence": evidence,
        "removal_gates": removal_gates,
        "lifecycle_state": lifecycle_state,
    }


def _binding_groups(
    *,
    surface: str,
    bindings: dict[str, str],
    runtime_loads: set[str],
    runtime_resolver_consumers: dict[str, list[str]],
    mapped_classes: set[str],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    for local, target in bindings.items():
        module, imported = target.split(":", 1)
        if local in mapped_classes:
            classification = "supported_public_reexport"
        elif (
            local in runtime_loads
            or local in runtime_resolver_consumers
            or local in DOCUMENTED_TRANSITIONAL_ALIASES
        ):
            classification = "transitional_private_seam"
        else:
            classification = "unsupported_test_only"
        grouped[(module, classification)][local] = imported

    groups = []
    for (module, classification), symbols in sorted(grouped.items()):
        canonical = surface == "nodes_canonical_bindings"
        owner_root = module.split(".", 1)[0]
        metadata = _metadata(
            classification=classification,
            current_target="nodes.py",
            canonical_target=module if canonical else None,
            target_state="canonical" if canonical else "legacy_owner",
            identity_requirement=(
                "not_applicable"
                if classification == "unsupported_test_only"
                else "required"
            ),
            binding_shape="direct_import",
            import_target=module,
            owner="#184/#188" if canonical else LEGACY_MODULE_OWNERS[owner_root],
        )
        if classification == "transitional_private_seam":
            direct_runtime = any(symbol in runtime_loads for symbol in symbols)
            resolver_modules = sorted(
                {
                    resolver_module
                    for symbol in symbols
                    for resolver_module in runtime_resolver_consumers.get(symbol, [])
                }
            )
            metadata["known_consumers"] = []
            metadata["evidence"] = []
            if direct_runtime:
                metadata["known_consumers"].append("nodes.py residual runtime")
                metadata["evidence"].append("AST:nodes.py direct runtime load")
            metadata["known_consumers"].extend(
                f"canonical runtime resolver: {resolver_module}"
                for resolver_module in resolver_modules
            )
            metadata["evidence"].extend(
                f"AST:{resolver_module} string runtime lookup"
                for resolver_module in resolver_modules
            )
            for symbol in sorted(symbols):
                documented = DOCUMENTED_TRANSITIONAL_ALIASES.get(symbol)
                if documented is None:
                    continue
                metadata["known_consumers"].append(documented["consumer"])
                metadata["evidence"].append(documented["evidence"])
            metadata["known_consumers"] = list(
                dict.fromkeys(metadata["known_consumers"])
            )
            metadata["evidence"] = list(dict.fromkeys(metadata["evidence"]))
            if not metadata["known_consumers"] or not metadata["evidence"]:
                raise AssertionError(
                    f"transitional group has no production evidence: {module}"
                )
        groups.append(
            {
                "id": f"{surface}:{module}:{classification}",
                "surface": surface,
                "symbols": dict(sorted(symbols.items())),
                **metadata,
            }
        )
    return groups


def _build_document() -> dict[str, Any]:
    entrypoint_tree = _read_tree(ENTRYPOINT_PATH)
    nodes_tree = _read_tree(NODES_PATH)
    import_try = _root_import_try(nodes_tree)
    preamble_bindings = _preamble_implementation_bindings(nodes_tree, import_try)
    if preamble_bindings != PREAMBLE_IMPLEMENTATION_BINDINGS:
        raise AssertionError(
            "nodes.py preamble implementation imports changed; classify the drift "
            "before updating the compatibility fixture"
        )
    relative, relative_legacy = _branch_bindings(import_try.body, expected_level=1)
    flat, flat_legacy = _branch_bindings(import_try.handlers[0].body, expected_level=0)
    if relative != flat or relative_legacy != flat_legacy:
        raise AssertionError("relative and flat fallback imports must have exact target parity")

    entrypoints = _literal_string_list(_named_assignment(entrypoint_tree, "__all__"))
    node_mappings = _literal_mapping(entrypoint_tree, "NODE_CLASS_MAPPINGS")
    display_mappings = _literal_mapping(entrypoint_tree, "NODE_DISPLAY_NAME_MAPPINGS")
    if set(node_mappings) != set(display_mappings):
        raise AssertionError("node and display mapping IDs differ")
    if set(node_mappings) != set(node_mappings.values()):
        raise AssertionError("mapped node IDs must retain same-named class bindings")
    mapped_classes = set(node_mappings.values())
    loads = _runtime_loads(nodes_tree, import_try)
    residuals = _root_residuals(nodes_tree)
    available = set(relative) | set(relative_legacy)
    for names in residuals.values():
        available.update(names)
    runtime_resolver_consumers = _runtime_resolver_consumers(
        nodes_tree,
        relative,
        available,
    )

    missing_documented_aliases = set(DOCUMENTED_TRANSITIONAL_ALIASES) - available
    if missing_documented_aliases:
        raise AssertionError(
            "documented transitional aliases are missing: "
            + ", ".join(sorted(missing_documented_aliases))
        )

    retired_overlap = set(RETIRED_PRIVATE_BINDINGS).intersection(available)
    if retired_overlap:
        raise AssertionError(
            "retired private bindings returned to the root surface: "
            + ", ".join(sorted(retired_overlap))
        )

    class_like_bindings = {
        name
        for name, target in relative.items()
        if name.startswith("EasyUseAnima") and target.endswith(f":{name}")
    }
    unmapped_classes = sorted(class_like_bindings - mapped_classes)

    groups: list[dict[str, Any]] = [
        {
            "id": "root_entrypoints:permanent",
            "surface": "root_entrypoints",
            "symbols": {name: name for name in sorted(entrypoints)},
            **_metadata(
                classification="permanent_entrypoint",
                current_target="__init__.py",
                canonical_target="__init__.py",
                target_state="canonical",
                identity_requirement="stable_entrypoint",
                binding_shape="entrypoint",
                import_target=None,
                owner="#184/#185",
            ),
        }
    ]
    groups.extend(
        _binding_groups(
            surface="nodes_canonical_bindings",
            bindings=relative,
            runtime_loads=loads,
            runtime_resolver_consumers=runtime_resolver_consumers,
            mapped_classes=mapped_classes,
        )
    )
    groups.extend(
        _binding_groups(
            surface="nodes_legacy_bindings",
            bindings=relative_legacy,
            runtime_loads=loads,
            runtime_resolver_consumers=runtime_resolver_consumers,
            mapped_classes=set(),
        )
    )

    for kind in ("functions", "classes", "globals"):
        groups.append(
            {
                "id": f"nodes_root_residuals:{kind}",
                "surface": "nodes_root_residuals",
                "kind": kind,
                "symbols": {name: name for name in residuals[kind]},
                **_metadata(
                    classification="transitional_private_seam",
                    current_target="nodes.py",
                    canonical_target=None,
                    target_state="unassigned",
                    identity_requirement="not_applicable",
                    binding_shape="root_definition",
                    import_target=None,
                    owner="#184",
                ),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "snapshot": {
            "base_branch": "dev",
            "base_commit": BASE_COMMIT,
            "first_release": None,
            "owner_tasks": [
                "#184",
                "#188",
                "B-10a",
                "B-10b1",
                "B-10b2",
                "B-10b3",
                "B-10b4",
                "B-10b5",
                "B-10b6",
            ],
        },
        "enums": {
            "classifications": list(CLASSIFICATIONS),
            "target_states": list(TARGET_STATES),
            "identity_requirements": list(IDENTITY_REQUIREMENTS),
            "binding_shapes": list(BINDING_SHAPES),
            "lifecycle_states": list(LIFECYCLE_STATES),
        },
        "expected_counts": {
            "root_entrypoints": 3,
            "excluded_preamble_implementation_bindings": 7,
            "nodes_canonical_bindings": 390,
            "nodes_legacy_bindings": 27,
            "mapped_public_classes": 18,
            "unmapped_classes": 3,
            "root_residual_functions": 41,
            "root_residual_classes": 2,
            "root_residual_globals": 33,
            "runtime_binders": 28,
            "direct_nodes_import_test_files": 21,
        },
        "mapped_public_classes": sorted(mapped_classes),
        "unmapped_classes": unmapped_classes,
        "excluded_preamble_implementation_bindings": preamble_bindings,
        "runtime_binders": _runtime_binders(nodes_tree),
        "runtime_resolver_consumers": runtime_resolver_consumers,
        "documented_transitional_aliases": DOCUMENTED_TRANSITIONAL_ALIASES,
        "retired_private_bindings": RETIRED_PRIVATE_BINDINGS,
        "direct_nodes_import_test_files": _direct_nodes_import_test_files(),
        "groups": sorted(groups, key=lambda group: group["id"]),
    }


def _flatten_groups(document: dict[str, Any], surface: str) -> dict[str, str]:
    flattened: dict[str, str] = {}
    for group in document["groups"]:
        if group["surface"] != surface:
            continue
        target = group["import_target"]
        for local, imported in group["symbols"].items():
            if local in flattened:
                raise AssertionError(f"duplicate fixture symbol on {surface}: {local}")
            if surface in {"nodes_canonical_bindings", "nodes_legacy_bindings"}:
                flattened[local] = f"{target}:{imported}"
            else:
                flattened[local] = imported
    return dict(sorted(flattened.items()))


class PythonCompatibilitySurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_fixture_is_deterministic_and_matches_the_current_ast_surface(self):
        self.assertEqual(self.document, _build_document())

    def test_schema_enforces_classification_and_required_lifecycle_metadata(self):
        self.assertEqual(self.document["schema_version"], SCHEMA_VERSION)
        self.assertEqual(self.document["enums"]["classifications"], list(CLASSIFICATIONS))
        self.assertEqual(self.document["enums"]["target_states"], list(TARGET_STATES))
        self.assertEqual(
            self.document["enums"]["identity_requirements"],
            list(IDENTITY_REQUIREMENTS),
        )
        self.assertEqual(self.document["enums"]["binding_shapes"], list(BINDING_SHAPES))
        self.assertEqual(
            self.document["enums"]["lifecycle_states"],
            list(LIFECYCLE_STATES),
        )

        required = {
            "id",
            "surface",
            "symbols",
            "classification",
            "current_target",
            "canonical_target",
            "target_state",
            "identity_requirement",
            "binding_shape",
            "import_target",
            "owner",
            "first_release",
            "known_consumers",
            "evidence",
            "removal_gates",
            "lifecycle_state",
        }
        seen_ids: set[str] = set()
        seen_symbols: dict[str, set[str]] = defaultdict(set)
        for group in self.document["groups"]:
            self.assertTrue(required.issubset(group), group.get("id"))
            self.assertNotIn(group["id"], seen_ids)
            seen_ids.add(group["id"])
            self.assertIn(group["classification"], CLASSIFICATIONS)
            self.assertIn(group["target_state"], TARGET_STATES)
            self.assertIn(group["identity_requirement"], IDENTITY_REQUIREMENTS)
            self.assertIn(group["binding_shape"], BINDING_SHAPES)
            self.assertIn(group["lifecycle_state"], LIFECYCLE_STATES)
            self.assertIsNone(group["first_release"])
            self.assertTrue(group["owner"])
            self.assertTrue(group["known_consumers"])
            self.assertTrue(group["evidence"])
            self.assertTrue(group["removal_gates"])
            self.assertTrue(group["symbols"])
            if group["binding_shape"] == "direct_import":
                self.assertTrue(group["import_target"])
            else:
                self.assertIsNone(group["import_target"])
            if group["classification"] == "unsupported_test_only":
                self.assertEqual(group["identity_requirement"], "not_applicable")
            duplicates = seen_symbols[group["surface"]].intersection(group["symbols"])
            self.assertEqual(duplicates, set(), group["id"])
            seen_symbols[group["surface"]].update(group["symbols"])

    def test_root_entrypoint_and_node_class_contracts_are_exact(self):
        counts = self.document["expected_counts"]
        entrypoints = _flatten_groups(self.document, "root_entrypoints")
        canonical = _flatten_groups(self.document, "nodes_canonical_bindings")
        legacy = _flatten_groups(self.document, "nodes_legacy_bindings")
        self.assertEqual(len(entrypoints), counts["root_entrypoints"])
        self.assertEqual(len(canonical), counts["nodes_canonical_bindings"])
        self.assertEqual(len(legacy), counts["nodes_legacy_bindings"])
        self.assertEqual(
            len(self.document["mapped_public_classes"]),
            counts["mapped_public_classes"],
        )
        self.assertEqual(
            len(self.document["unmapped_classes"]), counts["unmapped_classes"]
        )

        supported = {
            symbol
            for group in self.document["groups"]
            if group["surface"] == "nodes_canonical_bindings"
            and group["classification"] == "supported_public_reexport"
            for symbol in group["symbols"]
        }
        self.assertEqual(supported, set(self.document["mapped_public_classes"]))
        self.assertTrue(
            all(canonical[name].startswith("easyuse_anima.nodes.") for name in supported)
        )
        self.assertTrue(
            all(canonical[name].endswith(f":{name}") for name in supported)
        )
        self.assertEqual(
            self.document["unmapped_classes"],
            [
                "EasyUseAnimaPromptStudioExtend",
                "EasyUseAnimaSAM3Context",
                "EasyUseAnimaSAM3Detailer",
            ],
        )

    def test_preamble_implementation_import_exclusion_is_exact(self):
        counts = self.document["expected_counts"]
        excluded = self.document["excluded_preamble_implementation_bindings"]
        self.assertEqual(excluded, PREAMBLE_IMPLEMENTATION_BINDINGS)
        self.assertEqual(
            len(excluded),
            counts["excluded_preamble_implementation_bindings"],
        )
        compatibility_symbols = {
            symbol
            for group in self.document["groups"]
            for symbol in group["symbols"]
        }
        self.assertTrue(set(excluded).isdisjoint(compatibility_symbols))

    def test_retired_private_bindings_cannot_return_to_the_root_surface(self):
        retired = self.document["retired_private_bindings"]
        self.assertEqual(retired, RETIRED_PRIVATE_BINDINGS)
        compatibility_symbols = {
            symbol
            for group in self.document["groups"]
            for symbol in group["symbols"]
        }
        self.assertTrue(set(retired).isdisjoint(compatibility_symbols))
        for metadata in retired.values():
            self.assertTrue(metadata["canonical_target"])
            self.assertTrue(metadata["owner"])
            self.assertTrue(metadata["reason"])

    def test_relative_and_flat_binding_targets_match_the_machine_readable_fixture(self):
        tree = _read_tree(NODES_PATH)
        import_try = _root_import_try(tree)
        relative, relative_legacy = _branch_bindings(import_try.body, expected_level=1)
        flat, flat_legacy = _branch_bindings(
            import_try.handlers[0].body,
            expected_level=0,
        )
        canonical_fixture = _flatten_groups(
            self.document, "nodes_canonical_bindings"
        )
        legacy_fixture = _flatten_groups(self.document, "nodes_legacy_bindings")
        self.assertEqual(relative, flat)
        self.assertEqual(relative, canonical_fixture)
        self.assertEqual(relative_legacy, flat_legacy)
        self.assertEqual(relative_legacy, legacy_fixture)

    def test_compatibility_branches_reject_unregistered_imports_and_statements(self):
        unknown_import = ast.parse("from foreign_root import helper").body
        with self.assertRaisesRegex(
            AssertionError,
            "unregistered compatibility import root",
        ):
            _branch_bindings(unknown_import, expected_level=0)

        plain_import = ast.parse("import foreign_root").body
        with self.assertRaisesRegex(
            AssertionError,
            "may contain only from-imports",
        ):
            _branch_bindings(plain_import, expected_level=0)

    def test_root_residual_implementation_is_exact_and_never_publicly_promoted(self):
        counts = self.document["expected_counts"]
        expected = {
            "functions": counts["root_residual_functions"],
            "classes": counts["root_residual_classes"],
            "globals": counts["root_residual_globals"],
        }
        residual_groups = [
            group
            for group in self.document["groups"]
            if group["surface"] == "nodes_root_residuals"
        ]
        self.assertEqual({group["kind"] for group in residual_groups}, set(expected))
        for group in residual_groups:
            self.assertEqual(len(group["symbols"]), expected[group["kind"]])
            self.assertEqual(group["classification"], "transitional_private_seam")
            self.assertIsNone(group["canonical_target"])
            self.assertEqual(group["target_state"], "unassigned")
            self.assertEqual(group["identity_requirement"], "not_applicable")

    def test_runtime_binders_and_test_only_root_import_consumers_are_exact(self):
        counts = self.document["expected_counts"]
        self.assertEqual(len(self.document["runtime_binders"]), counts["runtime_binders"])
        self.assertEqual(
            len(self.document["direct_nodes_import_test_files"]),
            counts["direct_nodes_import_test_files"],
        )
        self.assertEqual(len(set(self.document["runtime_binders"])), 28)
        self.assertEqual(len(set(self.document["direct_nodes_import_test_files"])), 21)

    def test_string_runtime_resolvers_keep_production_seams_transitional(self):
        representative = {
            "_run_aio_legacy_generation",
            "_AIO_FIRST_PASS_CACHE",
            "_AIO_FIRST_PASS_CACHE_ORDER",
            "_load_aio_resources_from_input_context",
            "_sample_latent_with_aio_backend",
            "_advanced_prompt_with_artist_override",
            "_encode_prompt_data_positive_conditioning",
        }
        consumers = self.document["runtime_resolver_consumers"]
        classifications = {
            symbol: group["classification"]
            for group in self.document["groups"]
            if group["surface"]
            in {"nodes_canonical_bindings", "nodes_legacy_bindings"}
            for symbol in group["symbols"]
        }
        for symbol in representative:
            self.assertIn(symbol, consumers)
            self.assertTrue(consumers[symbol])
            self.assertEqual(
                classifications[symbol],
                "transitional_private_seam",
            )

    def test_documented_unmapped_convenience_alias_stays_transitional(self):
        symbol = "EasyUseAnimaSAM3Context"
        groups = [
            group
            for group in self.document["groups"]
            if symbol in group["symbols"]
        ]
        self.assertEqual(len(groups), 1)
        group = groups[0]
        self.assertEqual(group["classification"], "transitional_private_seam")
        documented = self.document["documented_transitional_aliases"][symbol]
        self.assertIn(documented["consumer"], group["known_consumers"])
        self.assertIn(documented["evidence"], group["evidence"])

    def test_tests_only_consumption_never_counts_as_public_support_evidence(self):
        for group in self.document["groups"]:
            if group["classification"] == "supported_public_reexport":
                self.assertTrue(
                    any(not item.startswith("test:") for item in group["evidence"]),
                    group["id"],
                )
            if group["classification"] == "unsupported_test_only":
                self.assertIn(
                    "test-only consumption is not public support evidence",
                    group["evidence"],
                )


def write_fixture() -> None:
    FIXTURE_PATH.write_text(
        json.dumps(_build_document(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    if sys.argv[1:] == ["--write-fixture"]:
        write_fixture()
    else:
        unittest.main()
