# Comfy Host-Provider Bridge Before the Final B-11 Shim

## Document status

- Status: active sequencing addendum
- Snapshot date: 2026-07-23
- Snapshot branch: `dev`
- Snapshot commit: `0bf5229adeda2708426a8d65e75380c9033b1835`
- Latest integrated slice: B-11c28, PR #322
- Primary execution issue: [#323](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/323)
- Parent runtime/lifecycle issue: [#187](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/187)
- Blocked extraction/final-shim issue: [#184](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/184)
- Scope: Python backend only

This document is a narrow active addendum to
[`python-backend-execution-roadmap.md`](python-backend-execution-roadmap.md).
While Issue #323 is open, this file overrides only the ordering between the
remaining B-11 work and Phase E:

```text
old default
  B-11 residual Moves -> final B-11 shim -> later Phase E

active bridge
  B-11c28 -> scoped E-02a/E-07a Contract -> remaining wrapper Moves
  -> final B-11 shim -> normal D/E sequence
```

It does not replace the target architecture, ADRs, ordinary validation gates,
or the later Phase E lifecycle work. When the bridge is complete, the main
execution roadmap must absorb the resulting state and this file becomes a
historical execution record.

## 1. Verified blocker

After B-11c28, root `nodes.py` contains eight top-level function
implementations. Seven form one ComfyUI host-capability and invocation family:

```text
_comfy_max_resolution
_find_comfy_node_class
_find_comfy_node_mapping_class
_require_custom_node_class
_require_any_custom_node_class
_encode_with_comfy_clip
_find_loaded_node_class
```

The eighth function, `_consume_reserved_wildcard_next_seed`, belongs to the
separate #167/D-12 seed and Wildcard boundary. It must not be pulled into this
provider bridge merely to make the root function count reach zero.

The seven Comfy wrappers currently combine two concerns:

1. discover host-owned modules, mappings, and node classes at call time; and
2. preserve private root monkeypatch observability because canonical runtime
   resolvers look up the root name again at each call.

The existing canonical helpers already separate much of the pure behavior:

- `easyuse_anima.infrastructure.comfy.capabilities` accepts a host module or a
  node-class lookup callable;
- `easyuse_anima.infrastructure.comfy.invocation` accepts a node-class lookup
  callable for CLIP encoding; and
- root `nodes.py` still owns the lazy `import nodes` boundary and chains the
  wrappers through its replaceable `_find_comfy_node_class` name.

A mechanical Move cannot choose a durable owner without deciding how host
access and private monkeypatch compatibility work. Moving first would require
at least one forbidden compromise:

- canonical production code importing the root compatibility module;
- duplicated host discovery;
- a broad global service locator reachable from feature code;
- eager ComfyUI or optional-node imports;
- silent removal of a currently observed private replacement seam; or
- a compatibility wrapper that hides a signature or lookup-order change.

This is therefore an architecture Contract blocker, not another residual Move.

## 2. Decision

Pull forward only the minimum E-02/E-07 boundary needed to give the seven
wrappers a canonical process owner.

The bridge consists of:

1. **E-01a:** scoped inventory and compatibility decision ledger;
2. **E-02a:** minimal runtime shell and access contract;
3. **E-07a:** narrow Comfy host-provider Protocol and default lazy provider;
4. **E-07b:** helper wiring, test migration, and compatibility gate;
5. **B-11c29+:** rollback-sized wrapper Moves or retirements under #184; and
6. **B-11d:** final binder audit and explicit root shim cutover.

The bridge does **not** introduce the complete `RuntimeServices` graph. It does
not create placeholder members for services that have not moved, and it does
not claim Phase E completion.

## 3. Ownership boundaries

### 3.1 `runtime.py`

Candidate owner:

```text
easyuse_anima/runtime.py
```

Minimum production shape:

```python
@dataclass(frozen=True)
class RuntimeServices:
    comfy: ComfyHostProvider
```

The exact names may change during review, but these rules do not:

- `bootstrap.py` is the only production composition root.
- `runtime.py` owns process-runtime access and installation state, not feature
  behavior.
- `get_runtime()` is allowed only at bootstrap and adapter boundaries where
  ComfyUI constructs an object directly.
- Feature/domain/service code receives a narrow Protocol or callable, not the
  complete `RuntimeServices` object.
- A conflicting production runtime installation is never silently accepted.
- Tests prefer explicit provider construction. A runtime override is limited to
  adapter/bootstrap integration fixtures and is always restored.
- This slice does not add settings, profiles, translation, autocomplete,
  wildcard, seed, AiO cache, clock, executor, or HTTP-client placeholders.
- No dependency-injection framework is introduced.

### 3.2 `ComfyHostProvider`

Candidate owner:

```text
easyuse_anima/infrastructure/comfy/provider.py
```

Minimum port:

```python
class ComfyHostProvider(Protocol):
    def max_resolution(self) -> int: ...
    def find_node_class(self, node_id: str): ...
    def find_node_mapping_class(self, node_id: str): ...
    def find_loaded_node_class(self, node_id: str): ...
```

The provider owns host discovery, not every operation that happens to use a
node class.

The following stay pure helpers or invocation adapters:

```text
_require_custom_node_class
_require_any_custom_node_class
_encode_with_comfy_clip
```

They receive `provider.find_node_class` or another narrow callable. Putting
these operations directly on a large provider interface would turn the host
port into a miscellaneous service and make future tests and replacements
harder.

### 3.3 Default provider

The production provider must preserve current host behavior:

- no `nodes`, `comfy`, `folder_paths`, `server`, or optional custom-node module
  is dereferenced when the provider module is imported;
- host discovery happens at use time;
- a missing host module remains a supported import/validation state;
- node mapping and attribute lookup order remain unchanged;
- the existing loaded-module fallback remains available where currently used;
- invalid or missing `MAX_RESOLUTION` still produces the same fallback;
- optional custom nodes remain optional until a selected feature requires them;
- no cache or snapshot is introduced in this Contract series; and
- no node class is owned, copied, wrapped, or subclassed by infrastructure.

Caching host lookups is a separate Behavior and lifecycle decision. It requires
revision/invalidation rules and must not be smuggled into the bridge.

### 3.4 Bootstrap

The current Phase B bootstrap owns guarded route and Wildcard startup. The
bridge may extend composition only enough to create and install the default
runtime/provider.

It must not:

- move feature repositories;
- construct optional provider clients eagerly;
- acquire PromptServer or route-table state during module import;
- add full shutdown or reverse partial-failure cleanup before their owners are
  ready; or
- make registration depend on runtime construction.

`registration.py` stays pure.

## 4. Compatibility decision ledger

Every wrapper must receive an explicit decision before its root implementation
moves. The ledger is machine-readable and reviewed together with human-readable
architecture notes.

Required fields:

```text
symbol
current root signature
canonical owner/target
production callers
runtime resolver/binder callers
repository monkeypatch consumers
external consumer evidence
host lookup/fallback order
error/result contract
compatibility classification
call-time replacement required: true/false
replacement mechanism when true
root removal gate
owner issue
```

Allowed compatibility classifications:

```text
provider_owned
pure_helper_with_provider_input
transitional_root_override
unsupported_test_only
supported_public
```

`private` spelling alone is not a removal decision, but it is also not public
support. Repository tests can justify migration work; they cannot by themselves
promote a root underscore name to supported public API.

### 4.1 Initial target mapping

| Root symbol | Durable responsibility | Candidate target |
| --- | --- | --- |
| `_comfy_max_resolution` | host capability | `ComfyHostProvider.max_resolution` |
| `_find_comfy_node_class` | host discovery | `ComfyHostProvider.find_node_class` |
| `_find_comfy_node_mapping_class` | direct host mapping lookup | `ComfyHostProvider.find_node_mapping_class` |
| `_find_loaded_node_class` | host/loaded-module discovery | `ComfyHostProvider.find_loaded_node_class` |
| `_require_custom_node_class` | pure requirement/error helper | existing capabilities helper with provider lookup input |
| `_require_any_custom_node_class` | pure requirement/error helper | existing capabilities helper with provider lookup input |
| `_encode_with_comfy_clip` | node invocation adapter | existing invocation helper with provider lookup input |

This table is a responsibility proposal, not the final compatibility decision.
E-01a must prove actual callers and replacement behavior before E-07b changes
wiring.

### 4.2 Preferred private-seam policy

The default preference is:

1. migrate repository tests from root monkeypatches to a fake provider or an
   explicitly injected lookup callable;
2. keep only a private replacement seam with real production or external
   consumer evidence;
3. document any retained seam as transitional with an exact owner and removal
   gate; and
4. avoid a permanent generic override registry.

If a retained root replacement must be observed at call time, the Contract PR
must explain how canonical code sees it without importing root `nodes.py`.
Passing an explicit callable from the composition boundary is acceptable;
canonical-to-root import is not.

### 4.3 E-01a locked result

The versioned decision ledger is
`tests/fixtures/comfy_host_compatibility.v1.json`. The compatibility-surface
test derives the current root signatures, adapter aliases, production
resolver/binder consumers, root-observation timing, and repository monkeypatch
consumers from the AST and rejects drift from the ledger.

The reviewed decisions are:

| Symbols | Durable classification | Root replacement decision |
| --- | --- | --- |
| `_comfy_max_resolution`, `_find_comfy_node_class`, `_find_comfy_node_mapping_class`, `_find_loaded_node_class` | `provider_owned` | private repository-test seam; migrate to fake provider/injection in E-07b |
| `_require_custom_node_class`, `_require_any_custom_node_class`, `_encode_with_comfy_clip` | `pure_helper_with_provider_input` | private repository-test seam; migrate to fake provider/injection in E-07b |

The GitHub public code-index search recorded in the ledger found no confirmed
consumer outside this repository. That search is explicitly non-exhaustive;
it does not convert absence of public hits into proof about private or
unindexed source. Repository tests alone do not promote the seven underscore
names to supported public API.

All 22 production consumer slots currently observe `nodes.py` globals at call
time. Some call the stored resolver directly and others bind a closure, but the
closure still executes `resolve_helper(name)` for every invocation. This is
inventory evidence, not a decision to preserve private root monkeypatching as
public compatibility. E-07b must migrate the listed repository tests before
#184 retires the corresponding root implementation.

## 5. Executable work units

### E-01a — Scoped host-wrapper inventory

- **State:** COMPLETE in PR #325
- **Owner:** #323 / parent #187
- **Type:** Contract/docs/gate
- **Base:** current `dev`
- **Production changes:** none

Required output:

- the seven-symbol ledger;
- complete caller and binder/resolver inventory;
- repository monkeypatch inventory;
- fallback and error/result order;
- optional dependency behavior;
- a reviewed decision for each root replacement seam; and
- exact next PR boundaries.

Allowed files:

```text
tests/fixtures/*compatibility*
tests/test_python_compatibility_surface.py
backend analyzer/import-boundary tools and tests
docs/architecture/*
```

Forbidden:

- moving a wrapper;
- adding runtime/provider production code;
- weakening a compatibility fixture; or
- deciding support solely from a test import.

Exit:

- each symbol is covered exactly once;
- no caller or monkeypatch consumer is unclassified;
- the ledger can reject silent support/removal changes; and
- E-02a/E-07a have fixed allowed-file and signature boundaries.

### E-02a — Minimal runtime shell

- **State:** COMPLETE in PR #327 (combined Contract with E-07a)
- **Owner:** #323 / parent #187
- **Type:** Contract

Allowed production files:

```text
easyuse_anima/infrastructure/comfy/provider.py
easyuse_anima/runtime.py
```

Required contract:

- declare only the four-method `ComfyHostProvider` Protocol needed to type the
  runtime shell;
- create a `RuntimeServices` value with only the ready `comfy` dependency;
- define production install/access semantics;
- reject or explicitly handle conflicting installation;
- support isolated construction in tests;
- keep `get_runtime()` out of feature/domain/service modules;
- do not wire bootstrap or implement host lookup; and
- avoid adding shutdown responsibilities for resources that do not yet exist.

Allowed test file:

```text
tests/test_runtime_services.py
```

Stop if a viable implementation requires a full service graph, broad global
mutation, or feature code importing runtime.

### E-07a — Provider Contract and default lazy provider

- **State:** COMPLETE in PR #327 (combined Contract with E-02a)
- **Owner:** #323 / parent #187
- **Type:** Contract

PR #327 combines E-02a and E-07a because the package-closure gate cannot admit
the new runtime/provider modules while both remain unreachable. The production
boundary is the union of the two Contract units plus the root entrypoint's
adapter-only host-module loader:

```text
__init__.py
easyuse_anima/runtime.py
easyuse_anima/bootstrap.py
easyuse_anima/infrastructure/comfy/provider.py
```

The root entrypoint owns the actual `import nodes` operation and injects a
call-time loader into bootstrap. Canonical code therefore does not import a
root shim, while the provider still observes delayed host availability without
caching. This sequencing correction does not add a package-closure exception
and does not authorize E-07b wiring, a wrapper Move, or a Behavior change.

Allowed production files:

```text
__init__.py
easyuse_anima/bootstrap.py
easyuse_anima/infrastructure/comfy/provider.py
```

Allowed test files:

```text
tests/test_comfy_host_provider.py
tests/test_runtime_services.py
```

E-07a implements the default lazy provider and composes it at bootstrap.
Requirement-helper and CLIP-invocation wiring remain E-07b work.

Stop if the provider starts owning feature schemas, node instances, stage
policy, or cache behavior.

### E-07b — Wiring and compatibility gate

- **State:** BLOCKED by E-07a
- **Owner:** #323 / parent #187 and #188 for gates
- **Type:** Contract/gate

Required work:

- wire existing pure capability/invocation helpers to a narrow provider method;
- add fake-provider fixtures;
- migrate repository-only root monkeypatch tests when the ledger says the seam
  is unsupported;
- implement only explicitly approved transitional replacement paths;
- enforce the bootstrap/adapter-only runtime-access rule; and
- leave the seven root implementations in place until the Contract is proven.

Exit:

- current behavior is reproduced through provider-backed tests;
- root compatibility decisions are executable;
- canonical modules do not import root;
- no new Pyright or import-boundary group appears; and
- #184 can resume wrapper Moves without redesign.

### B-11c29a — Max-resolution wrapper

- **State:** BLOCKED by E-07b
- **Owner:** #184
- **Type:** Move or retirement according to the ledger

Move or retire only `_comfy_max_resolution`. Preserve its zero-argument root
signature when the compatibility decision requires it. Do not combine node
lookup, requirement helpers, CLIP invocation, schema, or postprocess behavior.

### B-11c29b — Node discovery family

- **State:** BLOCKED by B-11c29a and E-07b
- **Owner:** #184
- **Type:** Move/retirement, split further when the ledger requires

Symbols:

```text
_find_comfy_node_class
_find_comfy_node_mapping_class
_find_loaded_node_class
```

Preserve direct mapping, attribute, and loaded-module lookup order. A new lookup
cache is forbidden.

### B-11c29c — Required-node helpers

- **State:** BLOCKED by B-11c29b
- **Owner:** #184
- **Type:** Move/retirement

Symbols:

```text
_require_custom_node_class
_require_any_custom_node_class
```

Preserve exact search order, tuple result, and error text. These stay pure
helpers; do not expand the provider interface merely to host them.

### B-11c29d — CLIP invocation wrapper

- **State:** BLOCKED by B-11c29b
- **Owner:** #184
- **Type:** Move/retirement

Move or retire only `_encode_with_comfy_clip`. Preserve class lookup timing,
constructor call, method lookup, result shape validation, and error text.

### B-11c30 — Runtime binder/resolver migration audit

- **State:** BLOCKED by B-11c29a-d
- **Owner:** #184/#188
- **Type:** Contract/gate plus separate cleanup Moves

Inventory all remaining `_bind_*_runtime` calls and resolver names. For each:

- migrate host capability access to the provider;
- keep feature-specific transitional seams only when their owner still requires
  them;
- prevent a provider bridge from becoming a generic string-key service locator;
- update the machine-readable compatibility surface; and
- split removal by owner family.

Do not collapse 30 binders in one PR.

### B-11d — Final root shim

- **State:** BLOCKED by B-11c30 and the separate seed/Wildcard decision for the
  final non-provider function
- **Owner:** #184
- **Type:** Move

Final conditions remain:

- root `nodes.py` contains explicit supported direct re-exports and `__all__`;
- no node execution, host discovery, prompt processing, sampling, cache,
  preview, save, or metadata implementation remains;
- mapped class identity and workflow fixtures pass;
- registration remains pure;
- bootstrap/runtime initialization is idempotent;
- package-to-root production imports are zero;
- actual package/Registry archive closure passes; and
- representative live ComfyUI execution is recorded.

The provider bridge does not authorize moving
`_consume_reserved_wildcard_next_seed`; that boundary remains owned by #167
and D-12 unless a separate behavior-preserving owner is proven.

## 6. Updated critical path

```text
COMPLETE: B-11c28 / PR #322
COMPLETE: E-01a scoped inventory / PR #325
COMPLETE: E-02a minimal runtime shell / PR #327
COMPLETE: E-07a default host provider / PR #327

READY:    E-07b wiring and compatibility gate
BLOCKED:  B-11c29a-d wrapper Moves/retirements
BLOCKED:  B-11c30 binder/resolver migration audit
BLOCKED:  B-11d final root shim

LATER:    #167 seed reservation
LATER:    #169 stage/cache Behavior
LATER:    Phase D feature consolidation
LATER:    remaining Phase E owners and lifecycle
```

G-03 enrollment and other quality work may continue in parallel only when the
changed paths and fixtures do not overlap this bridge. Issue #199 remains an
independent security track.

## 7. Validation matrix

Every bridge PR runs the checked-in project runner. Additional gates depend on
the unit:

| Gate | E-01a | E-02a | E-07a | E-07b | B-11 Moves | B-11d |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Deterministic inventory/fixture | Required | As affected | As affected | Required | Required | Required |
| Import without ComfyUI | Required | Required | Required | Required | Required | Required |
| Root/canonical behavior parity | Record | N/A | Required | Required | Required | Required |
| Private replacement decision | Required | Enforce access boundary | Enforce provider seam | Required | Required | Required |
| Pyright/import-boundary | Required | Required | Required | Required | Required | Required |
| Official full runner | Required | Required | Required | Required | Required | Required |
| `comfy node validate` and pack | No production change | If entry wiring changes | If package surface changes | If package surface changes | Path-dependent | Required |
| Live ComfyUI smoke | Not required | If entry lifecycle changes | Provider lookup smoke | Provider lookup smoke | Risk-dependent | Required |

A scenario that was not executable because an optional node/model was absent is
reported as unexecuted, not passed.

## 8. Stop conditions

Stop and document a blocker rather than expanding the PR when:

- a Contract PR needs to move one of the seven wrappers;
- a Move needs to alter lookup order, fallback, error text, or result identity;
- canonical code would import root `nodes.py`;
- feature/domain code would call `get_runtime()`;
- the provider interface starts accumulating unrelated feature operations;
- a global string-key override registry is proposed to preserve every private
  monkeypatch;
- host lookup caching appears without revision/invalidation ownership;
- an optional dependency becomes eager;
- the seed/Wildcard function is pulled into the provider bridge;
- bootstrap route/Wildcard behavior changes; or
- a wrapper removal lacks a machine-readable compatibility decision.

## 9. Codex start instruction

```text
Read docs/architecture/comfy-host-provider-bridge.md, Issue #323, Issue #184's
latest blocker/completion evidence, Issue #187, python-backend.md, ADR-002, and
the E-01a compatibility ledger before editing.

E-01a is complete in PR #325. E-02a and E-07a are complete together in PR #327
because bootstrap reachability is required by the package-closure gate. Start
with E-07b only and follow its exact compatibility and wiring boundary in
tests/fixtures/comfy_host_compatibility.v1.json. Do not move or remove the seven
root wrappers, add lookup caching, or migrate feature behavior in E-07b.

Only after the E-07b exit gates pass may #184 resume B-11c29 wrapper Moves.
Target dev, use one task ID per branch, run focused tests and the official full
runner, and record exact base/head SHA, compatibility decisions, package/live
status, rollback boundary, and next task. Do not release from this sequence.
```
