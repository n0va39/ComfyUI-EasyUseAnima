#!/usr/bin/env python3
"""Build a deterministic, AST-only inventory of the production Python backend.

The analyzer reads source files and ``.comfyignore`` only.  It never imports
production modules, starts ComfyUI, invokes Git, opens a network connection, or
executes repository code.

Deterministic output rules:

* paths are repository-relative POSIX paths;
* CRLF and bare CR are normalized to LF before parsing and blob hashing;
* module, edge, state, side-effect, and SCC collections are sorted;
* JSON object keys are sorted and the rendered document ends with one LF;
* no absolute paths, user names, object ids, timestamps, or runtime values are
  included.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import hashlib
import json
from collections import deque
from pathlib import Path
from typing import Iterable, Mapping, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ROOT_MODULE = "__root__"
SCHEMA_VERSION = 1
DYNAMIC_IMPORT_CALLEES = frozenset({"__import__", "importlib.import_module"})
MUTABLE_CONSTRUCTORS = {
    "dict": "dict",
    "list": "list",
    "set": "set",
}
ROUTE_METHODS = frozenset(
    {
        "delete",
        "get",
        "patch",
        "post",
        "put",
        "route",
    }
)


def _normalize_newlines(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _normalized_git_blob_sha1(data: bytes) -> str:
    normalized = _normalize_newlines(data)
    header = f"blob {len(normalized)}\0".encode("ascii")
    return hashlib.sha1(header + normalized).hexdigest()


def _decode_source(data: bytes) -> str:
    return _normalize_newlines(data).decode("utf-8-sig")


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _assigned_names(node: ast.AST) -> Iterable[str]:
    if isinstance(node, ast.Name):
        yield node.id
    elif isinstance(node, (ast.List, ast.Tuple)):
        for item in node.elts:
            yield from _assigned_names(item)


def _module_identity(path: str) -> tuple[str, bool]:
    parts = list(Path(path).with_suffix("").parts)
    is_package = bool(parts and parts[-1] == "__init__")
    if is_package:
        parts.pop()
    internal_name = ".".join(parts)
    return (internal_name or ROOT_MODULE), is_package


def _internal_name(module_name: str) -> str:
    return "" if module_name == ROOT_MODULE else module_name


def _ignore_rules(ignore_text: str) -> list[dict[str, object]]:
    rules = []
    for line_number, raw_line in enumerate(ignore_text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        negated = stripped.startswith("!")
        pattern = stripped[1:] if negated else stripped
        directory_only = pattern.endswith("/")
        pattern = pattern.rstrip("/")
        anchored = pattern.startswith("/")
        pattern = pattern.lstrip("/")
        if not pattern:
            continue
        rules.append(
            {
                "line": line_number,
                "pattern": pattern,
                "negated": negated,
                "directory_only": directory_only,
                "anchored": anchored,
            }
        )
    return rules


def _match_path_pattern(path: str, pattern: str, *, anchored: bool) -> bool:
    if "/" not in pattern:
        return fnmatch.fnmatchcase(path.rsplit("/", 1)[-1], pattern)
    if fnmatch.fnmatchcase(path, pattern):
        return True
    if anchored:
        return False
    parts = path.split("/")
    return any(
        fnmatch.fnmatchcase("/".join(parts[index:]), pattern)
        for index in range(1, len(parts))
    )


def _rule_matches(path: str, rule: Mapping[str, object]) -> bool:
    parts = path.split("/")
    pattern = str(rule["pattern"])
    anchored = bool(rule["anchored"])
    if bool(rule["directory_only"]):
        directories = ["/".join(parts[:index]) for index in range(1, len(parts))]
        if "/" not in pattern and not anchored:
            return any(fnmatch.fnmatchcase(part, pattern) for part in parts[:-1])
        return any(
            _match_path_pattern(directory, pattern, anchored=anchored)
            for directory in directories
        )
    return _match_path_pattern(path, pattern, anchored=anchored)


def _is_ignored(path: str, rules: Sequence[Mapping[str, object]]) -> bool:
    ignored = False
    for rule in rules:
        if _rule_matches(path, rule):
            ignored = not bool(rule["negated"])
    return ignored


def _collect_dynamic_aliases(tree: ast.AST) -> dict[str, set[str]]:
    aliases: dict[str, set[str]] = {}

    def bind(name: str, target: str) -> None:
        aliases.setdefault(name, set()).add(target)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    bind(alias.asname, alias.name)
                else:
                    bind(alias.name.split(".", 1)[0], alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            for alias in node.names:
                if alias.name != "*":
                    target = f"{module}.{alias.name}" if module else alias.name
                    bind(alias.asname or alias.name, target)
    return aliases


def _resolve_callee_aliases(callee: str, aliases: Mapping[str, set[str]]) -> set[str]:
    resolved = {callee}
    root, separator, suffix = callee.partition(".")
    for target in aliases.get(root, set()):
        resolved.add(f"{target}.{suffix}" if separator else target)
    return resolved


def _caught_import_error(handler_type: ast.AST | None) -> bool:
    if handler_type is None:
        return True
    names = (
        handler_type.elts
        if isinstance(handler_type, ast.Tuple)
        else [handler_type]
    )
    return any(
        _call_name(item).rsplit(".", 1)[-1] in {"ImportError", "ModuleNotFoundError"}
        for item in names
    )


def _is_type_checking_test(node: ast.AST) -> bool:
    return _call_name(node).rsplit(".", 1)[-1] == "TYPE_CHECKING"


class _ImportCandidateVisitor(ast.NodeVisitor):
    def __init__(self, aliases: Mapping[str, set[str]]) -> None:
        self.aliases = aliases
        self.candidates: list[dict[str, object]] = []
        self.scope_parts: list[str] = []
        self.optional_depth = 0
        self.conditional_depth = 0

    @property
    def scope(self) -> str:
        return ".".join(self.scope_parts) if self.scope_parts else "<module>"

    def _append(
        self,
        *,
        node: ast.AST,
        kind: str,
        requested: str,
        name: str | None,
        alias: str | None,
    ) -> None:
        self.candidates.append(
            {
                "kind": kind,
                "requested": requested,
                "name": name,
                "alias": alias,
                "line": node.lineno,
                "column": node.col_offset,
                "scope": self.scope,
                "optional": self.optional_depth > 0,
                "conditional": self.conditional_depth > 0,
            }
        )

    def _visit_scope(self, node: ast.AST, name: str) -> None:
        self.scope_parts.append(name)
        self.generic_visit(node)
        self.scope_parts.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_scope(node, node.name)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_scope(node, node.name)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._visit_scope(node, node.name)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._append(
                node=node,
                kind="static_import",
                requested=alias.name,
                name=None,
                alias=alias.asname,
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        requested = "." * node.level + (node.module or "")
        for alias in node.names:
            self._append(
                node=node,
                kind="static_from",
                requested=requested,
                name=alias.name,
                alias=alias.asname,
            )

    def visit_Call(self, node: ast.Call) -> None:
        callee = _call_name(node.func)
        if _resolve_callee_aliases(callee, self.aliases).intersection(DYNAMIC_IMPORT_CALLEES):
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                self._append(
                    node=node,
                    kind="literal_dynamic",
                    requested=node.args[0].value,
                    name=None,
                    alias=None,
                )
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        catches_import_error = any(_caught_import_error(handler.type) for handler in node.handlers)
        if catches_import_error:
            self.optional_depth += 1
        for statement in node.body:
            self.visit(statement)
        if catches_import_error:
            self.optional_depth -= 1
        for handler in node.handlers:
            self.visit(handler)
        for statement in node.orelse:
            self.visit(statement)
        for statement in node.finalbody:
            self.visit(statement)

    def visit_If(self, node: ast.If) -> None:
        self.visit(node.test)
        self.conditional_depth += 1
        if _is_type_checking_test(node.test):
            self.optional_depth += 1
        for statement in node.body:
            self.visit(statement)
        if _is_type_checking_test(node.test):
            self.optional_depth -= 1
        for statement in node.orelse:
            self.visit(statement)
        self.conditional_depth -= 1


def _mutable_kind(value: ast.AST | None) -> str | None:
    if isinstance(value, ast.Dict):
        return "dict"
    if isinstance(value, ast.List):
        return "list"
    if isinstance(value, ast.Set):
        return "set"
    if isinstance(value, ast.Call):
        return MUTABLE_CONSTRUCTORS.get(_call_name(value.func).rsplit(".", 1)[-1])
    return None


def _initializer_name(value: ast.AST | None) -> str:
    if isinstance(value, ast.Call):
        return _call_name(value.func)
    if value is None:
        return ""
    return type(value).__name__


def _owner_categories(
    name: str,
    initializer: str,
    mutable_kind: str | None,
    *,
    is_call_initializer: bool,
) -> list[str]:
    haystack = f"{name} {initializer}".lower().replace("-", "_")
    initializer_lower = initializer.lower()
    categories = set()
    if any(token in initializer_lower for token in ("rlock", "lock")) or (
        mutable_kind and "lock" in name.lower()
    ):
        categories.add("lock")
    if "future" in initializer_lower or (
        mutable_kind and any(token in haystack for token in ("inflight", "in_flight"))
    ):
        categories.add("future")
    if is_call_initializer and any(
        token in initializer_lower for token in ("executor", "worker", "threadpool", "processpool")
    ):
        categories.add("executor")
    if (
        is_call_initializer
        and any(token in haystack for token in ("client", "session", "translator"))
    ) or (
        mutable_kind
        and "provider_instances" in name.lower()
    ):
        categories.add("client")
    if (mutable_kind and "cache" in name.lower()) or "cache" in initializer_lower:
        categories.add("cache")
    if mutable_kind and any(
        token in haystack
        for token in ("single_flight", "singleflight", "inflight", "in_flight", "building")
    ):
        categories.add("single_flight")
    if mutable_kind and categories:
        categories.add("mutable_container")
    return sorted(categories)


def _direct_assignments(tree: ast.Module) -> list[tuple[str, int, ast.AST | None]]:
    assignments = []
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                for name in _assigned_names(target):
                    assignments.append((name, statement.lineno, statement.value))
        elif isinstance(statement, ast.AnnAssign):
            for name in _assigned_names(statement.target):
                assignments.append((name, statement.lineno, statement.value))
        elif isinstance(statement, ast.AugAssign):
            for name in _assigned_names(statement.target):
                assignments.append((name, statement.lineno, statement.value))
    return assignments


def _context_assignment_names(node: ast.Assign | ast.AnnAssign | ast.AugAssign) -> list[str]:
    if isinstance(node, ast.Assign):
        return sorted({name for target in node.targets for name in _assigned_names(target)})
    return sorted(set(_assigned_names(node.target)))


class _ImportTimeCallVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.scope_parts: list[str] = []
        self.context = "expression"

    @property
    def scope(self) -> str:
        return ".".join(self.scope_parts) if self.scope_parts else "<module>"

    def _visit_with_context(self, node: ast.AST | None, context: str) -> None:
        if node is None:
            return
        previous = self.context
        self.context = context
        self.visit(node)
        self.context = previous

    def _visit_function_definition(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        for decorator in node.decorator_list:
            self._visit_with_context(decorator, f"decorator:{node.name}")
        for default in (
            *node.args.defaults,
            *[item for item in node.args.kw_defaults if item],
        ):
            self._visit_with_context(default, f"default:{node.name}")

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function_definition(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function_definition(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        for default in (*node.args.defaults, *[item for item in node.args.kw_defaults if item]):
            self._visit_with_context(default, "lambda_default")

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for decorator in node.decorator_list:
            self._visit_with_context(decorator, f"decorator:{node.name}")
        for base in node.bases:
            self._visit_with_context(base, f"class_base:{node.name}")
        for keyword in node.keywords:
            self._visit_with_context(keyword.value, f"class_keyword:{node.name}")
        self.scope_parts.append(node.name)
        for statement in node.body:
            self.visit(statement)
        self.scope_parts.pop()

    def visit_Assign(self, node: ast.Assign) -> None:
        names = _context_assignment_names(node)
        self._visit_with_context(node.value, f"assign:{','.join(names)}")

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        names = _context_assignment_names(node)
        self._visit_with_context(node.value, f"assign:{','.join(names)}")

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        names = _context_assignment_names(node)
        self._visit_with_context(node.value, f"assign:{','.join(names)}")

    def visit_Call(self, node: ast.Call) -> None:
        callee = _call_name(node.func)
        lowered = callee.lower()
        tail = lowered.rsplit(".", 1)[-1]
        context_lower = self.context.lower()
        if self.context.startswith("decorator:") and (
            tail in ROUTE_METHODS or "route" in lowered
        ):
            kind = "route_registration"
        elif tail in {"mkdir", "makedirs"} or "ensure_default_wildcard_root" in lowered:
            kind = "directory_creation"
        elif self.context.startswith("assign:") and (
            "route" in context_lower or "route" in lowered
        ):
            kind = "route_registry_creation"
        elif self.context.startswith("assign:") and any(
            token in context_lower or token in lowered
            for token in ("client", "session", "translator")
        ):
            kind = "client_creation"
        else:
            kind = "import_time_call"
        self.calls.append(
            {
                "line": node.lineno,
                "column": node.col_offset,
                "scope": self.scope,
                "context": self.context,
                "callee": callee or "<callable-expression>",
                "kind": kind,
            }
        )
        self.generic_visit(node)


def _literal_string_sequence(value: ast.AST | None) -> list[str]:
    if not isinstance(value, (ast.List, ast.Tuple, ast.Set)):
        return []
    values = [
        item.value
        for item in value.elts
        if isinstance(item, ast.Constant) and isinstance(item.value, str)
    ]
    return values if len(values) == len(value.elts) else []


def _analyze_module(path: str, data: bytes) -> dict[str, object]:
    source = _decode_source(data)
    module_name, is_package = _module_identity(path)
    tree = ast.parse(source, filename=path)
    function_count = 0
    class_count = 0
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function_count += 1
        elif isinstance(statement, ast.ClassDef):
            class_count += 1

    assignments = _direct_assignments(tree)
    globals_by_name: dict[str, int] = {}
    mutable_globals = []
    owner_candidates = []
    declared_all: list[str] = []
    for name, line, value in assignments:
        globals_by_name.setdefault(name, line)
        mutable_kind = _mutable_kind(value)
        initializer = _initializer_name(value)
        if mutable_kind:
            mutable_globals.append(
                {
                    "module": path,
                    "name": name,
                    "line": line,
                    "kind": mutable_kind,
                }
            )
        categories = _owner_categories(
            name,
            initializer,
            mutable_kind,
            is_call_initializer=isinstance(value, ast.Call),
        )
        if categories:
            owner_candidates.append(
                {
                    "module": path,
                    "name": name,
                    "line": line,
                    "initializer": initializer,
                    "categories": categories,
                }
            )
        if name == "__all__":
            declared_all = _literal_string_sequence(value)

    aliases = _collect_dynamic_aliases(tree)
    import_visitor = _ImportCandidateVisitor(aliases)
    import_visitor.visit(tree)
    side_effect_visitor = _ImportTimeCallVisitor()
    side_effect_visitor.visit(tree)

    record = {
        "module": module_name,
        "path": path,
        "is_package": is_package,
        "normalized_git_blob_sha1": _normalized_git_blob_sha1(data),
        "loc": len(source.splitlines()),
        "top_level": {
            "function_count": function_count,
            "class_count": class_count,
            "global_count": len(globals_by_name),
        },
    }
    return {
        "record": record,
        "imports": import_visitor.candidates,
        "mutable_globals": mutable_globals,
        "owner_candidates": owner_candidates,
        "side_effects": side_effect_visitor.calls,
        "declared_all": declared_all,
        "public_global_names": sorted(
            name for name in globals_by_name if not name.startswith("_")
        ),
    }


def _resolve_relative_name(requested: str, *, source_name: str, is_package: bool) -> str:
    level = len(requested) - len(requested.lstrip("."))
    if level == 0:
        return requested
    remainder = requested[level:]
    package_parts = (
        source_name.split(".")
        if is_package and source_name
        else source_name.split(".")[:-1]
    )
    remove_count = max(0, level - 1)
    if remove_count:
        package_parts = package_parts[: max(0, len(package_parts) - remove_count)]
    if remainder:
        package_parts.extend(remainder.split("."))
    return ".".join(part for part in package_parts if part)


def _edge_display(candidate: Mapping[str, object]) -> str:
    requested = str(candidate["requested"])
    name = candidate.get("name")
    return f"{requested}:{name}" if name else requested


def _resolve_import_candidate(
    candidate: Mapping[str, object],
    *,
    source_name: str,
    is_package: bool,
    path_by_internal_name: Mapping[str, str],
) -> dict[str, object]:
    requested = str(candidate["requested"])
    resolved_base = _resolve_relative_name(
        requested,
        source_name=source_name,
        is_package=is_package,
    )
    options = []
    imported_name = candidate.get("name")
    if imported_name and imported_name != "*":
        options.append(".".join(part for part in (resolved_base, str(imported_name)) if part))
    options.append(resolved_base)
    is_relative = requested.startswith(".")
    target_internal_name = (
        next(
            (option for option in options if option in path_by_internal_name),
            None,
        )
        if is_relative
        else None
    )
    if target_internal_name is not None:
        classification = "internal"
        target = path_by_internal_name[target_internal_name]
    else:
        classification = "missing_internal" if is_relative else "external"
        target = None

    edge = {
        "source": str(candidate["source"]),
        "line": int(candidate["line"]),
        "column": int(candidate["column"]),
        "scope": str(candidate["scope"]),
        "kind": str(candidate["kind"]),
        "imported": _edge_display(candidate),
        "requested": requested,
        "name": imported_name,
        "alias": candidate.get("alias"),
        "optional": bool(candidate["optional"]),
        "conditional": bool(candidate["conditional"]),
        "classification": classification,
    }
    if target is not None:
        edge["target"] = target
    return edge


def _strongly_connected_components(
    nodes: Sequence[str],
    graph_edges: Sequence[Mapping[str, str]],
) -> list[dict[str, object]]:
    adjacency = {node: set() for node in nodes}
    self_edges = set()
    for edge in graph_edges:
        source = edge["from"]
        target = edge["to"]
        adjacency[source].add(target)
        if source == target:
            self_edges.add(source)

    index = 0
    indices: dict[str, int] = {}
    low_links: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        low_links[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for target in sorted(adjacency[node]):
            if target not in indices:
                visit(target)
                low_links[node] = min(low_links[node], low_links[target])
            elif target in on_stack:
                low_links[node] = min(low_links[node], indices[target])

        if low_links[node] == indices[node]:
            component = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == node:
                    break
            components.append(sorted(component))

    for node in sorted(nodes):
        if node not in indices:
            visit(node)

    components.sort()
    return [
        {
            "modules": component,
            "cyclic": len(component) > 1 or component[0] in self_edges,
        }
        for component in components
    ]


def _package_ancestors(path: str, available_paths: set[str]) -> list[str]:
    parts = path.split("/")[:-1]
    ancestors = []
    for length in range(1, len(parts) + 1):
        candidate = "/".join((*parts[:length], "__init__.py"))
        if candidate in available_paths:
            ancestors.append(candidate)
    return ancestors


def _registry_closure(
    nodes: Sequence[str],
    graph_edges: Sequence[Mapping[str, str]],
) -> list[str]:
    if "__init__.py" not in nodes:
        return []
    available = set(nodes)
    adjacency = {node: set() for node in nodes}
    for edge in graph_edges:
        adjacency[edge["from"]].add(edge["to"])
    pending = deque(["__init__.py"])
    visited = set()
    while pending:
        node = pending.popleft()
        if node in visited:
            continue
        visited.add(node)
        targets = set(adjacency.get(node, set()))
        for target in tuple(targets):
            targets.update(_package_ancestors(target, available))
        pending.extend(sorted(targets - visited))
    return sorted(visited)


def _edge_summary(edge: Mapping[str, object]) -> dict[str, object]:
    summary = {
        "source": edge["source"],
        "line": edge["line"],
        "kind": edge["kind"],
        "imported": edge["imported"],
        "classification": edge["classification"],
        "optional": edge["optional"],
    }
    if "target" in edge:
        summary["target"] = edge["target"]
    return summary


def _public_surface(
    root_analysis: Mapping[str, object],
    edges: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    declared_all = list(root_analysis["declared_all"])
    public_globals = list(root_analysis["public_global_names"])
    reexports = []
    for edge in edges:
        if (
            edge["source"] != "__init__.py"
            or edge["scope"] != "<module>"
            or edge["classification"] != "internal"
            or edge["kind"] == "literal_dynamic"
        ):
            continue
        bound_name = edge["alias"] or edge["name"]
        if not bound_name:
            bound_name = str(edge["requested"]).split(".", 1)[0]
        if not bound_name or str(bound_name).startswith("_"):
            continue
        reexports.append(
            {
                "name": str(bound_name),
                "source": str(edge["target"]),
                "imported": str(edge["imported"]),
                "line": int(edge["line"]),
                "declared_in_all": str(bound_name) in declared_all,
            }
        )
    reexports.sort(
        key=lambda item: (
            str(item["name"]),
            str(item["source"]),
            int(item["line"]),
        )
    )
    compatibility_names = sorted(
        set(declared_all)
        | set(public_globals)
        | {str(item["name"]) for item in reexports}
    )
    return {
        "root": "__init__.py",
        "declared_all": declared_all,
        "reexports": reexports,
        "public_globals": public_globals,
        "compatibility_names": compatibility_names,
    }


def analyze_source_set(
    sources: Mapping[str, bytes | str],
    *,
    comfyignore: bytes | str = b"",
) -> dict[str, object]:
    """Analyze an in-memory repository surface without executing its sources."""

    source_bytes = {
        Path(path).as_posix(): (
            value.encode("utf-8") if isinstance(value, str) else value
        )
        for path, value in sources.items()
    }
    ignore_bytes = (
        comfyignore.encode("utf-8")
        if isinstance(comfyignore, str)
        else comfyignore
    )
    ignore_text = _decode_source(ignore_bytes)
    rules = _ignore_rules(ignore_text)
    shipped_paths = sorted(
        path
        for path in source_bytes
        if path.endswith(".py") and not _is_ignored(path, rules)
    )
    if "__init__.py" not in shipped_paths:
        raise ValueError("Registry Python surface must include the root __init__.py entry module.")

    analyses = {
        path: _analyze_module(path, source_bytes[path])
        for path in shipped_paths
    }
    path_by_internal_name = {
        _internal_name(str(analysis["record"]["module"])): path
        for path, analysis in analyses.items()
    }
    edges = []
    for path in shipped_paths:
        analysis = analyses[path]
        module_name = _internal_name(str(analysis["record"]["module"]))
        is_package = bool(analysis["record"]["is_package"])
        for candidate in analysis["imports"]:
            candidate = {**candidate, "source": path}
            edges.append(
                _resolve_import_candidate(
                    candidate,
                    source_name=module_name,
                    is_package=is_package,
                    path_by_internal_name=path_by_internal_name,
                )
            )
    edges.sort(
        key=lambda item: (
            str(item["source"]),
            int(item["line"]),
            int(item["column"]),
            str(item["kind"]),
            str(item["imported"]),
            str(item.get("alias")),
        )
    )
    graph_edges = sorted(
        {
            (str(edge["source"]), str(edge["target"]))
            for edge in edges
            if edge["classification"] == "internal"
        }
    )
    graph_records = [{"from": source, "to": target} for source, target in graph_edges]
    closure = _registry_closure(shipped_paths, graph_records)
    closure_set = set(closure)
    closure_edges = [edge for edge in edges if edge["source"] in closure_set]

    mutable_globals = sorted(
        (item for analysis in analyses.values() for item in analysis["mutable_globals"]),
        key=lambda item: (str(item["module"]), str(item["name"]), int(item["line"])),
    )
    owner_candidates = sorted(
        (item for analysis in analyses.values() for item in analysis["owner_candidates"]),
        key=lambda item: (str(item["module"]), str(item["name"]), int(item["line"])),
    )
    side_effects = sorted(
        (
            {**item, "module": path}
            for path, analysis in analyses.items()
            for item in analysis["side_effects"]
        ),
        key=lambda item: (
            str(item["module"]),
            int(item["line"]),
            int(item["column"]),
            str(item["callee"]),
        ),
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "determinism": {
            "encoding": "utf-8-sig",
            "newline_normalization": "CRLF and CR become LF before parsing and hashing",
            "path_format": "repository-relative POSIX",
            "ordering": "paths, modules, edges, candidates, SCCs, and JSON keys are sorted",
        },
        "inventory": {
            "module_count": len(shipped_paths),
            "modules": [analyses[path]["record"] for path in shipped_paths],
        },
        "imports": {
            "edges": edges,
            "module_graph": graph_records,
            "sccs": _strongly_connected_components(shipped_paths, graph_records),
        },
        "state": {
            "mutable_globals": mutable_globals,
            "owner_candidates": owner_candidates,
        },
        "side_effects": {
            "candidates": side_effects,
        },
        "public_surface": _public_surface(analyses["__init__.py"], edges),
        "registry": {
            "package_root": ".",
            "ignore_file": ".comfyignore",
            "ignore_file_normalized_git_blob_sha1": _normalized_git_blob_sha1(ignore_bytes),
            "entry_modules": ["__init__.py"],
            "shipped_python_modules": shipped_paths,
            "runtime_import_closure": closure,
            "unreachable_shipped_python_modules": sorted(set(shipped_paths) - closure_set),
            "missing_internal_imports": [
                _edge_summary(edge)
                for edge in closure_edges
                if edge["classification"] == "missing_internal"
            ],
            "external_imports": [
                _edge_summary(edge)
                for edge in closure_edges
                if edge["classification"] == "external"
            ],
            "optional_imports": [
                _edge_summary(edge)
                for edge in closure_edges
                if edge["optional"]
            ],
        },
    }
    return report


def analyze_repository(root: Path = REPOSITORY_ROOT) -> dict[str, object]:
    root = root.resolve()
    ignore_path = root / ".comfyignore"
    ignore_bytes = ignore_path.read_bytes()
    rules = _ignore_rules(_decode_source(ignore_bytes))
    sources = {}
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        if _is_ignored(relative, rules):
            continue
        sources[relative] = path.read_bytes()
    return analyze_source_set(sources, comfyignore=ignore_bytes)


def render_json(report: Mapping[str, object]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_text(report: Mapping[str, object]) -> str:
    lines = [
        f"Python backend inventory schema {report['schema_version']}",
        "",
        "[modules]",
    ]
    for module in report["inventory"]["modules"]:
        top_level = module["top_level"]
        lines.append(
            f"{module['path']} | module={module['module']} | loc={module['loc']} | "
            f"functions={top_level['function_count']} | classes={top_level['class_count']} | "
            f"globals={top_level['global_count']}"
        )

    lines.extend(("", "[edges]"))
    for edge in report["imports"]["edges"]:
        target = edge.get("target", edge["imported"])
        flags = [str(edge["classification"]), str(edge["kind"])]
        if edge["optional"]:
            flags.append("optional")
        if edge["conditional"]:
            flags.append("conditional")
        lines.append(f"{edge['source']}:{edge['line']} -> {target} | {', '.join(flags)}")

    lines.extend(("", "[scc]"))
    for component in report["imports"]["sccs"]:
        marker = "cycle" if component["cyclic"] else "acyclic"
        lines.append(f"{marker} | {', '.join(component['modules'])}")

    lines.extend(("", "[state.mutable_globals]"))
    for item in report["state"]["mutable_globals"]:
        lines.append(f"{item['module']}:{item['line']} {item['name']} | {item['kind']}")

    lines.extend(("", "[state.owner_candidates]"))
    for item in report["state"]["owner_candidates"]:
        lines.append(
            f"{item['module']}:{item['line']} {item['name']} | "
            f"{', '.join(item['categories'])} | {item['initializer']}"
        )

    lines.extend(("", "[side_effects]"))
    for item in report["side_effects"]["candidates"]:
        lines.append(
            f"{item['module']}:{item['line']} {item['callee']} | "
            f"{item['kind']} | {item['context']}"
        )

    lines.extend(("", "[public_surface]"))
    lines.append(f"declared_all: {', '.join(report['public_surface']['declared_all'])}")
    lines.append(
        f"compatibility_names: {', '.join(report['public_surface']['compatibility_names'])}"
    )

    registry = report["registry"]
    lines.extend(("", "[registry]"))
    lines.append(f"entry_modules: {', '.join(registry['entry_modules'])}")
    lines.append(f"shipped_python_modules: {len(registry['shipped_python_modules'])}")
    lines.append(f"runtime_import_closure: {len(registry['runtime_import_closure'])}")
    lines.append(
        f"unreachable_shipped_python_modules: "
        f"{', '.join(registry['unreachable_shipped_python_modules']) or '<none>'}"
    )
    lines.append(f"missing_internal_imports: {len(registry['missing_internal_imports'])}")
    lines.append(f"external_imports: {len(registry['external_imports'])}")
    lines.append(f"optional_imports: {len(registry['optional_imports'])}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    report = analyze_repository(args.root)
    rendered = render_json(report) if args.format == "json" else render_text(report)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
