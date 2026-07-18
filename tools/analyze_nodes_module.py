#!/usr/bin/env python3
"""Deterministically describe the monolithic ``nodes.py`` module.

The analyzer is intentionally AST-only.  It never imports the custom node, so it
can be used before ComfyUI, model folders, or optional node packs are available.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Iterable


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPOSITORY_ROOT / "nodes.py"
DEFAULT_INTERNAL_PACKAGE = "easyuse_anima"
DOMAIN_LAYERS = frozenset({"domain", "service", "services"})
OUTER_LAYERS = frozenset({"adapters", "bootstrap", "registration"})
DYNAMIC_LOOKUP_CALLEES = frozenset(
    {
        "__import__",
        "getattr",
        "importlib.import_module",
        "sys.modules.get",
    }
)


def _git_blob_sha1(data: bytes) -> str:
    # The repository stores Python sources with LF even when a Windows checkout
    # materializes CRLF.  Normalize that text boundary so the report matches the
    # repository blob rather than the host checkout representation.
    normalized = data.replace(b"\r\n", b"\n")
    header = f"blob {len(normalized)}\0".encode("ascii")
    return hashlib.sha1(header + normalized).hexdigest()


def _source_label(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPOSITORY_ROOT).as_posix()
    except ValueError:
        # Reports must not disclose paths outside the repository.
        return path.name


def _assigned_names(node: ast.AST) -> Iterable[str]:
    if isinstance(node, ast.Name):
        yield node.id
    elif isinstance(node, (ast.Tuple, ast.List)):
        for item in node.elts:
            yield from _assigned_names(item)


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


class _LocationVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports: list[dict[str, object]] = []
        self.dynamic_lookups: list[dict[str, object]] = []
        self._scope: list[str] = []

    @property
    def scope(self) -> str:
        return ".".join(self._scope) if self._scope else "<module>"

    def _visit_scoped(self, node: ast.AST, name: str) -> None:
        self._scope.append(name)
        self.generic_visit(node)
        self._scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_scoped(node, node.name)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_scoped(node, node.name)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._visit_scoped(node, node.name)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(
                {
                    "kind": "import",
                    "module": alias.name,
                    "name": None,
                    "alias": alias.asname,
                    "line": node.lineno,
                    "column": node.col_offset,
                    "scope": self.scope,
                }
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = "." * node.level + (node.module or "")
        for alias in node.names:
            self.imports.append(
                {
                    "kind": "from",
                    "module": module,
                    "name": alias.name,
                    "alias": alias.asname,
                    "line": node.lineno,
                    "column": node.col_offset,
                    "scope": self.scope,
                }
            )

    def visit_Call(self, node: ast.Call) -> None:
        callee = _call_name(node.func)
        if callee in DYNAMIC_LOOKUP_CALLEES:
            self.dynamic_lookups.append(
                {
                    "callee": callee,
                    "line": node.lineno,
                    "column": node.col_offset,
                    "scope": self.scope,
                }
            )
        self.generic_visit(node)


def _definition_references(node: ast.AST, known_names: set[str]) -> list[str]:
    referenced = {
        child.id
        for child in ast.walk(node)
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load)
    }
    name = getattr(node, "name", None)
    if isinstance(name, str):
        referenced.discard(name)
    return sorted(referenced & known_names)


def analyze_source(source: str, *, source_label: str = "nodes.py", raw_bytes: bytes | None = None) -> dict:
    raw_bytes = raw_bytes if raw_bytes is not None else source.encode("utf-8")
    tree = ast.parse(source, filename=source_label)

    functions: list[dict[str, object]] = []
    classes: list[dict[str, object]] = []
    globals_by_name: dict[str, int] = {}
    definition_nodes: list[ast.AST] = []

    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(
                {
                    "name": statement.name,
                    "line": statement.lineno,
                    "async": isinstance(statement, ast.AsyncFunctionDef),
                }
            )
            definition_nodes.append(statement)
        elif isinstance(statement, ast.ClassDef):
            classes.append({"name": statement.name, "line": statement.lineno})
            definition_nodes.append(statement)
        elif isinstance(statement, ast.Assign):
            for target in statement.targets:
                for name in _assigned_names(target):
                    globals_by_name.setdefault(name, statement.lineno)
        elif isinstance(statement, (ast.AnnAssign, ast.AugAssign)):
            for name in _assigned_names(statement.target):
                globals_by_name.setdefault(name, statement.lineno)

    globals_list = [
        {"name": name, "line": line}
        for name, line in sorted(globals_by_name.items())
    ]
    known_names = {
        *(item["name"] for item in functions),
        *(item["name"] for item in classes),
        *globals_by_name,
    }
    reference_edges = []
    for node in definition_nodes:
        source_name = getattr(node, "name")
        for target_name in _definition_references(node, known_names):
            reference_edges.append({"from": source_name, "to": target_name})

    visitor = _LocationVisitor()
    visitor.visit(tree)
    imports = sorted(
        visitor.imports,
        key=lambda item: (
            int(item["line"]),
            int(item["column"]),
            str(item["module"]),
            str(item["name"]),
        ),
    )
    dynamic_lookups = sorted(
        visitor.dynamic_lookups,
        key=lambda item: (int(item["line"]), int(item["column"]), str(item["callee"])),
    )

    return {
        "schema_version": 1,
        "source": source_label,
        "git_blob_sha1": _git_blob_sha1(raw_bytes),
        "line_count": len(source.splitlines()),
        "top_level": {
            "function_count": len(functions),
            "class_count": len(classes),
            "global_count": len(globals_list),
            "functions": sorted(functions, key=lambda item: (str(item["name"]), int(item["line"]))),
            "classes": sorted(classes, key=lambda item: (str(item["name"]), int(item["line"]))),
            "globals": globals_list,
        },
        "imports": imports,
        "dynamic_lookups": dynamic_lookups,
        "reference_edges": sorted(reference_edges, key=lambda item: (item["from"], item["to"])),
    }


def analyze_path(path: Path) -> dict:
    data = path.read_bytes()
    source = data.decode("utf-8-sig")
    return analyze_source(source, source_label=_source_label(path), raw_bytes=data)


def render_json(report: dict) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_text(report: dict) -> str:
    top_level = report["top_level"]
    lines = [
        f"source: {report['source']}",
        f"git_blob_sha1: {report['git_blob_sha1']}",
        f"line_count: {report['line_count']}",
        f"top_level_functions: {top_level['function_count']}",
        f"top_level_classes: {top_level['class_count']}",
        f"top_level_globals: {top_level['global_count']}",
        "",
        "classes:",
    ]
    lines.extend(f"  {item['name']} @ {item['line']}" for item in top_level["classes"])
    lines.append("")
    lines.append("functions:")
    lines.extend(f"  {item['name']} @ {item['line']}" for item in top_level["functions"])
    lines.append("")
    lines.append("globals:")
    lines.extend(f"  {item['name']} @ {item['line']}" for item in top_level["globals"])
    lines.append("")
    lines.append("imports:")
    for item in report["imports"]:
        imported = item["module"]
        if item["name"]:
            imported = f"{imported}:{item['name']}"
        lines.append(f"  {imported} @ {item['line']} ({item['scope']})")
    lines.append("")
    lines.append("dynamic_lookups:")
    lines.extend(
        f"  {item['callee']} @ {item['line']} ({item['scope']})"
        for item in report["dynamic_lookups"]
    )
    lines.append("")
    lines.append("reference_edges:")
    lines.extend(f"  {item['from']} -> {item['to']}" for item in report["reference_edges"])
    return "\n".join(lines) + "\n"


def _resolve_from_import(
    node: ast.ImportFrom,
    *,
    module_name: str,
    is_package: bool,
) -> str:
    if node.level == 0:
        return node.module or ""
    package_parts = module_name.split(".") if is_package else module_name.split(".")[:-1]
    remove_count = max(0, node.level - 1)
    if remove_count:
        package_parts = package_parts[: max(0, len(package_parts) - remove_count)]
    if node.module:
        package_parts.extend(node.module.split("."))
    return ".".join(package_parts)


def _import_targets(
    tree: ast.AST,
    *,
    module_name: str,
    is_package: bool,
) -> Iterable[tuple[int, str]]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name
        elif isinstance(node, ast.ImportFrom):
            base = _resolve_from_import(node, module_name=module_name, is_package=is_package)
            if base:
                yield node.lineno, base
            for alias in node.names:
                if alias.name != "*":
                    yield node.lineno, f"{base}.{alias.name}" if base else alias.name
        elif isinstance(node, ast.Call) and _call_name(node.func) in {
            "__import__",
            "importlib.import_module",
        }:
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                yield node.lineno, node.args[0].value


def find_import_boundary_violations(
    source: str,
    *,
    module_name: str,
    package_name: str = DEFAULT_INTERNAL_PACKAGE,
    is_package: bool = False,
) -> list[dict[str, object]]:
    """Return stable violations for the future internal package layering rules."""

    tree = ast.parse(source, filename=module_name)
    prefix = f"{package_name}."
    relative_name = module_name[len(prefix) :] if module_name.startswith(prefix) else ""
    source_layer = relative_name.split(".", 1)[0] if relative_name else ""
    violations: set[tuple[str, int, str]] = set()

    for line, target in _import_targets(tree, module_name=module_name, is_package=is_package):
        if target == "nodes" or target.startswith("nodes."):
            violations.add(("internal-imports-root-nodes", line, target))

        if source_layer in DOMAIN_LAYERS:
            for outer_layer in OUTER_LAYERS:
                forbidden = f"{package_name}.{outer_layer}"
                if target == forbidden or target.startswith(f"{forbidden}."):
                    violations.add(("inner-layer-imports-outer-layer", line, target))

    return [
        {"rule": rule, "line": line, "module": module_name, "imported": target}
        for rule, line, target in sorted(violations, key=lambda item: (item[1], item[0], item[2]))
    ]


def scan_internal_package(
    package_root: Path,
    *,
    package_name: str = DEFAULT_INTERNAL_PACKAGE,
) -> list[dict[str, object]]:
    if not package_root.is_dir():
        return []

    violations: list[dict[str, object]] = []
    for path in sorted(package_root.rglob("*.py")):
        relative = path.relative_to(package_root)
        module_parts = list(relative.with_suffix("").parts)
        is_package = bool(module_parts and module_parts[-1] == "__init__")
        if is_package:
            module_parts.pop()
        module_name = ".".join((package_name, *module_parts))
        source = path.read_text(encoding="utf-8-sig")
        for violation in find_import_boundary_violations(
            source,
            module_name=module_name,
            package_name=package_name,
            is_package=is_package,
        ):
            violation["file"] = relative.as_posix()
            violations.append(violation)
    return sorted(
        violations,
        key=lambda item: (str(item["file"]), int(item["line"]), str(item["rule"])),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    report = analyze_path(args.source)
    rendered = render_json(report) if args.format == "json" else render_text(report)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
