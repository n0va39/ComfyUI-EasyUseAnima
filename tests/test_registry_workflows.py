from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLISH_WORKFLOW = ROOT / ".github" / "workflows" / "publish_action.yml"
METADATA_WORKFLOW = ROOT / ".github" / "workflows" / "registry_metadata.yml"
WORKFLOWS = (PUBLISH_WORKFLOW, METADATA_WORKFLOW)

CHECKOUT_PIN = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1"
SETUP_UV_PIN = "astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d # v10.0.1"
COMFY_CLI_SPEC = "comfy-cli==1.20.0"
REGISTRY_SECRET_EXPRESSION = "${{ secrets.REGISTRY_ACCESS_TOKEN }}"
VERSION_INPUT_REFERENCE = re.compile(
    r"(?:github\.event\.)?inputs(?:\.version|\[\s*['\"]version['\"]\s*\])"
)


def _mapping_block(document: str, key: str, indent: int) -> str:
    header = re.compile(rf"(?m)^{' ' * indent}{re.escape(key)}:\s*$")
    matches = list(header.finditer(document))
    if len(matches) != 1:
        raise ValueError(f"expected one {key!r} mapping at indent {indent}, found {len(matches)}")

    lines = document[matches[0].start() :].splitlines(keepends=True)
    end = len(lines)
    for index, line in enumerate(lines[1:], start=1):
        if not line.strip():
            continue
        line_indent = len(line) - len(line.lstrip(" "))
        if line_indent <= indent:
            end = index
            break
    return "".join(lines[:end])


def _direct_mapping(block: str, indent: int) -> dict[str, str]:
    pattern = re.compile(rf"^{' ' * indent}([A-Za-z0-9_-]+):(?:\s*(.*))?$")
    values: dict[str, str] = {}
    for line in block.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        key, value = match.groups()
        if key in values:
            raise ValueError(f"duplicate mapping key {key!r} at indent {indent}")
        values[key] = value or ""
    return values


def _step_blocks(workflow: str) -> list[tuple[str | None, str]]:
    matches = list(re.finditer(r"(?m)^      - .+$", workflow))
    blocks: list[tuple[str | None, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(workflow)
        block = workflow[match.start() : end]
        name_match = re.match(r"^      - name: (.+)$", block.splitlines()[0])
        blocks.append((name_match.group(1) if name_match else None, block))
    return blocks


def _named_steps(workflow: str) -> dict[str, str]:
    named: dict[str, str] = {}
    for name, block in _step_blocks(workflow):
        if name is None:
            continue
        if name in named:
            raise ValueError(f"duplicate step name {name!r}")
        named[name] = block
    return named


def _step_uses(block: str) -> str | None:
    match = re.search(r"(?m)^\s+(?:-\s+)?uses:\s*([^\s#]+)", block)
    return match.group(1) if match else None


def _run_blocks(workflow: str) -> list[str]:
    lines = workflow.splitlines(keepends=True)
    blocks: list[str] = []
    for start, line in enumerate(lines):
        match = re.match(r"^(?P<indent> +)(?:-\s+)?run:\s*.*$", line)
        if not match:
            continue
        indent = len(match.group("indent"))
        end = len(lines)
        for index in range(start + 1, len(lines)):
            candidate = lines[index]
            if not candidate.strip():
                continue
            candidate_indent = len(candidate) - len(candidate.lstrip(" "))
            if candidate_indent <= indent:
                end = index
                break
        blocks.append("".join(lines[start:end]))
    return blocks


class RegistryWorkflowTests(unittest.TestCase):
    def test_parser_covers_inline_step_mappings(self) -> None:
        inline_checkout = f"      - uses: actions/checkout@{'a' * 40}\n"
        self.assertEqual(_step_uses(inline_checkout), f"actions/checkout@{'a' * 40}")

        inline_run = "      - run: echo '${{inputs.version}}'\n"
        self.assertEqual(_run_blocks(inline_run), [inline_run])
        self.assertIsNotNone(VERSION_INPUT_REFERENCE.search(_run_blocks(inline_run)[0]))

    def test_workflows_keep_manual_read_only_checkout_boundary(self) -> None:
        for path in WORKFLOWS:
            with self.subTest(path=path.name):
                workflow = path.read_text(encoding="utf-8")
                on_mapping = _direct_mapping(_mapping_block(workflow, "on", 0), 2)
                self.assertEqual(list(on_mapping), ["workflow_dispatch"])

                permissions = _direct_mapping(
                    _mapping_block(workflow, "permissions", 0),
                    2,
                )
                self.assertEqual(permissions, {"contents": "read"})

                jobs = _direct_mapping(_mapping_block(workflow, "jobs", 0), 2)
                self.assertTrue(jobs)
                for job_name in jobs:
                    job = _mapping_block(workflow, job_name, 2)
                    self.assertNotRegex(job, r"(?m)^    permissions:")

                self.assertIn(CHECKOUT_PIN, workflow)
                action_refs = re.findall(r"(?m)^\s+uses: [^@\s]+@([^\s#]+)", workflow)
                self.assertTrue(action_refs)
                self.assertTrue(
                    all(re.fullmatch(r"[0-9a-f]{40}", ref) for ref in action_refs),
                    action_refs,
                )

                checkout_steps = [
                    block
                    for _, block in _step_blocks(workflow)
                    if (_step_uses(block) or "").startswith("actions/checkout@")
                ]
                self.assertEqual(len(checkout_steps), 1)
                checkout_options = _direct_mapping(
                    _mapping_block(checkout_steps[0], "with", 8),
                    10,
                )
                self.assertEqual(checkout_options.get("persist-credentials"), "false")

    def test_publish_tools_are_reviewed_immutable_versions(self) -> None:
        workflow = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(SETUP_UV_PIN, workflow)
        setup_uv = _named_steps(workflow)["Install uv"]
        setup_options = _direct_mapping(_mapping_block(setup_uv, "with", 8), 10)
        self.assertEqual(
            setup_options,
            {"version": "latest-known", "enable-cache": "false"},
        )
        self.assertEqual(workflow.count(f"--from {COMFY_CLI_SPEC}"), 2)
        self.assertNotIn("--from comfy-cli comfy", workflow)

    def test_free_form_version_input_remains_data_not_shell_source(self) -> None:
        workflow = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        extract = _named_steps(workflow)["Extract Registry changelog"]
        extract_env = _direct_mapping(_mapping_block(extract, "env", 8), 10)
        self.assertEqual(extract_env, {"RELEASE_VERSION": "${{ inputs.version }}"})
        self.assertIn('--version "$RELEASE_VERSION"', extract)
        self.assertEqual(VERSION_INPUT_REFERENCE.findall(workflow), ["inputs.version"])
        for run_block in _run_blocks(workflow):
            self.assertIsNone(VERSION_INPUT_REFERENCE.search(run_block), run_block)

    def test_registry_secret_is_absent_from_dry_run_steps(self) -> None:
        publish_workflow = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        metadata_workflow = METADATA_WORKFLOW.read_text(encoding="utf-8")
        publish_steps = _named_steps(publish_workflow)
        metadata_steps = _named_steps(metadata_workflow)

        for name, block in (
            ("Preview existing Registry metadata", publish_steps["Preview existing Registry metadata"]),
            ("Preview metadata sync", metadata_steps["Preview metadata sync"]),
        ):
            with self.subTest(step=name):
                self.assertIn("--dry-run true", block)
                self.assertNotIn("REGISTRY_ACCESS_TOKEN", block)

        for name, block in (
            ("Apply existing Registry metadata", publish_steps["Apply existing Registry metadata"]),
            ("Apply metadata sync", metadata_steps["Apply metadata sync"]),
        ):
            with self.subTest(step=name):
                self.assertIn("--dry-run false", block)
                env = _direct_mapping(_mapping_block(block, "env", 8), 10)
                self.assertEqual(
                    env,
                    {"REGISTRY_ACCESS_TOKEN": REGISTRY_SECRET_EXPRESSION},
                )

        allowed_secret_steps = {
            PUBLISH_WORKFLOW: {"Publish Custom Node", "Apply existing Registry metadata"},
            METADATA_WORKFLOW: {"Apply metadata sync"},
        }
        for path, workflow in (
            (PUBLISH_WORKFLOW, publish_workflow),
            (METADATA_WORKFLOW, metadata_workflow),
        ):
            with self.subTest(path=path.name):
                steps = _named_steps(workflow)
                allowed_names = allowed_secret_steps[path]
                self.assertEqual(
                    len(re.findall(r"\bsecrets(?:\.|\[)", workflow)),
                    len(allowed_names),
                )
                self.assertEqual(workflow.count(REGISTRY_SECRET_EXPRESSION), len(allowed_names))
                for name, block in steps.items():
                    if name in allowed_names:
                        env = _direct_mapping(_mapping_block(block, "env", 8), 10)
                        self.assertEqual(
                            env,
                            {"REGISTRY_ACCESS_TOKEN": REGISTRY_SECRET_EXPRESSION},
                        )
                    else:
                        self.assertNotIn(REGISTRY_SECRET_EXPRESSION, block, name)

        metadata_blocks = [
            block
            for name, block in (*publish_steps.items(), *metadata_steps.items())
            if name.startswith(("Preview", "Apply"))
        ]
        self.assertNotIn("${{ inputs.dry_run }}", "\n".join(metadata_blocks))


if __name__ == "__main__":
    unittest.main()
