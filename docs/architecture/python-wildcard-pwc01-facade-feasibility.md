# Python Wildcard P-WC-01 Facade Feasibility Contract

## Status and decision

- Owner: Issue #186
- Base: `769888aa0a48d32107d35fc0962241fee405aade`
- Classification: Contract; production-free
- Decision: **FEASIBLE**
- Next: one bounded P-WC-02 Move

Root `wildcard_engine.py` can become a direct-import compatibility shim without a new
canonical module. `easyuse_anima.wildcard.service` already owns the four transitional
facade functions, their exact signatures, the snapshot resolver, and the call-time
source/build dependencies.

P-WC-01 does not authorize root deletion or begin the ADR-002 support window. It only
fixes the owner and exact Move needed to remove the two remaining root production
consumer edges.

## Direct evidence

| Boundary | Current evidence | Decision |
| --- | --- | --- |
| Public facade | `python_wildcard_runtime_contract.v1.json`, `WildcardServiceTests`, and `WildcardEngineTests` cover `expand_wildcard_texts`, `expand_wildcards`, `list_wildcards`, and `wildcard_sources_signature`. | Preserve signatures and results; bind each root name directly to `easyuse_anima.wildcard.service`. |
| Canonical behavior | `service.py` already owns list/signature/library/expansion and resolves `_wildcard_sources._scan_wildcard_sources` plus `_build_wildcard_snapshot` at call time. | No new facade module and no canonical behavior change. |
| Snapshot lifecycle | The E-06 fixture and runtime contract own the exact `_DEFAULT_WILDCARD_SNAPSHOTS` identity, cache/build/Condition policy, retry, publication, and cleanup behavior. | Preserve the owner and every lifecycle invariant. |
| Seed and expansion | Wildcard golden tests cover NumPy `PCG64`, sequential mode, ordered multi-text selection, recursion, budgets, missing keys, YAML/TXT sources, and source signatures. | Root keeps eager `numpy as np`; all current canonical model/source/seed/mode/selector/expansion identities remain direct aliases. |
| Package and flat import | Root uses package-relative imports with flat-import fallbacks. Canonical wildcard modules import no root shim, bootstrap, or RuntimeServices. | Preserve both import modes and the canonical-to-root prohibition. |
| External evidence | Repository docs identify the root module as a retained compatibility surface. A best-effort search of the owner account found no additional repository import, but this is not proof of no external consumers. | Keep the root module and all supported bindings through ADR-002; do not deprecate or warn. |

## Remaining consumers

Only two root modules still import `wildcard_engine.py`:

- `api.py` imports `list_wildcards`; its payload factory deliberately reads the
  module global through a lambda so `api.list_wildcards` monkeypatching remains
  dynamic;
- `nodes.py` imports 19 seed, mode, expansion, and service names in both package and
  flat-import branches.

Canonical node, Prompt, Regional, seed-compatibility, and Wildcard feature modules
already import `easyuse_anima.wildcard.*` directly. P-WC-02 therefore changes no
feature implementation and creates no canonical-to-root edge.

## Public compatibility versus private test seams

The E-06 executable contract distinguishes these surfaces:

- the four facade functions are a transitional root public surface;
- snapshot constants, value type, and materializer are private identity re-exports;
- root `_wildcard_snapshot`, `_build_wildcard_snapshot`, and `_wildcard_sources`
  patching are private lifecycle test seams.

The private seams do not require root wrappers. The same isolated call-time injection
point already exists in `easyuse_anima.wildcard.service`: tests can patch
`service._wildcard_snapshot`, `service._build_wildcard_snapshot`, or the shared
`service._wildcard_sources` module as appropriate. P-WC-02 moves only those private
test patch targets. It does not treat them as supported external API.

The `api.py` callback seam is different and remains intact: importing canonical
`list_wildcards` into the existing `api.list_wildcards` global preserves the current
lambda lookup and direct API monkeypatch tests.

## Target shim shape

P-WC-02 leaves `wildcard_engine.py` as import-only compatibility code:

- keep eager `import numpy as np`;
- keep package-relative and flat-import fallback branches;
- keep all current direct model/source/snapshot/seed/mode/selector/expansion aliases;
- directly import `_wildcard_snapshot`, `_load_wildcard_map`, `_WildcardLibrary`,
  `list_wildcards`, `wildcard_sources_signature`, `expand_wildcard_texts`, and
  `expand_wildcards` from `easyuse_anima.wildcard.service`;
- define no wrapper function or adapter class.

Root object identity for the seven service bindings becomes the canonical identity,
which is the intended direct-shim form. Signatures, results, state owners, and all
other existing root identities remain unchanged.

## P-WC-02 task card

```text
Task ID: P-WC-02 wildcard internal-consumer and facade Move
Owner Issue: #186
Primary class: MOVE
Base SHA: latest origin/dev after P-WC-01 merges
Goal: move api.py/nodes.py off root wildcard_engine and make wildcard_engine import-only
Allowed production files:
  api.py
  nodes.py
  wildcard_engine.py
Allowed test/docs files:
  tests/test_wildcards.py
  tests/test_api_contract.py
  tests/test_python_wildcard_runtime_contract.py
  tests/fixtures/python_wildcard_runtime_contract.v1.json
  tests/test_python_compatibility_surface.py and its fixture only if generated owner changes
  analyzer/import/package owners and python_backend_baseline.json only when generated output changes
  this Contract, post-phase-e-maintenance-roadmap.md, python-compatibility-shims.md,
  architecture/development indexes
Forbidden changes:
  canonical wildcard behavior, schema, persistence, RuntimeServices, bootstrap,
  node/API payloads, public removal/deprecation, release/tag/Registry
Preserve:
  four facade signatures/results; every supported root binding; eager np identity;
  PCG64/sequential/golden output; snapshot cache/retry/atomic publication/cleanup;
  expansion budgets/errors/source signatures; api.list_wildcards dynamic callback;
  package and flat-import fallback; root/canonical import direction
Focused gates:
  WildcardServiceTests and WildcardEngineTests — canonical/root identity and parity
  WildcardSnapshotStoreTests plus direct concurrency methods — lifecycle and patch owner
  WildcardNodeTests — root nodes behavior after canonical imports
  ApiWildcardRouteTests and ApiRouteRegistrationOwnerTests — callback/payload/route parity
  PythonWildcardRuntimeContractTests — import-only root and canonical dynamic seam
  PythonCompatibilitySurfaceTests, PythonPackageSkeletonTests, import boundary, analyzer
Promotion:
  changed-file syntax/static; focused gates; git diff --check;
  official full exactly once on final SHA; validate/pack/archive because import closure changes;
  no live smoke because host-visible behavior does not change
Stop:
  a supported external root-private patch seam is proven;
  a canonical wildcard production change or new public API is required;
  any signature/result/object identity outside the selected service aliases changes;
  eager NumPy, deterministic output, route/node behavior, flat import, or import direction changes
Next: P-API-01 after P-WC-02 is reviewed and merged
```

## PRO review

No focused technical PRO review is required. Direct source and executable E-06
evidence leave one owner-preserving shape: the existing canonical service plus a root
direct-import shim. No second valid cross-boundary design remains.
