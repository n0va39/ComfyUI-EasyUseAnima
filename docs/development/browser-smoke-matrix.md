# Dual-Canvas Browser Smoke Matrix

## Purpose

Use this procedure to validate frontend behavior separately on the ComfyUI
legacy canvas and Node 2.0. It is the reusable browser evidence contract for
maintenance PRs that change UI behavior, DOM lifecycle, workflow
serialization, or queue preparation.

Browser evidence supplements the repository-owned focused and full runners. It
does not replace them.

## When To Run

Run the matrix after the behavior boundary and final diff are stable:

- During implementation, run only focused static and semantic checks.
- Run the official full runner once when the PR diff is ready.
- Run one legacy-canvas smoke and one Node 2.0 smoke only when the PR changes
  frontend behavior.
- At an Issue-close checkpoint, confirm that the current final diff has valid
  evidence for both surfaces. Do not rerun if that same final diff was already
  covered.
- Reuse valid evidence for the same final diff. Do not repeat the matrix after
  documentation, PR-body, label, or branch-management changes.
- Rerun only when tested code changes or an environment failure invalidates
  the previous result. Record the reason for the rerun.
- Keep user-instance confirmation separate. The current manual baseline is
  ComfyUI v0.27.0 and should be checked once after the maintenance goal is
  complete, unless an earlier user check is explicitly requested.

Pure helper extraction and test-only infrastructure changes may omit browser
smoke when the PR states that UI behavior and lifecycle are unchanged. Do not
use browser evidence from a different diff as a substitute.

## Test Targets

| Target | Purpose | Allowed use |
| --- | --- | --- |
| Codex test instance | Agent-run API, queue, and browser smoke | Default automated target |
| User v0.27.0 instance | Final manual confirmation | Explicit request or maintenance-goal completion |

Do not use the user instance as a substitute for the isolated Codex test
instance. Do not copy partial runtime files into an older install without also
checking their local import dependencies.

## Preconditions

1. Freeze the target diff and record its commit SHA.
2. Complete focused checks for the changed boundary.
3. Sync the target branch to the Codex test instance.
4. Restart only the Codex-owned test server when changed static or Python files
   require it.
5. Confirm the server loads one EasyUse Anima node-pack directory and the
   extension module requests return HTTP 200.
6. Load the same saved workflow for both canvas modes.
7. Capture the initial setting values and modern-node switch state so test
   markers and the starting canvas mode can be restored.
8. Record the post-reload console timestamp or read and clear the current log
   view before the first test action. Use that point as the new-error baseline.

## Surface Selection

Open ComfyUI settings and locate `Modern node design (Vue nodes)` or its
localized equivalent.

- Switch off: legacy canvas.
- Switch on: Node 2.0.

Close settings and reload after changing the mode. Record the switch state as
the primary surface proof. DOM-rendered Vue node count may be recorded as a
secondary signal; do not rely on a hard-coded count for every workflow.

Always finish and record one surface before switching to the other.

## Per-Surface Matrix

Run the following rows once on the legacy canvas and once on Node 2.0. Rows
marked “when changed” are required only when the PR affects that boundary.

| Boundary | Action | Pass condition |
| --- | --- | --- |
| Extension load | Hard reload and open the affected UI | No module-load, syntax, reference, or unhandled-rejection error from EasyUse Anima |
| Registration | Count the affected menu, setting, panel, or listener owner | One visible registration; no duplicate overlay, observer, or listener installation |
| Open/close lifecycle | Open, close, and reopen the UI | One live instance; focus and state are restored correctly |
| Cancel path, when changed | Edit a temporary value and choose Cancel | Persisted value is unchanged |
| Save/Apply path, when changed | Edit a test value and choose Save or Apply | Reopen shows the new value |
| Backdrop/Escape path, when changed | Close through backdrop and Escape | No active overlay listener remains after close and no listener is installed twice |
| Reset path, when changed | Change a value and use Reset | Default value is restored after reopen and reload |
| Workflow persistence | Save and reload the workflow | Custom widget data and settings remain serialized without duplicate entries |
| Queue | Queue the loaded workflow once | History reports `success` and `completed`; running and pending queues return to zero |
| Console | Compare warning and error logs with the recorded post-reload baseline | No new EasyUse Anima error; unrelated ComfyUI baseline messages are identified separately |

Use unique, disposable marker values. Restore them after evidence is captured.

## Area-Specific Checks

### Settings UI

- Confirm each EasyUse Anima section is registered once.
- Change one ordinary setting and verify it after reload.
- For resolution controls, verify both mode and scale persistence.
- For long-text editors, verify Save, Cancel, reopen, and reload.
- For wildcard paths, verify add, remove, reopen, and reload.
- For color editors, verify change, reopen, Reset, and reload.

### AiO Generator

- Open each changed dialog or stage editor.
- Exercise Cancel and Apply independently.
- Verify panel state, hidden-widget serialization, save/reload, and queue
  preparation.
- Confirm preview and native-preview ownership does not duplicate after reload.

### LoRA Preset

- Open and close the menu, search results, and preview.
- For an individual PR, exercise the changed profile or FIX flow.
- Verify drag/canvas interaction only when that lifecycle changed.
- Save, reload, reopen, and queue once.
- At the #55 close checkpoint, cover load, edit, FIX, menu/preview cleanup,
  save/reload, and queue on both surfaces.

### Autocomplete

- Focus a supported input and type a deterministic query.
- Verify popup placement, active-row movement, selection, and insertion.
- Verify composition, Escape, blur, and outside-close paths when changed.
- Confirm listeners are installed once after reload and work on both input
  surfaces.
- Keep cold first-query, repeated warm-query, cache identity, retry, and
  invalidation guarantees in the focused data-adapter semantic smoke; browser
  smoke verifies the input and popup lifecycle rather than timing internals.

## Evidence Record

Add a concise record to the PR and the owning Issue ledger:

```text
Commit: <tested SHA>
ComfyUI target: Codex test instance, <version/build if known>

Legacy canvas
- Surface proof: modern-node switch off
- Changed flow: <actions and result>
- Reload/serialization: <result>
- Queue: history success/completed; running=0; pending=0
- EasyUse Anima console errors: none | <details>

Node 2.0
- Surface proof: modern-node switch on; optional Vue-node signal
- Changed flow: <actions and result>
- Reload/serialization: <result>
- Queue: history success/completed; running=0; pending=0
- EasyUse Anima console errors: none | <details>

Not run or rerun reason: <reason, if applicable>
User v0.27.0 manual check: not run | passed | failed
```

Do not put local installation paths, copied-file lists, local file hashes,
database paths, prompt IDs, or other workstation operations in the PR body.

## Cleanup

After both surfaces pass:

1. Restore changed settings and remove temporary marker values.
2. Restore the recorded starting canvas mode, reload, and confirm the switch
   state.
3. Close browser tabs opened for the smoke.
4. Leave the user v0.27.0 instance unchanged unless the task explicitly
   includes final manual confirmation.
