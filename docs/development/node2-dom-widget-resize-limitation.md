# Node 2.0 DOM Widget Resize Limitation

## Status

Deferred. Do not merge the experimental resize PRs.

GitHub tracking issue: #21.

Current working judgment:

- ComfyUI Node 2.0 does not have a confirmed EasyUse Anima-side fix for the
  manual shrink-to-scroll behavior yet.
- The same nodes work normally enough when using the legacy canvas.
- The practical workaround is to use the legacy canvas when manual node-height
  shrink and internal scrolling are required.
- Further work should be tracked as an issue, not carried as an active PR, until
  a safer reproduction and fix plan exists.

## Affected Behavior

The desired behavior is:

- Prompt Studio / Advanced editor nodes: shrinking the whole node height should
  make the editor viewport scroll.
- Anima AiO Generator: shrinking the whole node height should keep the preview
  stable and make only the left settings panel scroll.

On Node 2.0, previous attempts to force this behavior through DOM widget height
ownership caused worse regressions, including uncontrolled height growth.

## Attempts That Should Not Be Reused Blindly

### PR #19 Direction

PR #19 explored a Node 2.0-specific DOM widget height contract approach:

- adding resize pointer tracking,
- writing viewport height into `widget.computedHeight`,
- driving AiO panel height through CSS variables,
- removing or reducing legacy layout-owned node height behavior.

This direction was not accepted as stable. It changed the height ownership model
too broadly and produced resize anomalies during manual testing.

### Reverted Commit `ba569be`

Commit `ba569be` (`Fix Node 2 DOM widget resize ownership`) repeated the same
general approach after PR #19:

- introduced `node_resize_tracking.js`,
- assigned DOM widget viewport height through `widget.computedHeight`,
- added CSS height variables for AiO panel, preview, and settings regions,
- changed Advanced editor allocation to preserve a user viewport height.

It produced an infinite or uncontrolled height expansion regression. It was
reverted by `f0e6163` (`Revert "Fix Node 2 DOM widget resize ownership"`).

### PR #20

PR #20 was reduced to a regression guard after the faulty fix was reverted.
That PR should be closed instead of merged. The remaining useful information is
the investigation record and the fact that the current dev branch should stay on
the legacy-stable AiO height path until a new design is proven.

## Future Fix Requirements

Do not restart from the reverted patch as-is. A future attempt should first:

- reproduce the issue separately on Node 2.0 and legacy canvas,
- define one height owner for each surface before editing:
  - node height,
  - DOM widget allocation height,
  - editor or panel viewport height,
  - child content height such as textarea, preview, or settings scroll area,
- prove there is no render -> layout -> resize -> layout loop,
- verify that Prompt Studio Advanced node resize does not rewrite textarea field
  heights,
- verify that AiO preview panes do not force node height through `height: 100%`
  or min-height chains,
- test both Node 2.0 and legacy canvas before treating the fix as complete.

Any future implementation should be small and reversible, with a browser/manual
smoke test plan recorded before merge.
