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


def _step_blocks(workflow: str) -> dict[str, str]:
    matches = list(re.finditer(r"(?m)^      - name: (?P<name>.+)$", workflow))
    blocks: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(workflow)
        blocks[match.group("name")] = workflow[match.start() : end]
    return blocks


class RegistryWorkflowTests(unittest.TestCase):
    def test_workflows_keep_manual_read_only_checkout_boundary(self) -> None:
        for path in WORKFLOWS:
            with self.subTest(path=path.name):
                workflow = path.read_text(encoding="utf-8")
                self.assertRegex(workflow, r"(?m)^on:\n  workflow_dispatch:\n")
                self.assertNotRegex(
                    workflow,
                    r"(?m)^  (?:push|pull_request|pull_request_target|schedule|workflow_run):",
                )
                self.assertIn("permissions:\n  contents: read\n", workflow)
                self.assertNotRegex(workflow, r"(?m)^permissions:\s+(?:write-all|read-all)$")
                self.assertNotRegex(workflow, r"(?m)^  [a-z-]+: write$")
                self.assertIn(CHECKOUT_PIN, workflow)
                action_refs = re.findall(r"(?m)^\s+uses: [^@\s]+@([^\s#]+)", workflow)
                self.assertTrue(action_refs)
                self.assertTrue(
                    all(re.fullmatch(r"[0-9a-f]{40}", ref) for ref in action_refs),
                    action_refs,
                )

                checkout = _step_blocks(workflow)["Check out code"]
                self.assertIn("persist-credentials: false", checkout)

    def test_publish_tools_are_reviewed_immutable_versions(self) -> None:
        workflow = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(SETUP_UV_PIN, workflow)
        setup_uv = _step_blocks(workflow)["Install uv"]
        self.assertIn("version: latest-known", setup_uv)
        self.assertIn("enable-cache: false", setup_uv)
        self.assertEqual(workflow.count(f"--from {COMFY_CLI_SPEC}"), 2)
        self.assertNotIn("--from comfy-cli comfy", workflow)

    def test_free_form_version_input_remains_data_not_shell_source(self) -> None:
        workflow = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        extract = _step_blocks(workflow)["Extract Registry changelog"]
        self.assertIn("RELEASE_VERSION: ${{ inputs.version }}", extract)
        self.assertIn('--version "$RELEASE_VERSION"', extract)
        self.assertNotIn('--version "${{ inputs.version }}"', extract)

    def test_registry_secret_is_absent_from_dry_run_steps(self) -> None:
        publish_steps = _step_blocks(PUBLISH_WORKFLOW.read_text(encoding="utf-8"))
        metadata_steps = _step_blocks(METADATA_WORKFLOW.read_text(encoding="utf-8"))

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
                self.assertIn(
                    "REGISTRY_ACCESS_TOKEN: ${{ secrets.REGISTRY_ACCESS_TOKEN }}",
                    block,
                )

        self.assertNotIn("${{ inputs.dry_run }}", "\n".join(
            block
            for name, block in (*publish_steps.items(), *metadata_steps.items())
            if name.startswith(("Preview", "Apply"))
        ))


if __name__ == "__main__":
    unittest.main()
