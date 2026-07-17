---
name: easyuse-anima-frontend-maintenance
description: Coordinate the active ComfyUI-EasyUseAnima frontend maintenance goal. Use when reconciling the version-controlled execution plan, assigning or receiving a production-lane handoff, advancing a PR through the integration gate, recording Issue evidence, or preparing the final user-instance sync.
---

# EasyUseAnima Frontend Maintenance

## Start From The Ledger

1. Work only in the assigned `codex/*` worktree.
2. Read `docs/development/frontend-maintenance-execution-plan.md` first.
3. Read `docs/development/current-policies.md` and the relevant section of
   `docs/development/frontend-maintenance-roadmap.md`.
4. Treat the execution plan as a checkpoint snapshot, not proof of current Git,
   GitHub, process, or Codex task state. Read those surfaces back before acting.

## Reconcile A Checkpoint

1. Fetch `origin`; record `origin/dev`, local `dev`, dirty state, and worktrees.
2. Read back active PR and Issue state after any GitHub mutation or uncertainty.
3. Read the owning Codex task handoff before touching its branch or worktree.
4. Reconcile task id, branch, worktree, base, HEAD, expected files, evidence,
   findings, next action, and cleanup state in the execution plan.
5. Update the plan at safe checkpoints: lane creation or clean handoff,
   blocker/review-fix resolution, frozen full/browser evidence, PR creation or
   merge read-back, Issue-ledger update or cleanup, and final instance sync.

Only the integration owner edits the shared execution plan and shared runner or
frontend-support files. Do not copy volatile state into this Skill.

## Hand Off A Production Lane

- Use one user-owned Codex task, one `codex/*` branch, and one worktree.
- Base it on the current `origin/dev`; record the exact base SHA and ownership.
- Give it a bounded lifecycle or behavior slice and explicit expected files.
- Keep overlapping production files in one lane. Maximum three production
  lanes may be active.
- A lane implements, runs sandbox-safe focused checks, commits, and leaves a
  clean worktree. It does not run the official full suite, browser/server smoke,
  push, PR, merge, shared-runner edits, or user-instance sync.
- Select each new user-owned Codex task's available model and reasoning level
  from slice complexity, risk, latency, and review needs. Use balanced settings
  for bounded audits or mechanical extractions and higher reasoning for
  intertwined runtime behavior or integration risk; do not default every task
  to `sol`/`max`. Do not claim a speed setting that the task API does not expose.

## Advance The Integration Gate

1. Admit one PR at a time and rebase its exact slice onto current `origin/dev`.
2. Re-run focused checks when the tested code or base changed.
3. Freeze and audit the final diff. The integration owner adds any shared runner
   registration required by the slice.
4. Follow the `$comfyui-codex-test` Skill and the repository runner contract.
   Run the official full profile once for the PR-ready diff.
5. For actual frontend behavior changes, follow
   `docs/development/browser-smoke-matrix.md` once on legacy canvas and once on
   Node 2.0. Reuse evidence only for the identical final diff.
6. Push, create a `dev` PR, apply labels, and read back head SHA, base,
   mergeability, checks, and review state.
7. Squash merge only within the active approval gate. Read back the merge SHA.
8. Append the completed boundary, PR/SHA, evidence, and deferred findings to the
   owning Issue ledger. Close an Issue only when all completion items reconcile.
9. Verify merge-tree preservation, fast-forward local `dev`, then clean only the
   confirmed lane branch/worktree. Update the execution plan checkpoint.

If a GitHub mutation times out or aborts, read back remote state before retrying.
After live smoke, free models, verify port ownership, stop only the Codex test
server/launcher, and confirm the port and related processes are gone.

## Close The Goal

- Keep `main` merge, release, tags, and Registry publishing out of scope unless
  separately approved.
- Keep the user ComfyUI instance untouched until all agreed maintenance and bug
  boundaries are integrated.
- At the final checkpoint, sync the complete compatible node-pack bundle once,
  prepare the user v0.27.0 manual check, record the result, and only then mark
  the maintenance Goal complete.
