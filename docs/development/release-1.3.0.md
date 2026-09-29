# 1.3.0 release preparation

- Status: PREPARED IN DEV; not published.
- Base: `fb8c26589f5f8f3efb05df45f3e489da2856f12b`.
- Scope: version, release/Registry copy, current sample version metadata, Korean
  and English node guidance, ResShift 0.27 evidence and release ledger.
- Preserve: runtime source, existing workflow topology and values, older release
  changelog text, node/publisher identity and existing API/network setup.
- Checks: Registry copy/extraction, current sample integrity, diff/link checks,
  official validate/pack with Safe PAG notices included. Reuse unchanged runtime full/GPU evidence.
- Stop: inconsistent version, unexpected package surface or failed metadata checks.
  No main/tag/GitHub Release/Registry publish or user-instance installation.

## Reusable runtime evidence

- Safe PAG: [native engine and old/new core compatibility](native-safe-pag.md),
  dev PR #793. DAVE remains deferred; Spectrum remains external.
- ResShift: [safe local loading and 0.27.0 x2 GPU](resshift-safe-loader.md), PR #792.
- Seed replay: [uint64 lossless round trip](aio-lossless-seed.md), PR #794.
  Final runtime full: 1,719 Python tests (3 skips), 125 JS files, ComfyUI 0.37.0.
  Both canvas round trips and uncached max-uint64 GPU replay passed.
- Only release metadata/docs/sample version labels change in this preparation;
  no repeated GPU or full code suite is required for these same runtime files.

## Remaining boundaries

- Shared-subgraph per-instance image replay (#786) remains limited.
- Actual Safe PAG 40-block GPU, optimized Compile/multi-GPU and ResShift x4 GPU
  remain unverified; user guides/release notes disclose these boundaries.
- As of the 2026-09-29 live review, Registry 1.2.2 is Flagged and extraction is
  pending. Node/publisher Active is separate. Recheck at any future authorized
  publication; do not infer approval from these tests or publish repeatedly.
- A future release still needs main promotion, immutable tag and manual-install
  ZIP/SHA-256/GitHub Release. Registry publication requires its own authorized
  publish/read-back; none of those external operations is performed here.

## Metadata preparation boundary

- The checked-in manifest keeps only 1.3.0 non-deprecated, as required by the
  existing release-copy contract. Its 1.2.2 deprecation is a future sync plan,
  not a live Registry change. Do not apply metadata sync before the new release
  is published and its status is checked.

## Preparation verification (2026-09-29)

- Candidate `88968f854ac9`: Registry release-copy 4 tests, publish-version
  extraction 3 tests, release workflow 12 tests passed through the focused runner.
  The publish-version test first hit sandbox temporary-directory ACL denial;
  the one permitted same-command non-sandbox retry passed.
- Only current sample `package_version` labels changed; workflow topology and
  all settings remain identical. Added local links and `git diff --check` passed.
- The publication extractor produced exactly the reviewed 1.3.0 plain-text file.
  Live read-only lookup of Registry 1.3.0 returned HTTP 404 (not yet published).
- `registry_nodepack.ps1 -Action Pack -Target None -ComfyCliSpec comfy-cli==1.20.0`
  ran official `comfy node validate` and `comfy node pack` successfully: 358
  packaged files, 500 tracked files excluded. Archive version is 1.3.0; Safe PAG
  LICENSE/NOTICE are present; tests/development docs/cache are excluded.
- No runtime files changed relative to `fb8c26589f5f8f3efb05df45f3e489da2856f12b`.
  The ledger-only follow-up does not invalidate package or runtime evidence.
