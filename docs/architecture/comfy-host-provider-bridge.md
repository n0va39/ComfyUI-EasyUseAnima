# Comfy Host-Provider Bridge Before the Final B-11 Shim

## Document status

- Status: active sequencing addendum
- Snapshot date: 2026-07-23
- Snapshot branch: `dev`
- Snapshot commit: `53d92aa944663a18ee593c027b90fa0b8e9444be`
- Latest integrated slice: B-11c29b3, PR #334
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

- **State:** COMPLETE in PR #328
- **Owner:** #323 / parent #187 and #188 for gates
- **Type:** Contract/gate

Pre-edit inventory at the E-07b base:

- the seven root implementations remain in `nodes.py`;
- 22 production consumer slots in 15 canonical modules resolve those names at
  call time through their existing binder/resolver contracts;
- all seven root replacement seams are `unsupported_test_only`;
- 16 repository test files still replace one or more root seams, including
  `patch.multiple` and direct assignment forms omitted by the E-01a detector;
- two repository test files patch canonical consumers directly; and
- the installed runtime exposes exactly one narrow `ComfyHostProvider`.

Completion evidence:

- all 22 host-helper consumer slots in 15 canonical modules resolve the seven
  owned seams through the installed provider while unrelated names and the
  pre-bootstrap flat-import compatibility path retain the existing root
  fallback;
- all 16 repository root-replacement test files use the fake provider or an
  explicit canonical lookup, leaving zero repository root replacements;
- the two intentional canonical `_comfy_max_resolution` replacement files
  remain recorded separately;
- `get_runtime()` remains limited to `runtime.py` and the Comfy wiring adapter;
- the resolver return annotation is `Any` because unrelated names continue
  through the existing fallback and include non-callable constants and module
  values; the seven provider-owned resolutions themselves remain callables;
- the seven root wrapper implementations remain unchanged for the subsequent
  rollback-sized Moves; and
- the deterministic backend inventory contains 86 shipped and reachable
  Python modules with no missing internal import.

Allowed production files:

```text
nodes.py
easyuse_anima/infrastructure/comfy/wiring.py
```

Allowed test and gate files:

```text
tests/comfy_host_fakes.py
tests/test_comfy_host_wiring.py
tests/test_aio_conditioning.py
tests/test_aio_generation_migrations.py
tests/test_aio_generation_settings.py
tests/test_aio_legacy_generation.py
tests/test_aio_model_preparation.py
tests/test_aio_nodes.py
tests/test_aio_output.py
tests/test_aio_preview.py
tests/test_aio_resources.py
tests/test_aio_sampling.py
tests/test_aio_schema_contract.py
tests/test_comfy_adapters.py
tests/test_node_contracts.py
tests/test_prompt_corrector.py
tests/test_prompt_studio_regional.py
tests/test_sam3_nodes.py
tests/test_python_compatibility_surface.py
tests/test_python_backend_analyzer.py
tests/test_nodes_module_analyzer.py
tests/fixtures/comfy_host_compatibility.v1.json
tests/fixtures/python_backend_baseline.json
tests/fixtures/python_compatibility_surface.v1.json
docs/architecture/*
```

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

Forbidden:

- moving, deleting, or changing the seven root implementations;
- changing lookup order, fallback values, error text, node/workflow schemas, or
  feature behavior;
- importing root `nodes.py` from the canonical package;
- adding a provider cache, snapshot, retry policy, or mutable override
  registry; and
- expanding `RuntimeServices` or calling `get_runtime()` from feature, domain,
  or service modules.

### B-11c29a — Max-resolution wrapper

- **State:** COMPLETE in PR #329
- **Owner:** #184
- **Type:** Move or retirement according to the ledger

Move or retire only `_comfy_max_resolution`. Preserve its zero-argument root
signature when the compatibility decision requires it. Do not combine node
lookup, requirement helpers, CLIP invocation, schema, or postprocess behavior.

Pre-edit inventory at `dev@14015769634d387fe5afa6a74a5594007e86346c`:

- root `nodes.py` owns one zero-argument `_comfy_max_resolution` wrapper and
  imports `_adapter_comfy_max_resolution` in relative and flat modes;
- the wrapper has no mutable state or import-time call and lazily resolves host
  `nodes.MAX_RESOLUTION`, returning `16384` after missing/invalid host state;
- three production consumers resolve the name at call time through the E-07b
  provider wiring: AiO generation normalization, Impact Detailer inputs, and
  SAM3 inputs;
- repository root replacements are zero; two tests intentionally replace the
  canonical consumer slot; external consumer evidence remains zero;
- the ledger classifies the private root seam as `unsupported_test_only` and
  does not require call-time root replacement; and
- therefore this unit retires the root wrapper instead of preserving a direct
  alias, while the wiring adapter keeps the pre-bootstrap flat-import fallback.

Allowed production files:

```text
nodes.py
easyuse_anima/infrastructure/comfy/wiring.py
```

Allowed test, fixture, and documentation files:

```text
tests/test_comfy_host_wiring.py
tests/test_node_contracts.py
tests/test_python_compatibility_surface.py
tests/test_nodes_module_analyzer.py
tests/test_python_backend_analyzer.py
tests/fixtures/comfy_host_compatibility.v1.json
tests/fixtures/python_compatibility_surface.v1.json
tests/fixtures/python_backend_baseline.json
docs/architecture/*
```

Exit:

- root `_comfy_max_resolution` and both adapter imports are absent;
- installed-runtime consumers continue to use
  `ComfyHostProvider.max_resolution`;
- pre-bootstrap flat import preserves delayed lookup and `16384` fallback
  without canonical-to-root imports;
- root and canonical replacement counts remain executable; and
- root residual/analyzer/package closure gates pass.

Forbidden:

- changing `ComfyHostProvider`, the domain-neutral capability helper, lookup
  order, default value, conversion/error behavior, schemas, or node inputs;
- moving any node-discovery, requirement, or CLIP helper;
- adding cache, snapshot, mutable override state, or canonical root import; and
- changing postprocess, seed, stage, route, workflow, or persistence behavior.

### B-11c29b — Node discovery family

- **State:** IN PROGRESS, split into B-11c29b1-b3
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

The ledger requires three rollback units:

1. **B-11c29b1:** direct mapping-only lookup,
   `_find_comfy_node_mapping_class`;
2. **B-11c29b2:** general lookup followed by loaded-module fallback,
   `_find_loaded_node_class`; and
3. **B-11c29b3:** mapping/attribute/loaded-module lookup,
   `_find_comfy_node_class`.

The first unit has one production consumer, no adapter import, no nested finder
dependency, and no repository or confirmed external replacement consumer. The
other two wrappers retain adapter imports. The loaded wrapper can retire through
its provider method while the general root lookup remains available to the
root requirement and CLIP wrappers. Those wrappers must retire before the
general lookup, so the executable order after B-11c29b2 is B-11c29c,
B-11c29d, then B-11c29b3. Combining any of these with B-11c29b1 would enlarge
the rollback and compatibility boundary without need.

#### B-11c29b1 — Direct mapping-only lookup

- **State:** COMPLETE in PR #330 / `7eafe06`
- **Owner:** #184
- **Type:** Retirement

Pre-edit inventory at `dev@0acc0152e1039d00c9387324faef43e9a7728219`:

- root `nodes.py` owns one `_find_comfy_node_mapping_class(node_id: str)`
  definition and no canonical adapter import for the symbol;
- the wrapper has no mutable state or import-time call and performs only a
  call-time host `nodes.NODE_CLASS_MAPPINGS.get(node_id)` lookup;
- the one production consumer is `easyuse_anima.image.sam3`, which resolves the
  name at call time through the E-07b provider wiring;
- repository root replacements, canonical replacements, and confirmed external
  consumers are all zero;
- the ledger classifies the private root seam as `unsupported_test_only` and
  does not require call-time root replacement; and
- therefore this unit retires the root definition while the wiring adapter
  preserves the runtime-missing flat-import path with a fresh default provider.

Allowed production files:

```text
nodes.py
easyuse_anima/infrastructure/comfy/wiring.py
```

Allowed test, fixture, and documentation files:

```text
tests/test_comfy_host_wiring.py
tests/test_comfy_host_provider.py
tests/test_node_contracts.py
tests/test_sam3_nodes.py
tests/test_python_compatibility_surface.py
tests/test_nodes_module_analyzer.py
tests/fixtures/comfy_host_compatibility.v1.json
tests/fixtures/python_compatibility_surface.v1.json
tests/fixtures/python_backend_baseline.json
docs/architecture/*
```

Exit:

- root `_find_comfy_node_mapping_class` is absent;
- installed-runtime SAM3 lookup continues to use
  `ComfyHostProvider.find_node_mapping_class`;
- flat pre-bootstrap lookup remains delayed, mapping-only, and returns `None`
  after missing or invalid host state;
- retirement gates reject both a restored root definition and an undocumented
  adapter alias; and
- root residual/analyzer/package closure gates pass.

Forbidden:

- moving either general or loaded node lookup;
- changing mapping, attribute, or loaded-module order;
- changing `ComfyHostProvider`, the provider implementation, SAM3 feature
  behavior, or node/workflow schemas;
- adding cache, snapshot, mutable override state, or canonical root import; and
- changing requirement, CLIP, seed, stage, route, persistence, or postprocess
  behavior.

#### B-11c29b2 — Loaded node lookup

- **State:** COMPLETE in PR #331 / `164b53e`
- **Owner:** #184
- **Type:** Retirement

Pre-edit inventory at `dev@7eafe063d4b0e7b90028bbb3cdf0597543802641`:

- root `nodes.py` owns one `_find_loaded_node_class(node_id: str)` definition
  and imports `_adapter_find_loaded_node_class` in relative and flat modes;
- the wrapper has no mutable state or import-time call. At call time it invokes
  the general root lookup, returns a non-`None` result, otherwise scans current
  `sys.modules` order for `NODE_CLASS_MAPPINGS[node_id]`, then returns `None`;
- the one production consumer is `easyuse_anima.prompt.conditioning`, which
  resolves the name at call time through the E-07b provider wiring;
- repository root replacements, canonical replacements, and confirmed external
  consumers are all zero;
- the ledger classifies the seam as `provider_owned`,
  `unsupported_test_only`, with no call-time root replacement requirement; and
- therefore this unit retires the root definition and both adapter imports.
  Installed runtime uses the provider method; runtime-missing flat imports use
  a fresh default provider without removing the still-required general root
  lookup.

Allowed production files:

```text
nodes.py
easyuse_anima/infrastructure/comfy/wiring.py
```

Allowed test, fixture, and documentation files:

```text
tests/test_comfy_host_wiring.py
tests/test_comfy_host_provider.py
tests/test_node_contracts.py
tests/test_python_compatibility_surface.py
tests/test_nodes_module_analyzer.py
tests/fixtures/comfy_host_compatibility.v1.json
tests/fixtures/python_compatibility_surface.v1.json
tests/fixtures/python_backend_baseline.json
docs/architecture/*
```

Exit:

- root `_find_loaded_node_class` and both adapter imports are absent;
- installed-runtime conditioning lookup continues to use
  `ComfyHostProvider.find_loaded_node_class`;
- flat pre-bootstrap lookup remains delayed, observes current host and loaded
  modules without importing optional packs, and returns `None` when missing;
- root general lookup remains available to requirement and CLIP wrappers;
- retirement gates reject restored root or adapter bindings; and
- root residual/analyzer/package closure gates pass.

Forbidden:

- moving the general node lookup, requirement helpers, or CLIP invocation;
- changing mapping, attribute, loaded-module order, or exception/result
  behavior;
- changing `ComfyHostProvider`, provider implementation, conditioning feature
  behavior, schemas, or workflows;
- adding cache, snapshot, mutable override state, optional imports, or
  canonical root import; and
- changing seed, stage, route, persistence, or postprocess behavior.

### B-11c29c — Required-node helpers

- **State:** COMPLETE in PR #332 / `449d9da`; precedes B-11c29d and B-11c29b3
- **Owner:** #184
- **Type:** Retirement

Symbols:

```text
_require_custom_node_class
_require_any_custom_node_class
```

Pre-edit inventory at `dev@164b53ec89947bc5a72889d83641c5db947dbef5`:

- root `nodes.py` owns both definitions and imports
  `_adapter_require_custom_node_class` and
  `_adapter_require_any_custom_node_class` in relative and flat modes;
- `_require_custom_node_class` has four call-time production consumer modules:
  `easyuse_anima.aio.legacy_generation`, `model_preparation`, `output`, and
  `sampling`;
- `_require_any_custom_node_class` has one call-time production consumer module,
  `easyuse_anima.aio.model_preparation`;
- installed runtime already resolves both canonical pure helpers with only
  `ComfyHostProvider.find_node_class` injected. The provider interface does not
  own requirement or error policy;
- both wrappers have zero repository root/canonical monkeypatch consumers, zero
  confirmed external consumers, no import-time calls, and no mutable state;
- the single helper calls the lookup once, returns the class object unchanged,
  or raises the exact existing node-id/pack/hint `RuntimeError`;
- the multi helper checks caller tuple order, returns the first
  `(node_id, class)` pair, or raises the exact existing joined-candidate
  `RuntimeError`; and
- the ledger classifies both as `pure_helper_with_provider_input`,
  `unsupported_test_only`, with no call-time root replacement requirement.

These symbols form one rollback unit because they share the same pure canonical
owner, root dependency, relative/flat adapter boundary, provider input, and
wiring branch. No Contract or Behavior change is included.

Allowed production files:

```text
nodes.py
easyuse_anima/infrastructure/comfy/wiring.py
```

Allowed test, fixture, and documentation files:

```text
tests/test_comfy_adapters.py
tests/test_comfy_host_wiring.py
tests/test_node_contracts.py
tests/test_python_compatibility_surface.py
tests/test_nodes_module_analyzer.py
tests/fixtures/comfy_host_compatibility.v1.json
tests/fixtures/python_compatibility_surface.v1.json
tests/fixtures/python_backend_baseline.json
docs/architecture/*
```

Exit:

- both root definitions and all four adapter imports are absent;
- installed-runtime consumers keep the existing provider-injected pure helpers;
- flat pre-bootstrap calls use a fresh default provider lookup at call time;
- success identity, candidate order, tuple shape, exact error text, and
  use-time-only optional dependency behavior remain unchanged;
- root general lookup remains available to the CLIP wrapper;
- retirement gates reject restored roots or adapter bindings; and
- root residual/analyzer/package closure gates pass.

Forbidden:

- changing canonical capability helper implementations or the provider
  interface/implementation;
- changing AiO consumers, binders, node/workflow schemas, or selected-feature
  timing;
- moving the CLIP or general lookup wrappers;
- changing search order, tuple/result identity, exception type/text, or error
  timing;
- adding cache, snapshot, mutable override state, optional imports, or
  canonical root imports; and
- changing seed, stage, route, persistence, or postprocess behavior.

### B-11c29d — CLIP invocation wrapper

- **State:** COMPLETE in PR #333 / `931a80f`; precedes B-11c29b3
- **Owner:** #184
- **Type:** Retirement

Pre-edit inventory at `dev@449d9da6e9f1d296a154a3cb20d9147dfc492467`:

- root `nodes.py` owns one `_encode_with_comfy_clip(clip, text: str)`
  definition and imports `_adapter_encode_with_comfy_clip` in relative and flat
  modes;
- the canonical pure helper is
  `easyuse_anima.infrastructure.comfy.invocation:_encode_with_comfy_clip` and
  accepts only the injected node finder in addition to `clip` and `text`;
- six call-time production binder modules own 28 call sites:
  `easyuse_anima.aio.conditioning`, `aio.legacy_generation`,
  `nodes.prompt_data_nodes`, `nodes.regional_nodes`, `nodes.sam3_nodes`, and
  `prompt.artist_mix`;
- installed runtime already injects only
  `ComfyHostProvider.find_node_class`; the provider does not own CLIP
  construction, invocation, validation, or error policy;
- the repository has no root/canonical monkeypatch consumer and no confirmed
  external consumer. Focused tests replace this seam through the E-07 layered
  fake provider; one legacy direct root invocation assertion is redundant with
  canonical and flat-wiring coverage and must retire with the root symbol;
- root/canonical helpers have no mutable state or import-time calls. The six
  consumers keep binder-owned runtime resolver state, but resolve and invoke
  the helper only at feature use time;
- exact order is node lookup for `CLIPTextEncode`, class construction,
  `encode` attribute read, `encode(clip, text)`, non-empty tuple validation,
  then `result[0]`;
- missing class, missing method, and invalid result each use the existing exact
  `RuntimeError`; lookup, constructor, attribute, and encode exceptions remain
  uncaught; and
- the ledger classifies the seam as `pure_helper_with_provider_input`,
  `unsupported_test_only`, with no call-time root replacement requirement.

Allowed production files:

```text
nodes.py
easyuse_anima/infrastructure/comfy/wiring.py
```

Allowed test, fixture, and documentation files:

```text
tests/test_comfy_adapters.py
tests/test_comfy_host_wiring.py
tests/test_node_contracts.py
tests/test_python_compatibility_surface.py
tests/test_nodes_module_analyzer.py
tests/fixtures/comfy_host_compatibility.v1.json
tests/fixtures/python_compatibility_surface.v1.json
tests/fixtures/python_backend_baseline.json
docs/architecture/*
```

Exit:

- root definition and both adapter imports are absent;
- installed-runtime consumers keep the provider-injected canonical helper;
- flat pre-bootstrap calls inject a fresh default provider lookup at call time;
- lookup/constructor/method/call/result order, success identity, exact errors,
  and raw exception propagation remain unchanged;
- root general lookup remains available for B-11c29b3;
- retirement gates reject restored root or adapter bindings; and
- root residual/analyzer/package closure gates pass.

Forbidden:

- changing the canonical invocation helper or provider
  interface/implementation;
- changing the six production consumers, binders, schemas, workflows, or
  feature-selection timing;
- moving the general node lookup;
- changing lookup/construction/call order, return identity, result validation,
  exception type/text/timing, or raw exception propagation;
- adding cache, snapshot, mutable override state, optional imports, or
  canonical root imports; and
- changing seed, stage, route, persistence, or postprocess behavior.

#### B-11c29b3 — General node lookup

- **State:** COMPLETE in PR #334 / `53d92aa`
- **Owner:** #184
- **Type:** Retirement

Pre-edit inventory at `dev@931a80f44bea694f3a91a200fe53123226a70b3a`:

- root `nodes.py` owns one `_find_comfy_node_class(node_id: str)` definition
  and imports `_adapter_find_comfy_node_class` in relative and flat modes;
- its canonical owner is
  `ComfyHostProvider.find_node_class`, implemented through
  `easyuse_anima.infrastructure.comfy.capabilities:_find_comfy_node_class`;
- six call-time production binder modules own 17 lookup call sites:
  `easyuse_anima.aio.model_preparation` (2), `aio.output` (1),
  `aio.preview` (1), `aio.resources` (7), `aio.sampling` (4), and
  `image.sam3` (2);
- installed runtime already resolves those calls through
  `ComfyHostProvider.find_node_class`. Repository root replacements,
  canonical replacements, and confirmed external consumers are all zero;
- the root wrapper has no mutable state or import-time call. Every consumer
  keeps its existing binder-owned resolver state and performs lookup only at
  feature use time;
- exact lookup order is lazy host `nodes` import, host
  `NODE_CLASS_MAPPINGS[node_id]`, host attribute `node_id`, then current
  `sys.modules` order for `NODE_CLASS_MAPPINGS[node_id]`;
- host mapping and attribute exceptions fall through to the loaded-module scan,
  the first non-`None` class object is returned unchanged, and a missing class
  returns `None`;
- optional custom-node modules are observed only when already loaded and are
  never imported by this helper; and
- the ledger classifies the root seam as `provider_owned`,
  `unsupported_test_only`, with no call-time root replacement requirement.

Allowed production files:

```text
nodes.py
easyuse_anima/infrastructure/comfy/wiring.py
```

Allowed test, fixture, and documentation files:

```text
tests/test_comfy_host_wiring.py
tests/test_comfy_host_provider.py
tests/test_node_contracts.py
tests/test_aio_model_preparation.py
tests/test_aio_output.py
tests/test_aio_preview.py
tests/test_aio_resources.py
tests/test_aio_sampling.py
tests/test_sam3_nodes.py
tests/test_python_compatibility_surface.py
tests/test_nodes_module_analyzer.py
tests/fixtures/comfy_host_compatibility.v1.json
tests/fixtures/python_compatibility_surface.v1.json
tests/fixtures/python_backend_baseline.json
docs/architecture/*
```

Exit:

- the root definition and both adapter imports are absent;
- installed-runtime consumers continue using
  `ComfyHostProvider.find_node_class`;
- flat pre-bootstrap calls use a fresh default provider at call time;
- mapping, attribute, and loaded-module order, exception fallthrough, result
  identity, missing result, and use-time-only optional dependency behavior
  remain unchanged;
- retirement gates reject restored root or adapter bindings; and
- root residual/analyzer/package closure gates pass.

Forbidden:

- changing `ComfyHostProvider`, its implementation, or the canonical capability
  helper;
- changing the six production consumers, binders, schemas, workflows, or
  feature-selection timing;
- changing lookup order, exception fallthrough, result identity, missing-result
  behavior, or optional dependency timing;
- adding cache, snapshot, mutable override state, optional imports, or
  canonical root imports; and
- changing requirement, CLIP, seed, stage, route, persistence, or postprocess
  behavior.

### B-11c30 — Runtime binder/resolver migration audit

- **State:** COMPLETE on `dev` in PR #336 / `02b8c4a`
- **Owner:** #184/#188
- **Type:** Contract/gate
- **Production changes:** none

Pre-edit inventory at `dev@53d92aa944663a18ee593c027b90fa0b8e9444be`:

- root `nodes.py` invokes exactly 30 canonical `_bind_*_runtime` functions;
- 15 binders use the provider-aware resolver followed by root fallback, 13 use
  root `globals()` resolution only, and two receive explicit root callbacks;
- the canonical modules resolve 295 unique names: 288 current root names and
  seven provider virtual seams that no longer exist as root symbols;
- the 288 root names consist of the existing 284 compatibility/residual
  resolver names plus the four preamble dependencies `ceil`, `json`, `random`,
  and `sqrt`;
- all seven provider seams remain active in 22 consumer slots across 15 modules;
  they are not generic provider operations and retain the E-07 narrow provider
  decisions;
- binder calls also pass 14 unique direct root dependencies in 32 slots;
- repository tests replace 165 root names across 20 files. This is migration
  cost evidence, not supported-public compatibility evidence;
- every string resolver observes the root at call time; the two explicit
  callback binders receive root-calling closures, so their target lookup also
  remains use-time; and
- no binder, resolver, provider, consumer, node/workflow schema, or runtime
  state changes in this Contract/gate.

Machine-readable owner families:

| Family | Binders | Root name slots | Provider slots | Direct slots | Test-replaced names |
| --- | ---: | ---: | ---: | ---: | ---: |
| AiO | 12 | 260 | 13 | 8 | 133 |
| Image/SAM3/Impact | 3 | 3 | 5 | 3 | 2 |
| Prompt/Regional | 10 | 154 | 4 | 7 | 37 |
| Wildcard/NAIA | 2 | 0 | 0 | 9 | 5 |
| LoRA | 3 | 25 | 0 | 5 | 14 |

Allowed files:

```text
tests/test_python_compatibility_surface.py
tests/fixtures/python_compatibility_surface.v1.json
docs/architecture/*
```

Exit:

- every binder has one canonical module, one owner family, exact bound globals,
  root call keywords, direct dependencies, resolver names, provider names, and
  repository replacement evidence;
- new or returned provider virtual names, unknown direct resolver names,
  binder/family drift, and root/provider count drift fail deterministically;
- the provider remains restricted to the seven E-07 decisions and is not a
  generic string-key service locator;
- production code and behavior are unchanged; and
- the first cleanup candidate can be selected without combining owner families.

Forbidden:

- changing `nodes.py`, any binder, runtime consumer, provider, wiring, schema,
  workflow, seed, stage, cache, route, persistence, or optional dependency;
- treating repository test replacement as public support evidence;
- deleting aliases or rewriting tests before the owning family Move; and
- collapsing 30 binders or multiple owner families into one cleanup PR.

Planned cleanup sequence:

1. **B-11c30a Image/SAM3/Impact:** three binders, five provider slots, three
   root-name slots, and two test-replaced names. This is the smallest
   provider-bearing family and the first focused implementation candidate.
2. **B-11c30b LoRA:** three non-provider binders with 25 root-name slots;
   preserve logger proxy, prompt-token callback, input-type identity, and
   bind-time object installation.
3. **B-11c30c Prompt/Regional:** ten binders; split service and node-adapter
   subunits before implementation because 154 root-name slots and 37
   test-replaced names exceed one rollback unit.
4. **B-11c30d AiO:** twelve binders; split support/service and node-adapter
   subunits and retain #169 behavior ownership. Do not migrate 260 root-name
   slots in one PR.
5. **B-11c30e Wildcard/NAIA:** two explicit-callback binders; keep separate from
   D-12 seed/Wildcard behavior and legacy engine consolidation.

### B-11c30a — Image/SAM3/Impact binder retirement

- **State:** COMPLETE on `dev` in PR #337 / `3647d3a`
- **Owner:** #184
- **Type:** Move
- **Base:** `dev@02b8c4a17b11011f1381c27cef6bd869b50f81bb`

Pre-edit inventory:

- root `nodes.py` imports three private binders in both package and flat-import
  paths, then calls each binder once during module initialization:
  `_bind_sam3_runtime`, `_bind_impact_detailer_node_runtime`, and
  `_bind_sam3_node_runtime`;
- those binders install eight canonical module globals: two SAM3 discovery
  helpers, two Impact node input helpers, and four SAM3 node input/execution
  helpers;
- five slots are E-07 provider decisions:
  `_find_comfy_node_class`, `_find_comfy_node_mapping_class`,
  `_comfy_max_resolution` in two modules, and `_encode_with_comfy_clip`;
- three slots are existing canonical root-name helpers:
  `_impact_scheduler_names`, `_load_checkpoint_with_comfy`, and
  `_preferred_checkpoint_default`;
- all three root calls depend directly on `_resolve_comfy_host_helper`;
- the consumers are SAM3 optional-node discovery, Impact Detailer input
  construction, SAM3 context input/loading, and SAM3 prompt encoding;
- repository tests replace two names that occur in this family,
  `_impact_scheduler_names` and `_load_checkpoint_with_comfy`. This is test
  migration evidence, not public root compatibility;
- the binders mutate canonical module globals once at root import, while each
  installed closure resolves its actual target at call time; and
- the root aliases for the three non-provider helpers remain required by other
  owner families and are not retirement targets in this lane.

Allowed production files:

```text
nodes.py
easyuse_anima/image/sam3.py
easyuse_anima/nodes/impact_detailer_nodes.py
easyuse_anima/nodes/sam3_nodes.py
```

Allowed supporting files are the focused SAM3/node-contract tests, the Python
compatibility gate and fixture, and these architecture documents.

Exit:

- root no longer imports or calls the three family binders;
- the canonical modules own their provider and direct-helper wiring without
  importing root `nodes.py`;
- E-07 provider decisions remain call-time and flat pre-bootstrap imports keep
  the default-provider fallback;
- the three non-provider targets keep their current canonical implementation,
  return identity, exceptions, and call timing;
- no bind-time mutable runtime installation remains in these three modules; and
- node schema, workflow, SAM3/Impact behavior, optional dependency timing, and
  public mappings remain unchanged.

Forbidden:

- changing provider protocol or lifecycle, detection/detailing behavior,
  checkpoint semantics, input defaults, schemas, workflows, seed/stage/cache,
  dependency discovery, or error text;
- removing root aliases still consumed by AiO or another binder family; and
- including LoRA, Prompt/Regional, AiO, or Wildcard/NAIA binder cleanup.

Implementation result:

- root imports/calls and the three canonical binder definitions are removed;
- provider-backed helpers now resolve directly in their canonical modules at
  call time, while the scheduler/checkpoint/default helpers are direct
  canonical imports;
- the Comfy host ledger still records 22 provider slots across 15 modules and
  marks the five moved slots as direct call-time consumers instead of root
  binder consumers;
- the remaining root audit is 27 binders in four families: 12
  provider-then-root, 13 root-only, and two explicit callbacks;
- `nodes.py` is 1,820 lines, down 30 lines from the B-11c30 base; and
- focused SAM3, Comfy adapter, compatibility, and backend analyzer validation
  passes 61 tests.

### B-11c30b — LoRA binder retirement

- **State:** COMPLETE on `dev` in PR #338 / `cdd115d`
- **Owner:** #184
- **Type:** Move
- **Base:** `dev@3647d3ad35dffb77b35ca423e1b89c6a4d7c3116`

Pre-edit inventory:

- root `nodes.py` imports three private binders in both package and flat-import
  paths, then calls `_bind_lora_metadata_runtime`,
  `_bind_lora_preset_runtime`, and `_bind_lora_node_runtime` once each;
- the metadata binder installs `_prompt_tokens`, `_resolve_helper`, and a
  `_RuntimeLoggerProxy` in three module globals. Its resolver observes eight
  metadata-owned names through root at call time;
- the preset binder installs the prompt-correction callback and resolver in two
  module globals. Its resolver observes five preset/value names through root at
  call time;
- the node binder replaces twelve already-imported canonical helpers with
  call-time root closures, then installs the two shared input-type objects by
  identity, for 14 bound globals total;
- combined scope is 25 root-name slots, five direct dependency slots, and 19
  bind-time global installations;
- repository tests replace 14 names found in this family. The LoRA-specific
  migrations are in `tests/test_lora_preset.py` and the LoRA contract section
  of `tests/test_node_contracts.py`; replacements for other owner families do
  not move in this lane;
- root direct aliases for the metadata/preset helpers and shared input types
  remain consumed by other tests or owner families and are not retirement
  targets here; and
- metadata/preset internal recursion, logger access, prompt-token/prompt-
  correction callbacks, and node adapter helper calls all observe their
  current target at use time after the one-time root binder installation.

Allowed production files:

```text
nodes.py
easyuse_anima/lora/metadata.py
easyuse_anima/lora/preset.py
easyuse_anima/nodes/lora_nodes.py
```

Allowed supporting files are focused LoRA/node-contract tests, the Python
compatibility gate and fixtures, the nodes/backend analyzer baselines, and
these architecture documents.

Exit:

- root no longer imports or calls the three LoRA binders;
- canonical LoRA modules own their internal calls and canonical cross-module
  dependencies without importing root `nodes.py`;
- logger access and prompt-token/prompt-correction callbacks remain use-time;
- `_FlexibleOptionalInputType` and `_ANY_TYPE` retain exact canonical object
  identity;
- LoRA helper/class root aliases, node schema, workflow payloads, stack order,
  trigger order, error text, and optional dependency timing remain unchanged;
  and
- tests that previously replaced root only to drive LoRA canonical consumers
  replace the owning canonical module instead.

Forbidden:

- changing LoRA profile/metadata/model-discovery behavior, prompt correction,
  missing-model policy, schema/workflow serialization, logger message text, or
  optional imports;
- retiring root aliases used by another owner family; and
- including Prompt/Regional, AiO, or Wildcard/NAIA binder cleanup.

Implementation result:

- root imports/calls and the three canonical LoRA binder definitions are
  removed;
- metadata and preset internal helper calls resolve their canonical module
  globals at use time, while prompt tokenization and prompt correction remain
  lazy use-time callbacks to `prompt.fields`;
- `_RuntimeLoggerProxy` remains installed at module import and resolves the
  canonical logger at attribute access time;
- the LoRA node adapter keeps direct canonical helper imports and exact
  `_FlexibleOptionalInputType` / `_ANY_TYPE` identity;
- LoRA-specific root-patch tests now replace the canonical owner, while root
  aliases and replacements belonging to other families remain unchanged;
- the remaining root audit is 24 binders in three families: 12
  provider-then-root, ten root-only, and two explicit callbacks;
- `nodes.py` is 1,800 lines, down 20 lines from the B-11c30a base; and
- focused LoRA, contract, compatibility, and analyzer validation passes 61
  tests.

### B-11c30c — Prompt/Regional binder split gate

- **State:** COMPLETE on `dev` in PR #339 / `d0188b5`
- **Owner:** #184
- **Type:** Contract/gate

The production-free gate splits the ten Prompt/Regional binders into six
feature-service binders and four node-adapter binders. Symbols, callers,
resolver modes, bound globals, provider/root resolver names, direct
dependencies, and repository replacement evidence remain unchanged. The two
subgroups are separate Move and rollback units.

### B-11c30c1 — Prompt/Regional service binder retirement

- **State:** COMPLETE on `dev` in PR #340 / `4cc5cab`
- **Owner:** #184
- **Type:** Move
- **Base:** `dev@d0188b5e687164bdba817c9705c64e23c1262733`

Pre-edit inventory:

- six binders: Regional, Advanced, Conditioning, Artist Mix, Prompt Fields,
  and Prompt Correction;
- four root-only and two provider-then-root binders install 21 service globals;
- 55 root resolver slots cover 46 unique root names, while two provider slots
  retain `_encode_with_comfy_clip` and `_find_loaded_node_class`;
- three direct dependency slots cover `_resolve_comfy_host_helper` and
  `logger`; and
- repository tests replace 22 unique family names in six files. This is test
  migration evidence, not public root compatibility.

Allowed production files:

```text
nodes.py
easyuse_anima/prompt/regional.py
easyuse_anima/prompt/advanced.py
easyuse_anima/prompt/conditioning.py
easyuse_anima/prompt/artist_mix.py
easyuse_anima/prompt/fields.py
easyuse_anima/prompt/correction.py
```

Implementation result:

- root no longer imports or invokes the six binders, and their canonical
  definitions and bind-time placeholder state are absent;
- service-internal calls use canonical module globals and explicit canonical
  imports without importing root `nodes.py`; the still-legacy
  `wildcard_engine` owner remains a call-time import so direct package imports
  do not eagerly load NumPy before D-12;
- Artist Mix CLIP encoding and Conditioning loaded-node discovery resolve the
  existing E-07 provider directly at call time. The Comfy host ledger remains
  22 slots across 15 modules;
- root helper aliases retain direct canonical identity, while service-specific
  tests replace the owning canonical module;
- all four Prompt/Regional node-adapter binders remain unchanged for
  B-11c30c2;
- the remaining audit is 18 binders in three families: ten
  provider-then-root, six root-only, and two explicit callbacks; and
- `nodes.py` is 1,763 lines, down 37 lines from the B-11c30b base.

Forbidden:

- changing Prompt/Regional schema, workflow serialization, mapped-class
  identity, prompt/conditioning output, seed behavior, provider lookup order,
  warning-once state, or optional dependency timing; and
- retiring any of the four node-adapter binders or combining B-11c30c2.

### B-11c30c2 — Prompt/Regional node-adapter split gate

- **State:** COMPLETE in PR #341 / `6a21e26`
- **Owner:** #184
- **Blocker owner:** #167 / D-12
- **Type:** Contract/gate
- **Production changes:** none
- **Base:** `dev@4cc5cabe83d2ba87c700607edf72b4166b4da1ff`

Pre-edit inventory:

- four binders remain: two provider-then-root and two root-only;
- 84 bind-time global slots cover 61 unique names;
- 99 root resolver slots cover 71 unique names;
- two provider slots retain `_encode_with_comfy_clip`;
- four direct dependency slots cover `_FlexibleOptionalInputType` and
  `_resolve_comfy_host_helper`; and
- repository tests replace 26 unique family names. This remains migration-cost
  evidence, not public compatibility.

Split decision:

1. **B-11c30c2a Prompt Data / Classic Prompt:** two binders, 30 root resolver
   slots over 27 unique names, one provider slot, and no
   `_consume_reserved_wildcard_next_seed` dependency. This Move is READY.
2. **B-11c30c2b Advanced / Regional:** two binders, 69 root resolver slots over
   53 unique names, and one provider slot. Both build paths call the root-only
   `_consume_reserved_wildcard_next_seed`; this Move is BLOCKED by #167/D-12.

The c2b blocker may not be bypassed with a new callback setter/binder,
canonical-to-root import, copied reservation logic, or changed seed payload.
All four binders and production callers remain unchanged in this gate.

### B-11c30c2a — Prompt Data / Classic Prompt adapter Move

- **State:** COMPLETE in PR #342
- **Owner:** #184
- **Type:** Move
- **Base:** `dev@6a21e2667ea5eb8723346d44d8d913444f230b05`

Pre-edit inventory:

- `_bind_prompt_data_node_runtime` and `_bind_prompt_node_runtime` are the only
  owned binders; Advanced and Regional remain excluded;
- 12 bind-time global slots cover 12 unique names;
- 30 root resolver slots cover 27 unique names;
- Prompt Data has one E-07 provider slot for `_encode_with_comfy_clip` and one
  direct root dependency on `_resolve_comfy_host_helper`;
- repository tests replace 20 family slots over 17 unique names; this remains
  migration-cost evidence, not public compatibility; and
- neither binder resolves `_consume_reserved_wildcard_next_seed`.

Allowed production files are `nodes.py`,
`easyuse_anima/nodes/prompt_data_nodes.py`, and
`easyuse_anima/nodes/prompt_nodes.py`. This Move must preserve schemas, mapped
class identity, prompt and conditioning outputs, provider lookup order,
warning/error behavior, optional-dependency timing, and saved workflows. It
must not modify the Advanced/Regional adapters, seed reservation, or wildcard
behavior.

Implementation result:

- root no longer imports or invokes the two binders, and both canonical binder
  definitions plus their bind-time mutation state are absent;
- Prompt Data imports canonical prompt/AiO helpers directly and resolves CLIP
  encoding through the existing E-07 provider at call time;
- Classic Prompt uses canonical common/prompt helpers and the existing
  `anima_prompt`/`settings` fallback imports directly;
- root mapped classes retain direct canonical identity, and adapter tests now
  replace the canonical adapter/provider seam instead of root-only binder
  globals;
- the Comfy host ledger remains 22 slots across 15 modules;
- the remaining audit is 16 binders in three families: nine
  provider-then-root, five root-only, and two explicit callbacks; and
- `nodes.py` is 1,750 lines, down 13 lines from the B-11c30c2 base.

### B-11d — Final root shim

- **State:** BLOCKED by the remaining B-11c30 family Moves and the separate
  seed/Wildcard decision for the final non-provider function
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
COMPLETE: E-07b wiring and compatibility gate / PR #328

COMPLETE: B-11c29a max-resolution wrapper retirement / PR #329
COMPLETE: B-11c29b1 direct mapping lookup retirement / PR #330
COMPLETE: B-11c29b2 loaded lookup retirement / PR #331
COMPLETE: B-11c29c requirement helper retirement / PR #332
COMPLETE: B-11c29d CLIP wrapper retirement / PR #333
COMPLETE: B-11c29b3 general node lookup retirement / PR #334
COMPLETE: B-11c30 binder/resolver migration audit / PR #336
COMPLETE: B-11c30a Image/SAM3/Impact binder Move / PR #337
COMPLETE: B-11c30b LoRA binder Move / PR #338
COMPLETE: B-11c30c Prompt/Regional split gate / PR #339
COMPLETE: B-11c30c1 Prompt/Regional service binder Move / PR #340
COMPLETE: B-11c30c2 Prompt/Regional node-adapter split gate / PR #341
COMPLETE: B-11c30c2a Prompt Data / Classic Prompt adapter Move / PR #342
BLOCKED:  B-11c30c2b Advanced / Regional adapter Move (#167/D-12)
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
