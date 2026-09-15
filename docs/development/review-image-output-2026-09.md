# Code review and standalone image output

Base: `dev` at `aef6772e378ed581298ae31c903f289f1b13f0c2`.
Task: `IMAGE-OUTPUT-NODES`.

The authorized scope is security remediation, measured performance improvement,
and two generic image-output nodes, delivered through a PR into `dev`.
Unrelated behavior defects require user review before implementation.

## Change boundaries

- Add `Easy Save Image` and `Easy Image Metadata` through the existing native
  output engine, with optional `EASYUSE_IMAGE_METADATA` socket data.
- Preserve existing node identifiers, AiO settings, model inventory constraints,
  output-directory containment, collision-safe publication and metadata privacy.
- Keep generated node/source ownership contracts and all four native locales
  aligned with the new adapters; no package dependency is added.
- Isolate imported Prompt Studio field state while preserving field identifiers,
  cached state and asynchronous result ownership. Tracks #752.
- Filter filename candidates before filesystem metadata calls and retain only
  the greatest suffix. The focused regression avoids 2,000 unrelated file-state
  lookups while preserving image/sidecar collision and directory handling.
- Bound wildcard YAML source traversal, avoid repeatedly scanning numeric text
  while detecting quantified wildcards, and skip comment scans for text without
  a comment marker. Existing comment/blank-line output is preserved. Tracks #754.
- YAML files are checked before option construction: depth 64, 65,536 visits,
  65,536 option references across temporary/published aggregates, and 8,388,608
  accumulated output characters. Cyclic or over-budget files follow the existing
  invalid-YAML skip policy; valid sibling files and normal duplicate weights remain.
- After user review of #753, handle non-finite integer settings through the
  existing default-value fallback, including values already saved on disk.

## Review disposition

The review covered Prompt Studio frontend input/state boundaries and backend
API, settings, profile, LoRA and wildcard input owners. Findings are based on
reachable callers and focused reproductions; this is not an exhaustive audit of
third-party ComfyUI node packs or every model execution backend.

The non-finite numeric setting failure was recorded in #753 before modification.
The user confirmed the defect, and the focused settings projection/save test now
proves that existing invalid values and subsequent writes/readbacks recover
without changing the stored data or valid-value range policy. This reproduction
uses the real payload helper with in-memory persistence.

## Validation and completion

Focused checks passed for the new adapters (8 tests), wildcard budgets and scans
(9 tests), settings recovery, filename allocation, locales, public node contracts
and direct frontend state isolation. The highlight smoke reproduced the failure
before the patch and passed afterward, including reserved field identifiers,
cached state identity and reversed asynchronous completion across two nodes.

On isolated ComfyUI 0.34.0 / frontend 1.49.6, Legacy Canvas and Node 2.0 both
rendered the new nodes and connected metadata socket. Each canvas queued a
64x48 image with seed 42, steps 20 and CFG 7. PNG readback verified Unicode
parameters, the API prompt, all three workflow links and an identical JSON
sidecar. Node 2.0 also preserved the filename, values and links after saving,
closing and reopening the workflow. The metadata seed has no automatic
generation control; existing browser documents must reload the new node schema.

A separate real ComfyUI queue verified JPEG/WebP Unicode EXIF and JSON sidecars,
plus a disconnected-metadata PNG containing pixels only. Seven changed runtime
files matched the installed copy, and the served highlight module matched the
source. The temporary canvas setting was restored and the owned server stopped.
These runtime checks used EmptyImage and did not load a generation model.

The repository full gate passed on the final code candidate: 1,630 Python tests
(3 existing skips), frontend checks over 123 JavaScript files, Pyright baseline,
import boundaries, size/complexity, file disposition, support ownership and diff
checks. Existing report-only Ruff findings and the Pyright baseline were unchanged.
The task ends at `dev`; public release metadata is a separate rollback unit.
