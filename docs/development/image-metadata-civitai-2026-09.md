# Image metadata ownership and Civitai lookup

Base: `dev` at `76dbb63651d088a39c816f4f5a08b1fb2c795187`.

Move workflow embedding and JSON sidecar controls to Easy Save Image. Easy Image
Metadata retains A1111 generation data only. Add a standalone hash/AIR Civitai
lookup using the existing bounded, fixed-host transport and compact result cache.

The change owns image-output adapters, native Civitai lookup, registration,
workflow-option migration, native locales, related documentation and exact
node/source/test inventories. Existing AiO settings, node IDs, metadata privacy,
output containment, collision-safe writes and user data remain intact. Legacy
pre-release workflows migrate trailing metadata options to connected savers;
existing API callers should move those options to saver inputs explicitly.

Focused checks cover real PNG/JPEG/WebP and JSON readbacks, workflow migration
and hash/AIR identity validation, compact caching and retries. Complete the
repository full gate and changed API/Legacy/Node 2.0 flows on the isolated Codex
test instance before the authorized PR merge into dev. User-instance testing is
excluded by the user's latest instruction. Stop affected runtime validation on
test-environment update failure; expose lookup failures without false hash data.

## Completion evidence

The final full gate passed 1,645 Python tests with three existing skips and
frontend checks over 125 JavaScript files. Import ownership, file disposition,
size/complexity and type checks passed; report-only Ruff and Pyright debt stayed
at their existing 25/14 findings. The new focused contracts cover 11 image-output
cases, 12 Civitai cases and deterministic workflow migration.

Review identified a missing weight in the metadata connection. The standalone
builder now opts into a `Resource weights` A1111 JSON field; the existing AiO
default remains unchanged. PNG/JPEG/WebP readbacks with workflow export disabled
prove that the weight reaches the stored parameters without extra HTTP calls.

On isolated ComfyUI 0.34.0 / frontend 1.49.6, all three nodes registered and the
served migration modules matched source. Real Civitai hash and AIR lookups
agreed. An API queue connected lookup, metadata and a 64x48 PNG with embedding
disabled. Legacy Canvas and Node 2.0 migrated the original options, queued real
image saves and preserved seed 42, steps 20, CFG 7, links and JSON sidecars.
Node 2.0 also preserved lookup hash/weight and saver controls after file reload.
The temporary canvas setting was restored, generated test files removed and the
owned test server stopped. No model generation or user-instance tests were run.
