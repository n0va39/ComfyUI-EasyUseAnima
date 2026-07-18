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
import hashlib
import json
import re
from collections import deque
from pathlib import Path
from typing import Iterable, Mapping, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ROOT_MODULE = "__root__"
SCHEMA_VERSION = 2
DYNAMIC_IMPORT_CALLEES = frozenset({"__import__", "importlib.import_module"})
MUTABLE_CONSTRUCTORS = {
    "ChainMap": "dict",
    "Counter": "dict",
    "OrderedDict": "dict",
    "UserDict": "dict",
    "UserList": "list",
    "defaultdict": "dict",
    "deque": "list",
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


def _strip_unescaped_trailing_spaces(line: str) -> str:
    while line.endswith(" ") and not line.endswith("\\ "):
        line = line[:-1]
    return line.replace("\\ ", " ")


def _ignore_rules(ignore_text: str) -> list[dict[str, object]]:
    rules = []
    for line_number, raw_line in enumerate(ignore_text.splitlines(), start=1):
        line = _strip_unescaped_trailing_spaces(raw_line)
        if not line:
            continue
        escaped_marker = line.startswith((r"\#", r"\!"))
        if line.startswith("#") and not escaped_marker:
            continue
        negated = line.startswith("!") and not escaped_marker
        pattern = line[1:] if negated or escaped_marker else line
        directory_only = pattern.endswith("/")
        pattern = pattern.rstrip("/")
        anchored = pattern.startswith("/")
        pattern = pattern[1:] if anchored else pattern
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


def _glob_regex(pattern: str) -> re.Pattern[str]:
    pieces = ["^"]
    index = 0
    while index < len(pattern):
        character = pattern[index]
        if character == "\\" and index + 1 < len(pattern):
            index += 1
            pieces.append(re.escape(pattern[index]))
        elif pattern.startswith("**/", index):
            pieces.append("(?:.*/)?")
            index += 2
        elif pattern.startswith("**", index):
            pieces.append(".*")
            index += 1
        elif character == "*":
            pieces.append("[^/]*")
        elif character == "?":
            pieces.append("[^/]")
        elif character == "[":
            closing = pattern.find("]", index + 1)
            if closing == -1:
                pieces.append(r"\[")
            else:
                content = pattern[index + 1 : closing]
                if content.startswith("!"):
                    content = "^" + content[1:]
                elif content.startswith("^"):
                    content = "\\" + content
                pieces.append(f"(?!/)[{content}]")
                index = closing
        else:
            pieces.append(re.escape(character))
        index += 1
    pieces.append("$")
    return re.compile("".join(pieces))


def _match_path_pattern(path: str, pattern: str) -> bool:
    return bool(_glob_regex(pattern).fullmatch(path))


def _rule_matches(
    path: str,
    rule: Mapping[str, object],
    *,
    is_directory: bool,
) -> bool:
    parts = path.split("/")
    pattern = str(rule["pattern"])
    anchored = bool(rule["anchored"])
    directory_only = bool(rule["directory_only"])
    candidates = []
    for length in range(1, len(parts) + 1):
        candidate_is_directory = length < len(parts) or is_directory
        if directory_only and not candidate_is_directory:
            continue
        candidate = "/".join(parts[:length])
        candidates.append((candidate, candidate.rsplit("/", 1)[-1]))
    if anchored or "/" in pattern:
        return any(_match_path_pattern(candidate, pattern) for candidate, _ in candidates)
    return any(_match_path_pattern(basename, pattern) for _, basename in candidates)


def _is_ignored(
    path: str,
    rules: Sequence[Mapping[str, object]],
    *,
    is_directory: bool = False,
) -> bool:
    ignored = False
    for index, rule in enumerate(rules):
        if not _rule_matches(path, rule, is_directory=is_directory):
            continue
        if not bool(rule["negated"]):
            ignored = True
            continue
        parent_parts = path.split("/")[:-1]
        parent_is_ignored = any(
            _is_ignored(
                "/".join(parent_parts[:length]),
                rules[:index],
                is_directory=True,
            )
            for length in range(1, len(parent_parts) + 1)
        )
        if not parent_is_ignored:
            ignored = False
    return ignored


def _handler_exception_names(handler_type: ast.AST | None) -> list[str]:
    if handler_type is None:
        return ["<bare>"]
    nodes = handler_type.elts if isinstance(handler_type, ast.Tuple) else [handler_type]
    return sorted(
        {
            _call_name(node).rsplit(".", 1)[-1] or "<expression>"
            for node in nodes
        }
    )


def _catches_import_error(handler_type: ast.AST | None) -> bool:
    names = set(_handler_exception_names(handler_type))
    return bool(names & {"<bare>", "ImportError", "ModuleNotFoundError"})


def _catches_import_failure(handler_type: ast.AST | None) -> bool:
    names = set(_handler_exception_names(handler_type))
    return bool(
        names
        & {
            "<bare>",
            "BaseException",
            "Exception",
            "ImportError",
            "ModuleNotFoundError",
        }
    )


def _is_type_checking_test(node: ast.AST) -> bool:
    return _call_name(node).rsplit(".", 1)[-1] == "TYPE_CHECKING"


class _FunctionLocalBindingVisitor(ast.NodeVisitor):
    """Find names statically local to one function without entering nested scopes."""

    def __init__(self) -> None:
        self.names: set[str] = set()
        self.global_names: set[str] = set()
        self.nonlocal_names: set[str] = set()

    def _add_target(self, target: ast.AST) -> None:
        self.names.update(_assigned_names(target))

    def visit_Global(self, node: ast.Global) -> None:
        self.global_names.update(node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self.nonlocal_names.update(node.names)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.names.add(node.name)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.names.add(node.name)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.names.add(node.name)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return None

    def visit_Import(self, node: ast.Import) -> None:
        self.names.update(
            alias.asname or alias.name.split(".", 1)[0]
            for alias in node.names
        )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.names.update(
            alias.asname or alias.name
            for alias in node.names
            if alias.name != "*"
        )

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._add_target(target)
        self.visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._add_target(node.target)
        if node.value:
            self.visit(node.value)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._add_target(node.target)
        self.visit(node.value)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        self._add_target(node.target)
        self.visit(node.value)

    def visit_For(self, node: ast.For) -> None:
        self._add_target(node.target)
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.visit_For(node)

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            if item.optional_vars:
                self._add_target(item.optional_vars)
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self.visit_With(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self.names.add(node.name)
        self.generic_visit(node)


def _function_local_names(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> set[str]:
    visitor = _FunctionLocalBindingVisitor()
    for statement in node.body:
        visitor.visit(statement)
    return visitor.names - visitor.global_names - visitor.nonlocal_names


def _lambda_local_names(node: ast.Lambda) -> set[str]:
    visitor = _FunctionLocalBindingVisitor()
    visitor.visit(node.body)
    return visitor.names - visitor.global_names - visitor.nonlocal_names


def _argument_names(arguments: ast.arguments) -> set[str]:
    names = {
        argument.arg
        for argument in (
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
        )
    }
    if arguments.vararg:
        names.add(arguments.vararg.arg)
    if arguments.kwarg:
        names.add(arguments.kwarg.arg)
    return names


class _ImportCandidateVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.candidates: list[dict[str, object]] = []
        self.scope_parts: list[str] = []
        self.alias_scopes: list[dict[str, set[str] | None]] = [{}]
        self.alias_scope_kinds = ["module"]
        self.branch_context: list[dict[str, object]] = []

    @property
    def scope(self) -> str:
        return ".".join(self.scope_parts) if self.scope_parts else "<module>"

    def _bind_alias(self, name: str, target: str) -> None:
        self.alias_scopes[-1][name] = {target}

    def _shadow_names(self, names: Iterable[str]) -> None:
        for name in names:
            self.alias_scopes[-1][name] = None

    def _resolve_callee_aliases(self, callee: str) -> set[str]:
        resolved = {callee}
        root, separator, suffix = callee.partition(".")
        crossed_function_scope = False
        for aliases, scope_kind in zip(
            reversed(self.alias_scopes),
            reversed(self.alias_scope_kinds),
        ):
            if scope_kind in {"function", "lambda"}:
                crossed_function_scope = True
            elif scope_kind == "class" and crossed_function_scope:
                continue
            if root not in aliases:
                continue
            targets = aliases[root]
            if targets:
                resolved.update(
                    f"{target}.{suffix}" if separator else target
                    for target in targets
                )
            break
        return resolved

    def _push_branch(self, context: dict[str, object]) -> None:
        self.branch_context.append(context)

    def _pop_branch(self) -> None:
        self.branch_context.pop()

    def _optional_candidate(self) -> bool:
        for context in self.branch_context:
            if (
                context["kind"] == "try"
                and context["branch"] == "body"
                and context.get("handles_import_failure")
            ):
                return True
            if (
                context["kind"] == "if"
                and context["branch"] == "body"
                and context.get("type_checking")
            ):
                return True
        return False

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
                "branch_context": [dict(item) for item in self.branch_context],
                "optional_candidate": self._optional_candidate(),
                "conditional": bool(self.branch_context),
            }
        )

    def _visit_function_definition_expressions(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)
        arguments = (
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
        )
        for argument in arguments:
            if argument.annotation:
                self.visit(argument.annotation)
        if node.args.vararg and node.args.vararg.annotation:
            self.visit(node.args.vararg.annotation)
        if node.args.kwarg and node.args.kwarg.annotation:
            self.visit(node.args.kwarg.annotation)
        if node.returns:
            self.visit(node.returns)
        for default in (
            *node.args.defaults,
            *[item for item in node.args.kw_defaults if item],
        ):
            self.visit(default)

    def _visit_function_body(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        self.scope_parts.append(node.name)
        local_names = _argument_names(node.args) | _function_local_names(node)
        self.alias_scopes.append({name: None for name in local_names})
        self.alias_scope_kinds.append("function")
        for statement in node.body:
            self.visit(statement)
        self.alias_scope_kinds.pop()
        self.alias_scopes.pop()
        self.scope_parts.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function_definition_expressions(node)
        self._shadow_names([node.name])
        self._visit_function_body(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function_definition_expressions(node)
        self._shadow_names([node.name])
        self._visit_function_body(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        for default in (
            *node.args.defaults,
            *[item for item in node.args.kw_defaults if item],
        ):
            self.visit(default)
        self.scope_parts.append(f"<lambda>@{node.lineno}")
        local_names = _argument_names(node.args) | _lambda_local_names(node)
        self.alias_scopes.append({name: None for name in local_names})
        self.alias_scope_kinds.append("lambda")
        self.visit(node.body)
        self.alias_scope_kinds.pop()
        self.alias_scopes.pop()
        self.scope_parts.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)
        for base in node.bases:
            self.visit(base)
        for keyword in node.keywords:
            self.visit(keyword.value)
        self.scope_parts.append(node.name)
        self.alias_scopes.append({})
        self.alias_scope_kinds.append("class")
        for statement in node.body:
            self.visit(statement)
        self.alias_scope_kinds.pop()
        self.alias_scopes.pop()
        self.scope_parts.pop()
        self._shadow_names([node.name])

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._append(
                node=node,
                kind="static_import",
                requested=alias.name,
                name=None,
                alias=alias.asname,
            )
            if alias.asname:
                self._bind_alias(alias.asname, alias.name)
            else:
                root_name = alias.name.split(".", 1)[0]
                self._bind_alias(root_name, root_name)

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
            if alias.name != "*":
                if requested.endswith("."):
                    target = f"{requested}{alias.name}"
                elif requested:
                    target = f"{requested}.{alias.name}"
                else:
                    target = alias.name
                self._bind_alias(alias.asname or alias.name, target)

    def visit_Call(self, node: ast.Call) -> None:
        callee = _call_name(node.func)
        if self._resolve_callee_aliases(callee).intersection(DYNAMIC_IMPORT_CALLEES):
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                self._append(
                    node=node,
                    kind="literal_dynamic",
                    requested=node.args[0].value,
                    name=None,
                    alias=None,
                )
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        self.visit(node.value)
        self._shadow_names(
            name
            for target in node.targets
            for name in _assigned_names(target)
        )

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value:
            self.visit(node.value)
        self._shadow_names(_assigned_names(node.target))

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self.visit(node.value)
        self._shadow_names(_assigned_names(node.target))

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        self.visit(node.value)
        self._shadow_names(_assigned_names(node.target))

    def visit_For(self, node: ast.For) -> None:
        self.visit(node.iter)
        self._shadow_names(_assigned_names(node.target))
        for statement in (*node.body, *node.orelse):
            self.visit(statement)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.visit_For(node)

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            self.visit(item.context_expr)
            if item.optional_vars:
                self._shadow_names(_assigned_names(item.optional_vars))
        for statement in node.body:
            self.visit(statement)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self.visit_With(node)

    def visit_Try(self, node: ast.Try) -> None:
        catches_import_error = any(
            _catches_import_error(handler.type) for handler in node.handlers
        )
        handles_import_failure = any(
            _catches_import_failure(handler.type) for handler in node.handlers
        )
        self._push_branch(
            {
                "kind": "try",
                "line": node.lineno,
                "branch": "body",
                "handles_import_failure": handles_import_failure,
                "has_import_fallback_handler": catches_import_error,
            }
        )
        for statement in node.body:
            self.visit(statement)
        self._pop_branch()
        for handler in node.handlers:
            self._push_branch(
                {
                    "kind": "try",
                    "line": node.lineno,
                    "branch": "except",
                    "handler_line": handler.lineno,
                    "exceptions": _handler_exception_names(handler.type),
                    "catches_import_error": _catches_import_error(handler.type),
                }
            )
            for statement in handler.body:
                self.visit(statement)
            self._pop_branch()
        self._push_branch(
            {"kind": "try", "line": node.lineno, "branch": "else"}
        )
        for statement in node.orelse:
            self.visit(statement)
        self._pop_branch()
        self._push_branch(
            {"kind": "try", "line": node.lineno, "branch": "finally"}
        )
        for statement in node.finalbody:
            self.visit(statement)
        self._pop_branch()

    visit_TryStar = visit_Try

    def visit_If(self, node: ast.If) -> None:
        self.visit(node.test)
        type_checking = _is_type_checking_test(node.test)
        self._push_branch(
            {
                "kind": "if",
                "line": node.lineno,
                "branch": "body",
                "type_checking": type_checking,
            }
        )
        for statement in node.body:
            self.visit(statement)
        self._pop_branch()
        self._push_branch(
            {
                "kind": "if",
                "line": node.lineno,
                "branch": "else",
                "type_checking": type_checking,
            }
        )
        for statement in node.orelse:
            self.visit(statement)
        self._pop_branch()


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


class _ModuleAssignmentVisitor(ast.NodeVisitor):
    """Collect assignments executed in module control flow, excluding local scopes."""

    def __init__(self) -> None:
        self.assignments: list[tuple[str, int, ast.AST | None]] = []

    def _append(self, target: ast.AST, line: int, value: ast.AST | None) -> None:
        self.assignments.extend(
            (name, line, value)
            for name in _assigned_names(target)
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        return None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        return None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        return None

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return None

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._append(target, node.lineno, node.value)
        self.visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._append(node.target, node.lineno, node.value)
        if node.value:
            self.visit(node.value)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._append(node.target, node.lineno, node.value)
        self.visit(node.value)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        self._append(node.target, node.lineno, node.value)
        self.visit(node.value)


def _module_assignments(tree: ast.Module) -> list[tuple[str, int, ast.AST | None]]:
    visitor = _ModuleAssignmentVisitor()
    visitor.visit(tree)
    return visitor.assignments


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

    assignments = _module_assignments(tree)
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

    import_visitor = _ImportCandidateVisitor()
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


def _bound_name(candidate: Mapping[str, object]) -> str | None:
    alias = candidate.get("alias")
    if alias:
        return str(alias)
    imported_name = candidate.get("name")
    if imported_name and imported_name != "*":
        return str(imported_name)
    if candidate["kind"] == "static_import":
        return str(candidate["requested"]).split(".", 1)[0]
    return None


def _nearest_try_context(
    edge: Mapping[str, object],
    branch: str,
) -> Mapping[str, object] | None:
    for context in reversed(edge["branch_context"]):
        if context["kind"] == "try" and context["branch"] == branch:
            return context
    return None


def _absolute_local_target(
    edge: Mapping[str, object],
    path_by_internal_name: Mapping[str, str],
) -> str | None:
    requested = str(edge["requested"])
    if requested.startswith("."):
        return None
    options = []
    imported_name = edge.get("name")
    if imported_name and imported_name != "*":
        options.append(f"{requested}.{imported_name}")
    options.append(requested)
    return next(
        (
            path_by_internal_name[option]
            for option in options
            if option in path_by_internal_name
        ),
        None,
    )


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
        "bound_name": _bound_name(candidate),
        "branch_context": candidate["branch_context"],
        "optional": bool(candidate["optional_candidate"]),
        "conditional": bool(candidate["conditional"]),
        "classification": classification,
        "role": (
            "optional_dependency"
            if candidate["optional_candidate"]
            else "ordinary"
        ),
    }
    if target is not None:
        edge["target"] = target
    return edge


def _classify_compatibility_fallbacks(
    edges: list[dict[str, object]],
    *,
    path_by_internal_name: Mapping[str, str],
) -> None:
    primary_by_key: dict[
        tuple[str, str, int, str, str],
        list[dict[str, object]],
    ] = {}
    for edge in edges:
        context = _nearest_try_context(edge, "body")
        bound_name = edge.get("bound_name")
        target = edge.get("target")
        if (
            edge["classification"] != "internal"
            or not str(edge["requested"]).startswith(".")
            or context is None
            or not context.get("has_import_fallback_handler")
            or not bound_name
            or not target
        ):
            continue
        key = (
            str(edge["source"]),
            str(edge["scope"]),
            int(context["line"]),
            str(bound_name),
            str(target),
        )
        primary_by_key.setdefault(key, []).append(edge)

    for fallback in edges:
        context = _nearest_try_context(fallback, "except")
        bound_name = fallback.get("bound_name")
        if (
            fallback["classification"] != "external"
            or context is None
            or not context.get("catches_import_error")
            or not bound_name
        ):
            continue
        target = _absolute_local_target(fallback, path_by_internal_name)
        if target is None:
            continue
        key = (
            str(fallback["source"]),
            str(fallback["scope"]),
            int(context["line"]),
            str(bound_name),
            target,
        )
        primaries = primary_by_key.get(key)
        if not primaries:
            continue
        pair = {
            "try_line": int(context["line"]),
            "bound_name": str(bound_name),
            "target": target,
        }
        fallback.update(
            {
                "classification": "compatibility_fallback",
                "target": target,
                "role": "compatibility_fallback",
                "optional": False,
                "compatibility_pair": pair,
            }
        )
        for primary in primaries:
            primary.update(
                {
                    "role": "compatibility_primary",
                    "optional": False,
                    "compatibility_pair": pair,
                }
            )


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
        "role": edge["role"],
        "optional": edge["optional"],
        "conditional": edge["conditional"],
        "branch_context": edge["branch_context"],
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
    _classify_compatibility_fallbacks(
        edges,
        path_by_internal_name=path_by_internal_name,
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
            if edge["classification"]
            in {"compatibility_fallback", "internal"}
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
            "dynamic_alias_policy": {
                "lexical_scopes": (
                    "module, class, function, and lambda bindings are tracked; "
                    "class namespaces are skipped for nested function lookup"
                ),
                "control_flow_merge": (
                    "if/try branch bindings are visited in deterministic source order; "
                    "conflicting branch aliases remain heuristic"
                ),
            },
            "module_graph_policy": {
                "included_classifications": [
                    "compatibility_fallback",
                    "internal",
                ],
                "duplicate_policy": "collapse by source and target path",
            },
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
            "compatibility_fallback_imports": [
                _edge_summary(edge)
                for edge in closure_edges
                if edge["classification"] == "compatibility_fallback"
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


def _render_branch_context(contexts: Sequence[Mapping[str, object]]) -> str:
    labels = []
    for context in contexts:
        label = f"{context['kind']}@{context['line']}:{context['branch']}"
        exceptions = context.get("exceptions")
        if exceptions:
            label += f"[{','.join(str(item) for item in exceptions)}]"
        labels.append(label)
    return " > ".join(labels) if labels else "module"


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
        flags = [
            str(edge["classification"]),
            str(edge["role"]),
            str(edge["kind"]),
        ]
        if edge["optional"]:
            flags.append("optional")
        if edge["conditional"]:
            flags.append("conditional")
        lines.append(
            f"{edge['source']}:{edge['line']} -> {target} | "
            f"{', '.join(flags)} | {_render_branch_context(edge['branch_context'])}"
        )

    lines.extend(("", "[scc]"))
    for component in report["imports"]["sccs"]:
        marker = "cycle" if component["cyclic"] else "acyclic"
        lines.append(f"{marker} | {', '.join(component['modules'])}")

    alias_policy = report["imports"]["dynamic_alias_policy"]
    lines.extend(("", "[analysis_policy]"))
    lines.append(f"dynamic_alias_lexical_scopes: {alias_policy['lexical_scopes']}")
    lines.append(f"dynamic_alias_control_flow: {alias_policy['control_flow_merge']}")

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
    lines.append(
        f"compatibility_fallback_imports: "
        f"{len(registry['compatibility_fallback_imports'])}"
    )
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
