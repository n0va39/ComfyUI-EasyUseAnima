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
tests/test_sam3_services.py
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
tests/test_sam3_services.py
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
tests/test_sam3_services.py
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
   53 unique names, and one provider slot. Both build paths call the root alias
   `_consume_reserved_wildcard_next_seed`. S167-01a / PR #344 supplies its
   canonical behavior-preserving owner; c2b is the next separate Move.

S167-01a does not bypass the boundary with a new callback setter/binder,
canonical-to-root import, copied reservation logic, or changed seed payload.
The two remaining c2b binders and production callers stay unchanged in that
owner Move.

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

### B-11c30c2b — Advanced / Regional adapter Move

- **State:** COMPLETE in PR #345
- **Owner:** #184, prerequisite #167 S167-01a
- **Type:** Move
- **Base:** `dev@b69d33857ef85fb81388f02e9ff1cff195a092d1`

Pre-edit inventory:

- `_bind_prompt_advanced_node_runtime` and `_bind_regional_node_runtime` are the
  only owned binders;
- 72 bind-time global slots cover 55 unique names;
- 69 root resolver slots cover 53 unique names;
- Regional owns the only provider slot, `_encode_with_comfy_clip`;
- three direct root dependency slots cover `_FlexibleOptionalInputType` and
  `_resolve_comfy_host_helper`;
- repository tests replace 21 family slots over 13 unique names; this remains
  migration-cost evidence, not public compatibility; and
- both real build paths call
  `easyuse_anima.seed.compatibility._consume_reserved_wildcard_next_seed`,
  whose behavior-preserving canonical owner was completed by S167-01a / PR
  #344.

Allowed production files are `nodes.py`,
`easyuse_anima/nodes/prompt_advanced_nodes.py`, and
`easyuse_anima/nodes/regional_nodes.py`. Gate, focused-test, and deterministic
fixture updates may touch only:

- `tests/test_node_contracts.py`;
- `tests/test_prompt_corrector.py`;
- `tests/test_prompt_studio_regional.py`;
- `tests/test_naia_settings.py`;
- `tests/test_nodes_module_analyzer.py`;
- `tests/test_python_compatibility_surface.py`;
- `tests/fixtures/comfy_host_compatibility.v1.json`;
- `tests/fixtures/python_backend_baseline.json`;
- `tests/fixtures/python_compatibility_surface.v1.json`;
- `docs/architecture/comfy-host-provider-bridge.md`;
- `docs/architecture/python-backend-execution-roadmap.md`; and
- `docs/architecture/python-compatibility-shims.md`.

This Move must preserve schemas, mapped-class and input-type identity, prompt
and Regional conditioning outputs, call-time Comfy provider lookup order,
NAIA and optional-dependency timing, seed reservation payloads and pop order,
wildcard seed arithmetic, warnings/errors, and saved workflows. It must not
add a callback/binder, import root `nodes.py` from the canonical package, copy
seed or Wildcard behavior, or begin S167-02 reservation behavior.

Implementation result:

- root no longer imports or invokes the two binders, and both canonical binder
  definitions plus their bind-time mutation state are absent;
- Advanced imports its canonical common, Prompt, seed, NAIA, workflow, and
  input-type owners directly. Its legacy settings fallback remains explicit,
  and the existing Prompt service's call-time Wildcard module resolver
  preserves the no-eager-NumPy boundary;
- Regional imports canonical Prompt/seed/workflow owners directly and resolves
  CLIP encoding through the existing E-07 provider at call time;
- tests that previously patched root only to drive Advanced or Regional now
  patch the canonical adapter owner;
- mapped classes and input types remain direct canonical identities, and seed
  reservation payload parsing remains owned by S167-01a;
- the Comfy host ledger remains 22 slots across 15 modules;
- the remaining audit is 14 binders in two families: eight provider-then-root,
  four root-only, and two explicit callbacks; and
- `nodes.py` is 1,662 lines, down 15 lines from the S167-01a base.

### B-11c30d — AiO binder split gate

- **State:** COMPLETE in PR #346
- **Owner:** #184
- **Behavior boundary:** #168 and #169
- **Type:** Contract/gate
- **Production changes:** none
- **Base:** `dev@1debd5c3ea75f1d14e66a3cfbba0e93e003f69cb`

Pre-edit inventory:

- twelve AiO binders remain: eight provider-then-root and four root-only;
- each binder mutates one `_RUNTIME_RESOLVER` slot, for twelve bind-time
  global slots over one unique name;
- 260 root resolver slots cover 187 unique names;
- thirteen provider slots cover `_comfy_max_resolution`,
  `_encode_with_comfy_clip`, `_find_comfy_node_class`,
  `_require_any_custom_node_class`, and `_require_custom_node_class`;
- eight direct root dependency slots all name
  `_resolve_comfy_host_helper`;
- repository tests replace 199 binder slots over 133 unique names in fourteen
  files. This is migration-cost evidence, not public compatibility;
- `easyuse_anima.aio.first_pass_cache` owns the actual cache dictionary, order
  list, and entry limit. Their object identity, ordering, eviction, cloning,
  and key semantics belong to the #169 behavior boundary; and
- `easyuse_anima.aio.legacy_generation` is the 59-root-slot orchestration
  consumer, while `easyuse_anima.nodes.aio_nodes` is the separate 30-slot
  public node adapter.

The production-free split is:

| Move | Owned binders | Root slots / unique | Provider slots | Direct slots | Replacement slots / unique |
| --- | ---: | ---: | ---: | ---: | ---: |
| B-11c30d1 cache state | 1 | 7 / 7 | 0 | 0 | 7 / 7 |
| B-11c30d2 normalization/planning | 3 | 72 / 66 | 1 | 1 | 37 / 31 |
| B-11c30d3 I/O boundary | 3 | 49 / 46 | 4 | 3 | 47 / 44 |
| B-11c30d4 execution services | 3 | 43 / 37 | 6 | 3 | 30 / 25 |
| B-11c30d5 legacy orchestration | 1 | 59 / 59 | 2 | 1 | 48 / 48 |
| B-11c30d6 node adapter | 1 | 30 / 30 | 0 | 0 | 30 / 30 |

Group ownership is exact:

- d1: `_bind_aio_first_pass_cache_runtime`;
- d2: `_bind_aio_generation_normalization_runtime`,
  `_bind_aio_usdu_planning_runtime`, and `_bind_aio_postprocess_runtime`;
- d3: `_bind_aio_resource_runtime`, `_bind_aio_preview_runtime`, and
  `_bind_aio_output_runtime`;
- d4: `_bind_aio_model_preparation_runtime`, `_bind_aio_sampling_runtime`, and
  `_bind_aio_conditioning_runtime`;
- d5: `_bind_aio_legacy_generation_runtime`; and
- d6: `_bind_aio_node_runtime`.

This gate may change only
`tests/test_python_compatibility_surface.py`,
`tests/fixtures/python_compatibility_surface.v1.json`,
`docs/architecture/comfy-host-provider-bridge.md`,
`docs/architecture/python-backend-execution-roadmap.md`, and
`docs/architecture/python-compatibility-shims.md`. Production files, runtime
binders, root imports/calls, schemas, settings, workflows, stage order, seed
resolution, cache behavior, model preparation, sampling, preview, save,
conditioning, provider lookup, and error text remain unchanged.

Each Move is a separate rollback unit. d5 cannot begin until its canonical
service dependencies are direct, and d6 remains last because the public node
adapter consumes the legacy orchestrator and service owners. No Move may begin
#169 stage/cache Behavior or combine the Wildcard/NAIA family.

The machine-readable gate records the exact, non-overlapping subgroup
membership and the per-group mode, root/provider/direct dependency, replacement
slot, and replacement-file counts. Later Moves consume that frozen subgroup
instead of reconstructing the full twelve-binder inventory.

Two import cycles require separate behavior-preserving prerequisite Moves:

1. **B-11c30d0a output settings owner:** move only
   `_normalize_aio_hash_bundles` and
   `_normalize_aio_civitai_hash_fetchers` from
   `easyuse_anima.aio.output` to the new pure
   `easyuse_anima.aio.output_settings` owner. This breaks the
   generation-normalization → output → sampling → generation-normalization
   cycle and unblocks d2 through d4.
2. **B-11c30d0b input context owner:** move only
   `_easy_use_anima_input_signature` and
   `_require_easy_use_anima_input` from
   `easyuse_anima.nodes.aio_nodes` to the new pure
   `easyuse_anima.aio.input_context` owner. This breaks the
   legacy-generation ↔ node-adapter cycle and unblocks d5 and d6.

Neither prerequisite is implemented in this Contract/gate. d1 has no blocking
cycle and is the first READY production Move. d0a may follow as a separate
Move before d2; d0b remains a separate Move before d5. The two prerequisite
Moves preserve existing root aliases and do not change normalization, input,
stage, seed, cache, provider, error, or workflow behavior.

### B-11c30d1 — AiO cache-state binder Move

- **State:** COMPLETE in PR #347
- **Owner:** #184
- **Behavior boundary:** #169
- **Type:** Move
- **Base:** `dev@7b25483c23fc3f430bf108fcb3ef23b6a64cd7e3`

Pre-edit inventory:

- root `nodes.py` imports `_bind_aio_first_pass_cache_runtime` in both package
  and flat-import paths and invokes it once with a root-global resolver;
- the binder installs one `_RUNTIME_RESOLVER` global. The canonical module
  resolves seven root names at call time:
  `AIO_FIRST_PASS_CACHE_MAX_ENTRIES`, `_AIO_FIRST_PASS_CACHE`,
  `_AIO_FIRST_PASS_CACHE_ORDER`, `_clone_aio_cache_value`,
  `_stable_change_key`, `_prompt_data_json_safe`, and
  `_aio_lora_stack_signature`;
- the entry limit, cache dictionary, order list, and recursive clone function
  are already owned by `easyuse_anima.aio.first_pass_cache`;
- the other three dependencies have canonical owners in
  `easyuse_anima.common.serialization`, `easyuse_anima.prompt.data`, and
  `easyuse_anima.aio.model_preparation`;
- the seven names are replaced across four repository test files, but only
  `tests/test_aio_first_pass_cache.py` uses root replacement to drive the cache
  owner. Replacements in legacy-generation, node-adapter, and preview tests
  belong to their still-active binder families and remain unchanged;
- root retains direct identity aliases for the limit, mutable state, clone,
  key, get, and put symbols. The previously retired private cache-clear alias
  remains absent; and
- mutable object identity, limit 2, key field order and values, recursive clone
  and CPU-failure handling, falsey miss, LRU refresh, overwrite, and
  oldest-first eviction are #169 Behavior and are frozen in this Move.

Allowed production files:

```text
nodes.py
easyuse_anima/aio/first_pass_cache.py
```

Allowed supporting files are `tests/test_aio_first_pass_cache.py`, the Python
compatibility gate and fixture, the nodes/backend analyzer gate and fixture,
and the three architecture documents.

Exit:

- root no longer imports or invokes the cache binder, and the canonical binder
  definition plus `_RUNTIME_RESOLVER` state are absent;
- the cache module uses its own state and recursive helper directly and imports
  the three canonical cross-module dependencies without importing root
  `nodes.py`;
- root cache aliases retain exact canonical object identity;
- tests that used root replacement to drive the cache owner replace the
  canonical owner instead;
- the frozen AiO split gate marks only d1 retired and keeps d2 through d6
  active; and
- cache behavior and the #169 boundary remain unchanged.

Forbidden:

- changing cache key schema/version/order, copy/clone policy, hit/miss
  semantics, eviction order/limit, cache scope, stage metadata, or performance
  policy;
- retiring root cache aliases or changing callers in the legacy-generation
  binder; and
- combining d0a, d2 through d6, Wildcard/NAIA, Contract, or Behavior work.

Implementation result:

- root no longer imports or invokes `_bind_aio_first_pass_cache_runtime`, and
  the canonical binder, `_RUNTIME_RESOLVER`, and `_runtime_helper` are absent;
- the cache owner directly uses its module-owned limit, dictionary, order list,
  and recursive clone function;
- `_stable_change_key`, `_prompt_data_json_safe`, and
  `_aio_lora_stack_signature` are direct imports from their existing canonical
  owners, with no root import or new callback seam;
- cache-specific tests replace the canonical owner while the root aliases
  retain exact object identity;
- the split gate now marks only d1 retired and retains d2 through d6 as the
  complete active AiO set;
- the remaining audit is 13 binders in two families: eight provider-then-root,
  three root-only, and two explicit callbacks;
- `nodes.py` is 1,657 lines, down 5 lines from the B-11c30d base; and
- focused cache, compatibility, nodes-analyzer, and backend-analyzer validation
  passes 45 tests.

### B-11c30d0a — AiO output-settings owner Move

- **State:** COMPLETE in PR #348
- **Owner:** #184
- **Behavior boundary:** #169
- **Type:** Move
- **Base:** `dev@66825e966ba5715e59c9f0cacf539fc8ad19e694`

Pre-edit inventory:

- `_normalize_aio_hash_bundles` and
  `_normalize_aio_civitai_hash_fetchers` are defined in
  `easyuse_anima.aio.output`; neither owns mutable module or process state;
- `easyuse_anima.aio.generation_normalization` resolves both names through its
  root runtime binder before normalizing the image-saver settings, while
  `easyuse_anima.aio.output` resolves both names through its own binder for
  save-time metadata assembly;
- root `nodes.py` imports both names from `easyuse_anima.aio.output` in package
  and flat-import modes and exposes exact identity aliases;
- `_normalize_aio_hash_bundles` depends only on JSON decoding and scalar/list
  filtering. `_normalize_aio_civitai_hash_fetchers` additionally resolves root
  `_as_bool` at call time; that root name is already an exact alias of the
  stateless canonical `easyuse_anima.common.values._as_bool`;
- direct function coverage is in `tests/test_aio_output.py`; normalized
  image-saver settings are covered by `tests/test_aio_generation_settings.py`,
  `tests/test_aio_nodes.py`, and `tests/test_aio_schema_contract.py`; and
- the only test-only replacement seam owned by these functions patches root
  `_as_bool`. It moves to the canonical owner seam when the runtime lookup is
  replaced by a direct import. Save-time output helper replacements remain on
  the still-active d3 binder and are not changed here.

Allowed production files:

```text
nodes.py
easyuse_anima/aio/output.py
easyuse_anima/aio/output_settings.py
easyuse_anima/aio/generation_normalization.py
```

Allowed supporting files are the focused output/generation tests, the Python
compatibility gate and fixture, the nodes/backend analyzer gate and fixture,
and the three architecture documents.

Exit:

- the two normalizers have one pure canonical owner in
  `easyuse_anima.aio.output_settings`;
- generation normalization imports them directly without creating the
  generation-normalization → output → sampling → generation-normalization
  cycle;
- output may re-export the exact owner objects for local compatibility while
  its d3 runtime binder remains active;
- root aliases retain exact canonical object identity in both import modes;
- normalization results, JSON fallback, filtering, field trimming, default
  boolean conversion, schemas, save behavior, and error text are unchanged;
  and
- d2 through d4 are unblocked without retiring any binder in this Move.

Forbidden:

- changing the accepted settings shape, normalization output, save metadata,
  dependency/provider behavior, errors, schemas, workflows, seeds, cache, or
  stage order;
- retiring the generation-normalization or output binder; and
- combining d2 through d6, d0b, Wildcard/NAIA, Contract, or Behavior work.

Implementation result:

- `easyuse_anima.aio.output_settings` is the sole definition owner for both
  normalizers and directly imports canonical `_as_bool`;
- `generation_normalization` imports both functions directly and no longer
  resolves either name through its runtime binder;
- `output` re-exports the exact owner objects while its save-time d3 binder
  calls remain unchanged;
- root imports both aliases directly from `output_settings` in package and
  flat-import modes, preserving exact object identity;
- the d2 gate drops two root-resolver slots and names plus one replacement slot
  and name, while all 13 remaining binders and d3 through d6 stay active;
- backend inventory grows from 89 to 90 shipped and reachable Python modules,
  with no missing internal imports; and
- one timeboxed focused process passes 82 output, generation, compatibility,
  nodes-analyzer, and backend-analyzer tests in 10.495 seconds.

### B-11c30d2 — AiO normalization/planning binder Move

- **State:** COMPLETE in PR #349
- **Owner:** #184
- **Behavior boundary:** #169
- **Type:** Move
- **Base:** `dev@7c5cd5c41a9a2b777c4acb9c5307b5ad1920692b`

Pre-edit inventory:

- the frozen d2 subgroup contains exactly
  `_bind_aio_generation_normalization_runtime`,
  `_bind_aio_usdu_planning_runtime`, and
  `_bind_aio_postprocess_runtime`;
- the three binders own only three `_RUNTIME_RESOLVER` slots. They account for
  70 root-resolver slots over 64 unique names, one
  `_comfy_max_resolution` provider slot, one direct
  `_resolve_comfy_host_helper` dependency, and 36 repository replacement slots
  over 30 names in nine test files;
- generation normalization owns its regex/set, seed/detailer/settings
  normalizers, and consumes the existing output-settings owner. Its remaining
  dependencies already have canonical owners in common values/serialization,
  Prompt Data/conditioning/artist mix, image scaling, Comfy capabilities,
  generation settings, and the E-07 host provider;
- root still owns `AIO_GENERATION_DEFAULT_SETTINGS` plus its generation schema,
  final-fit/upscale, USDU, and ResShift choice constants. The default payload is
  mutable compatibility state and must move with exact object identity. A new
  pure `easyuse_anima.aio.generation_defaults` data owner keeps this large
  declarative payload out of the normalization implementation;
- the default owner reads the existing seed-control/max values without changing
  Wildcard or seed behavior. No Wildcard function, reservation policy, or
  provider operation moves in d2;
- USDU planning resolves only `math.ceil`, geometry/value helpers, and its own
  tile-dimension function. Postprocess planning resolves only `math.sqrt`,
  logging, geometry/value/upscale helpers, and its own resize/final-fit
  functions;
- root imports all three binders in package and flat modes and invokes them
  consecutively during module initialization. Root aliases for every moved
  function and generation default/choice value remain compatibility surface;
  and
- focused call-time replacement assertions are concentrated in
  `tests/test_aio_generation_settings.py` and the generation/USDU/postprocess
  sections of `tests/test_node_contracts.py`. Replacements in output,
  legacy-generation, node-adapter, preview, and resource tests remain owned by
  their still-active binder families.

Allowed production files:

```text
nodes.py
easyuse_anima/aio/generation_defaults.py
easyuse_anima/aio/generation_normalization.py
easyuse_anima/aio/usdu.py
easyuse_anima/aio/postprocess.py
```

Allowed supporting files are the focused generation/USDU/postprocess tests,
the Python compatibility gate and fixture, the nodes/backend analyzer gate and
fixture, and the three architecture documents.

Exit:

- all three d2 binder definitions, root imports/calls, `_RUNTIME_RESOLVER`
  slots, and `_runtime_helper` functions are absent;
- generation defaults and choice constants have one pure data owner and root
  retains exact aliases to the same objects/values;
- generation normalization uses canonical feature/service dependencies and the
  E-07 provider directly, without importing root `nodes.py`;
- USDU and postprocess use canonical math/value/geometry/invocation owners and
  direct same-module calls;
- tests that patched root only to drive a d2 owner patch that canonical owner;
- d2 alone is marked retired while d3 through d6 remain the exact active AiO
  groups; and
- normalized payload order/values, input mutation/isolation, seed bounds,
  capability fallback, tile planning, resize/final-fit metadata, logging,
  schemas, workflows, stage order, and errors are unchanged.

Forbidden:

- changing generation defaults, validation/clamping choices, public schema,
  Wildcard/seed policy, cache, sampling, model preparation, conditioning,
  preview, save, stage order, provider interface, optional dependency timing,
  or error text;
- retiring any d3 through d6 or Wildcard/NAIA binder; and
- combining d0b, Contract, Behavior, performance, or formatting cleanup.

Implementation result:

- root and all three canonical modules no longer define, import, invoke, or
  retain the d2 binders, `_RUNTIME_RESOLVER`, or `_runtime_helper`;
- `easyuse_anima.aio.generation_defaults` is the sole owner of the mutable
  generation default payload, special-seed set, schema/version aliases, and
  final-fit/upscale/USDU/ResShift choices. Root and generation normalization
  import the exact same objects and values;
- generation normalization imports its stateless feature dependencies
  directly and keeps only `_comfy_max_resolution` behind the existing E-07
  call-time provider;
- USDU planning imports `ceil`, common values, and geometry directly.
  Postprocess planning imports `sqrt`, logging, common values, geometry,
  upscale invocation, and `LATENT_ALIGN` directly. Same-module planning calls
  no longer round-trip through root;
- d2-specific tests patch the canonical owner. Root replacements that drive
  d3 through d6 remain on those still-active families;
- the split gate marks d1 and d2 retired and leaves d3 through d6 as the exact
  active AiO set. The repository now contains ten binders total: eight AiO and
  two Wildcard/NAIA;
- backend inventory grows from 90 to 91 shipped and reachable Python modules,
  with no missing internal imports; and
- normalized defaults, key order, clamping, seed interpretation, provider
  observation time, USDU planning, postprocess resize/metadata/logging, schema,
  workflow, and stage behavior remain unchanged.

### B-11c30d3 — AiO I/O-boundary binder Move

- **State:** COMPLETE in PR #350
- **Owner:** #184
- **Behavior boundary:** #169
- **Type:** Move
- **Base:** `dev@fab74ef45837f0b8d05fe4f6b723b557b41f9f53`

Pre-edit inventory:

- the frozen d3 subgroup contains exactly `_bind_aio_resource_runtime`,
  `_bind_aio_preview_runtime`, and `_bind_aio_output_runtime`;
- the three binders own only three `_RUNTIME_RESOLVER` slots. They account for
  49 root-resolver slots over 46 unique names, four provider slots over
  `_find_comfy_node_class` and `_require_custom_node_class`, three direct
  `_resolve_comfy_host_helper` dependencies, and 45 repository replacement
  slots over 43 names in eight test files;
- resources owns input-settings normalization, Comfy resource lists/loaders,
  SAM3 context loading, and input-context resource loading. Its stateless
  dependencies already have canonical owners in common values, generation
  normalization, Comfy resource/invocation adapters, SAM3, and the E-07 host
  provider;
- root still owns `AIO_INPUT_DEFAULT_SETTINGS` plus its input schema/version,
  default resource candidates, CLIP types/devices, and UNet dtypes. The mutable
  default payload and related declarative values move with exact identity to a
  pure `easyuse_anima.aio.input_defaults` owner. The later d0b input-context
  Move remains separate;
- preview owns its stage/event/cache constants, filesystem/path inspection,
  event dispatch, temporary WebP save, and PreviewImage fallback. Optional
  `folder_paths`, NumPy, PIL, and PromptServer imports remain call-time, while
  node lookup stays behind the E-07 provider;
- output owns Image Saver/Civitai metadata adaptation and Comfy SaveImage
  invocation. It consumes the existing generation-defaults, output-settings,
  common values, LoRA formatting, seed-resolution, and E-07 provider owners
  directly; and
- d3-owner tests patch the canonical resource, preview, or output module.
  Replacements used to drive d4 through d6 remain on their still-active binder
  families.

Allowed production files:

```text
nodes.py
easyuse_anima/aio/input_defaults.py
easyuse_anima/aio/resources.py
easyuse_anima/aio/preview.py
easyuse_anima/aio/output.py
```

Allowed supporting files are the focused resource/preview/output and direct
adapter tests, the Python package/compatibility gate and fixture, the
nodes/backend analyzer gate and fixture, and the three architecture documents.

Exit:

- all three d3 binder definitions, root imports/calls, `_RUNTIME_RESOLVER`
  slots, and `_runtime_helper` functions are absent;
- input defaults and resource-choice constants have one pure data owner and
  root retains exact aliases to the same objects/values;
- resources imports canonical stateless dependencies directly and resolves
  only Comfy node lookup through the existing E-07 call-time provider;
- preview and output use canonical helpers and direct same-module calls while
  preserving optional dependency observation time and provider lookup;
- tests that patched root only to drive a d3 owner patch the canonical owner;
- d3 alone is marked retired while d4 through d6 remain the exact active AiO
  groups; and
- resource selection/loading, input payload order/values, preview paths/files,
  event payloads, WebP/PNG fallback, output metadata, save arguments, schemas,
  workflows, stage order, errors, and logs are unchanged.

Forbidden:

- changing input defaults, validation choices, loader selection, provider
  interface or lookup order, optional dependency timing, preview/save formats,
  metadata, filenames, event payloads, errors, schemas, workflows, seeds,
  cache, model preparation, sampling, conditioning, or stage order;
- moving the d0b input-context functions or retiring any d4 through d6 or
  Wildcard/NAIA binder; and
- combining Contract, Behavior, performance, or broad formatting cleanup.

Result:

- all three d3 binder definitions, resolver globals/helpers, and root
  imports/calls are absent;
- `easyuse_anima.aio.input_defaults` is the single pure owner of the mutable
  input-default payload and its declarative choices; root aliases preserve
  exact identity;
- resource, preview, and output owners use direct canonical dependencies,
  while optional I/O imports and E-07 Comfy host lookup retain call-time
  observation;
- d3 alone is retired. Seven binders remain: five AiO binders in d4 through d6
  and two Wildcard/NAIA binders;
- the compatibility surface contains 296 canonical root bindings, three
  residual root globals, and 92 shipped and reachable Python modules; and
- `nodes.py` is 1,182 lines, 11,481 fewer than the 12,663-line Phase A
  baseline (90.7% removed).

### B-11c30d4 — AiO execution-service binder Move

- **State:** COMPLETE in PR #351
- **Owner:** #184
- **Behavior boundary:** #168 and #169
- **Type:** Move
- **Base:** `dev@62e92e16b38b2b9cf521df474eaae7ccc1bf1ec8`

Pre-edit inventory:

- the frozen d4 subgroup contains exactly
  `_bind_aio_model_preparation_runtime`, `_bind_aio_sampling_runtime`, and
  `_bind_aio_conditioning_runtime`;
- the three binders own only three `_RUNTIME_RESOLVER` globals. They account
  for 43 root-resolver slots over 37 unique names, six provider slots over
  `_find_comfy_node_class`, `_require_custom_node_class`,
  `_require_any_custom_node_class`, and `_encode_with_comfy_clip`, three direct
  `_resolve_comfy_host_helper` dependencies, and 23 repository replacement
  slots over 21 names in six test files;
- model preparation has fourteen root-resolver names, three provider names,
  and one direct E-07 bridge. It owns twelve root identity aliases covering
  AuraFlow, KJ, DAVE, Safe PAG, Spectrum model patches, LoRA normalization and
  application, signature construction, and ephemeral-model cleanup;
- sampling has nineteen root-resolver names, two provider names, and one direct
  E-07 bridge. It owns eleven root identity aliases covering random/effective
  seeds, latent creation, Comfy/Spectrum sampling, VAE encode/decode, stage
  sampler settings, and highres backend selection;
- conditioning has ten root-resolver names, one provider name, and one direct
  E-07 bridge. It owns three root identity aliases covering Prompt Data field
  selection, the no-general prompt, and USDU conditioning;
- root imports all 26 canonical functions as exact package/flat aliases and
  imports/calls each binder once during module initialization;
- `easyuse_anima.aio.legacy_generation` is the production caller of the d4
  execution functions through its still-active d5 resolver. Direct d4 owner
  tests currently patch root to affect same-module calls, while d5/d6 tests
  also patch root aliases for their still-active binders; and
- model-management, Comfy node, Spectrum, KJ, DAVE, Safe PAG, seed, LoRA,
  Prompt Data, and CLIP behavior already have canonical stateless/provider
  owners. No new data, service, or callback contract is required.

Exact root-resolver names:

```text
model_preparation:
  _apply_aio_anima_dave_patch
  _apply_aio_kj_model_patches
  _apply_aio_safe_pag_patch
  _apply_aio_spectrum_correction_patch_for_comfy_sampler
  _apply_aio_spectrum_forecast_patch_for_comfy_sampler
  _as_bool
  _as_float
  _as_int
  _call_with_supported_kwargs
  _lora_stack_name
  _node_output_tuple
  _normalize_aio_lora_stack
  _patch_model_sampling_aura_flow
  logger

sampling:
  AIO_SPECIAL_SEEDS
  ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE
  ANIMA_MOD_GUIDANCE_PROFILE_OFF
  MAX_SEED
  SEED_CONTROL_FIXED
  _as_bool
  _as_float
  _as_int
  _call_with_supported_kwargs
  _json_clone
  _new_aio_random_seed
  _node_output_tuple
  _normalize_aio_seed
  _normalize_anima_mod_guidance_profile
  _resolve_aio_runtime_seed
  _sample_latent_with_comfy
  _sample_latent_with_spectrum_mod_guidance_advanced
  _sample_latent_with_spectrum_spd
  random

conditioning:
  AIO_USDU_PROMPT_FULL
  AIO_USDU_PROMPT_NO_GENERAL
  _advanced_artist_field_prompt
  _advanced_enabled_pane_fields
  _aio_prompt_data_fields_for_usdu
  _aio_usdu_prompt_without_general
  _as_bool
  _correct_advanced_field_sequence
  _normalize_advanced_fields
  _normalize_prompt_data
```

Allowed production files:

```text
nodes.py
easyuse_anima/aio/model_preparation.py
easyuse_anima/aio/sampling.py
easyuse_anima/aio/conditioning.py
```

Allowed supporting files are the focused d4 owner/caller tests, Comfy-host and
Python compatibility gates/fixtures, nodes/backend analyzer gates/fixtures,
and the three architecture documents.

Exit:

- all three d4 binder definitions, root imports/calls, `_RUNTIME_RESOLVER`
  globals, and `_runtime_helper` functions are absent;
- the three canonical modules import existing stateless owners directly, use
  direct same-module calls, and resolve only their existing E-07 host seams at
  call time;
- root keeps exact aliases for all 26 canonical execution functions;
- only d4 owner tests move their patch ownership to canonical modules. Root
  replacements that drive the still-active d5/d6 binders remain;
- d4 alone is retired while d5 and d6 remain the exact active AiO groups; and
- all model patch/cleanup, LoRA, seed, sampler/Spectrum, VAE, stage-setting,
  Prompt Data, conditioning, provider, error, log, schema, workflow, cache,
  and stage behavior remains unchanged.

Forbidden:

- changing patch order/kwargs, LoRA normalization/application, cleanup timing,
  seed/random semantics, backend selection, sampler/Spectrum/VAE invocation,
  SPD Euler normalization, stage sampler settings, prompt field selection,
  quality fallback, CLIP text, provider lookup, errors/logs, schemas,
  workflows, cache, or stage order;
- retiring d5, d6, or Wildcard/NAIA binders, or beginning d0b; and
- combining Contract, Behavior, performance, dependency, or broad formatting
  cleanup.

Result:

- all three d4 binder definitions, resolver globals/helpers, and root
  imports/calls are absent;
- model preparation, sampling, and conditioning use direct canonical
  stateless dependencies and same-module calls. The four existing E-07 host
  seams retain call-time provider observation;
- all 26 root execution aliases retain exact canonical identity, while only
  d4 owner tests moved patch ownership to canonical modules;
- d4 alone is retired. Four binders remain: the d5 legacy orchestrator, d6 node
  adapter, and two Wildcard/NAIA callback binders;
- the compatibility surface contains 293 canonical root bindings, three
  residual root globals, and 92 shipped and reachable Python modules; and
- `nodes.py` is 1,158 lines, 11,505 fewer than the 12,663-line Phase A
  baseline (90.9% removed).

### B-11c30d0b — AiO input-context owner Move

- **State:** COMPLETE in PR #352
- **Owner:** #184
- **Behavior boundary:** #168 and #169
- **Type:** Move
- **Base:** `dev@431fe632d1017db320a99ba3cdadb732973874cd`

Pre-edit inventory:

- `_easy_use_anima_input_signature` and
  `_require_easy_use_anima_input` are defined in
  `easyuse_anima.nodes.aio_nodes`. Neither function owns mutable module or
  process state;
- `_easy_use_anima_input_signature` reads no root data directly, but resolves
  `_prompt_data_json_safe` three times through the d6 node-adapter
  `_RUNTIME_RESOLVER`. `_require_easy_use_anima_input` has no dependency and
  preserves the exact validation order and error text;
- `EasyUseAnimaAIOGenerator.IS_CHANGED` is the signature caller through the
  still-active d6 resolver. `_run_aio_legacy_generation` is the required-input
  caller through the still-active d5 resolver;
- root `nodes.py` imports both functions from the node adapter in package and
  flat modes. Root and `easyuse_anima.nodes.aio_nodes` currently expose the
  same function objects, although neither private name is in the adapter's
  `__all__`;
- `easyuse_anima.prompt.data._prompt_data_json_safe` is the existing pure
  canonical dependency. A new `easyuse_anima.aio.input_context` owner can
  consume it directly without introducing a service, callback, provider, or
  new global;
- direct behavior and alias coverage is in `tests/test_aio_nodes.py`.
  `tests/test_aio_legacy_generation.py` replaces the root required-input alias
  to drive the still-active d5 binder; that single replacement must move to
  the direct consumer module when the production caller becomes direct; and
- the d5 legacy-generation and d6 node-adapter binders, their two
  `_RUNTIME_RESOLVER` globals, all other resolver slots, and the two
  Wildcard/NAIA callback binders remain outside this Move.

Allowed production files:

```text
nodes.py
easyuse_anima/aio/input_context.py
easyuse_anima/aio/legacy_generation.py
easyuse_anima/nodes/aio_nodes.py
```

Allowed supporting files are the focused AiO owner/caller tests, Python
compatibility and backend analyzer gates/fixtures, package-closure gate, and
the three architecture documents.

Exit:

- the two functions have one definition owner in
  `easyuse_anima.aio.input_context`;
- legacy generation and the node adapter consume that owner directly;
- the node adapter re-exports both functions and root imports the new owner in
  both import modes, preserving exact object identity;
- the legacy-generation ↔ node-adapter cycle edge is absent while d5 and d6
  remain active and otherwise unchanged; and
- input signature shape, JSON-safe conversion, validation order, error text,
  schemas, workflows, seeds, cache, stages, provider timing, and generation
  behavior remain unchanged.

Forbidden:

- retiring or otherwise changing the d5 or d6 binders;
- changing input schema, serialization, validation, errors, workflows, seed,
  cache, stage, provider, or generation behavior;
- beginning d5/d6 implementation, Wildcard/NAIA retirement, or #168/#169
  Behavior; and
- combining Contract, performance, dependency, or broad formatting cleanup.

Result:

- both helpers have one pure definition owner in
  `easyuse_anima.aio.input_context`, which imports only the existing canonical
  JSON-safe helper and owns no mutable state;
- legacy generation and the node adapter import the owner directly. The node
  adapter re-exports the same function objects, and root imports the owner in
  both package and flat modes;
- the d5 resolver drops `_require_easy_use_anima_input` and falls from 59 to
  58 root slots. The d6 resolver drops `_easy_use_anima_input_signature` and
  falls from 30 to 29 root slots;
- all four remaining binders stay active. Their combined audit contains 84
  unique resolver names, 82 root names, two provider names, and 69 repository
  replacement names across five files;
- root still contains 293 canonical bindings and three residual globals. The
  package grows to 93 shipped and reachable Python modules, while `nodes.py`
  is 1,162 lines because its two compatibility aliases now import their
  canonical owner directly; and
- focused input-context, node-adapter, legacy-generation, compatibility,
  package-closure, and analyzer gates preserve signature shape, JSON-safe
  conversion, validation/error behavior, object identity, and import closure.

### B-11c30d5 — AiO legacy-orchestration binder Move

- **State:** COMPLETE IN PR #353
- **Owner:** #184
- **Behavior boundary:** #168 and #169
- **Type:** Move
- **Base:** `dev@4409c17e87a8d7a06157c85ce38b72b8e3de5c39`

Pre-edit inventory:

- the frozen d5 subgroup contains exactly
  `_bind_aio_legacy_generation_runtime`;
- the binder owns one `_RUNTIME_RESOLVER` global and one `_runtime_helper`
  dispatcher. After d0b it accounts for 58 root-resolver slots over 58 unique
  names, two provider slots (`_encode_with_comfy_clip` and
  `_require_custom_node_class`), one direct `_resolve_comfy_host_helper`
  dependency, and 42 repository replacement slots over 42 names in
  `tests/test_aio_legacy_generation.py`, `tests/test_aio_nodes.py`, and
  `tests/test_node_contracts.py`;
- root imports the binder plus seven execution functions as exact package/flat
  aliases, then invokes the binder once during module initialization;
- `easyuse_anima.nodes.aio_nodes` is the sole production consumer of
  `_run_aio_legacy_generation` through the still-active d6 resolver. The other
  six stage functions are same-module orchestration calls and root
  compatibility aliases;
- direct canonical owners already exist for all 55 non-provider dependencies.
  They span common values and invocation, Prompt Data/conditioning/Artist Mix,
  AiO settings/cache/resources/model/sampling/conditioning/planning/preview/
  output/postprocess, image geometry/SAM3, and the two existing node adapters;
- `json`, `logger`, and `random` are currently root-resolved even though the
  canonical module can own the same standard-library/module-local objects;
  no process-global state or new service contract is required; and
- the legacy execution trace fixture freezes base generation and optional
  stage order, cache/cleanup timing, preview/save behavior, and returned
  metadata. Existing tests also freeze short circuits, exact errors,
  call-time provider observation, and package/flat root alias identity.

Exact root-resolver ownership:

```text
stdlib/module-local:
  json, logger, random
common/invocation:
  _as_bool, _as_float, _as_int, _single_value, _node_output_tuple
prompt:
  ANIMA_MOD_GUIDANCE_PROFILE_OFF
  _advanced_outputs_from_prompt_data
  _apply_spectrum_anima_mod_guidance
  _encode_prompt_data_positive_conditioning
  _normalize_anima_mod_guidance_profile
  _normalize_prompt_data
  _prompt_data_json_safe
  _resolve_anima_mod_guidance_enabled
aio generation/cache:
  AIO_USDU_PROMPT_FULL
  _aio_detailer_has_enabled_targets
  _aio_detailer_target_order
  _aio_first_pass_cache_key
  _get_aio_first_pass_cache
  _normalize_aio_generation_settings
  _put_aio_first_pass_cache
aio model/sampling/conditioning/planning:
  _aio_highres_effective_backend
  _aio_stage_sampler_settings
  _aio_usdu_conditioning
  _aio_usdu_tile_plan
  _apply_aio_lora_stack
  _apply_aio_model_patches
  _apply_aio_spectrum_model_patches_for_comfy_sampler
  _cleanup_aio_ephemeral_model
  _decode_latent_with_comfy
  _encode_image_with_comfy_vae
  _generate_empty_latent_with_comfy
  _resolve_aio_runtime_seed
  _sample_latent_with_aio_backend
aio resources/output/preview/postprocess:
  _aio_save_filename_prefix
  _load_aio_resources_from_input_context
  _load_aio_sam3_context
  _load_upscale_model_with_comfy
  _resize_image_to_size_if_needed
  _run_aio_postprocess_stage
  _save_aio_temp_preview_image
  _save_image_with_comfy
  _save_image_with_image_saver
  _send_aio_preview_event
  _tag_aio_preview_images
image/node adapters:
  EasyUseAnimaImageScaleByMultiple
  EasyUseAnimaSAM3Detailer
  _context_value
  _image_tensor_size
  _segs_has_items
same-module:
  _run_aio_detailer_stage
  _run_aio_detailer_target
  _run_aio_highres_stage
  _run_aio_resshift_upscale_stage
  _run_aio_upscale_stage
  _run_aio_usdu_upscale_stage
```

Allowed production files:

```text
nodes.py
easyuse_anima/aio/legacy_generation.py
```

Allowed supporting files are the three d5 replacement-owner tests, Comfy-host
and Python compatibility gates/fixtures, nodes/backend analyzer gates/fixture,
the frozen legacy execution trace assertion, and the three architecture
documents.

Exit:

- the d5 binder definition, root imports/call, `_RUNTIME_RESOLVER`, and
  `_runtime_helper` are absent;
- legacy orchestration imports existing canonical stateless owners directly,
  uses direct same-module calls, and owns standard-library logger/random/JSON
  access;
- the two E-07 host seams remain call-time provider-resolved;
- all seven root execution aliases retain exact identity;
- only d5 replacement ownership moves from root/binder injection to the
  canonical consumer module; and
- d6 and Wildcard/NAIA remain active while stage/cache/seed/provider/error/
  schema/workflow behavior and the execution trace remain unchanged.

Implementation result:

- the binder, resolver global/helper, root imports, and root initialization call
  are absent; all seven root execution aliases retain exact identity;
- the canonical orchestrator imports its existing stateless owners directly,
  uses direct same-module stage calls, and keeps both E-07 host seams
  call-time provider-resolved;
- d5 test replacements now target the canonical consumer, so tests no longer
  install or restore process-global resolver state;
- the active audit contains only d6 plus the Wildcard/NAIA callbacks: three
  binders, 29 unique resolver/root names, no provider-resolver slot, and 32
  replacement names across five files;
- the compatibility surface contains 291 canonical root bindings, three
  residual globals, 93 shipped/reachable Python modules, and a 1,147-line
  `nodes.py`; and
- the consolidated focused checkpoint ran 239 tests in 13.401 seconds. Its 237
  behavior/contract passes were retained; the two deterministic fixture/SHA
  gate drifts were updated and their exact closure tests pass.

Forbidden:

- retiring or otherwise changing the d6 or Wildcard/NAIA binders;
- changing stage order, cache keys/state/eviction, cleanup timing, preview/save
  order, seed/random semantics, sampler/model/conditioning behavior, provider
  lookup, optional dependency timing, errors/logs, metadata, schemas, or
  workflows;
- beginning #168/#169 Behavior, d6, or final root-shim work; and
- combining Contract, performance, dependency, or broad formatting cleanup.

### B-11c30d6 — AiO node-adapter binder Move

- **State:** COMPLETE IN PR #354
- **Owner:** #184
- **Behavior boundary:** #167
- **Type:** Move
- **Base:** `dev@cf772f1d8c0fe47999deb2af1a25621587717939`

Pre-edit inventory:

- the final active AiO subgroup contains exactly `_bind_aio_node_runtime`;
- the binder owns one `_RUNTIME_RESOLVER` global and one `_runtime_helper`
  dispatcher. After d5 it accounts for 29 root-resolver slots over 29 unique
  names, no provider or direct-root dependency, and 27 repository replacement
  slots over 27 names in `tests/test_aio_legacy_generation.py`,
  `tests/test_aio_nodes.py`, and `tests/test_node_contracts.py`;
- root imports the binder, both mapped classes (`EasyUseAnimaInput` and
  `EasyUseAnimaAIOGenerator`), and the two hidden-widget serializers
  (`_aio_input_settings_json` and `_aio_generation_settings_json`) as exact
  package/flat aliases, then invokes the binder once during module
  initialization;
- `easyuse_anima.registration` consumes the two mapped classes directly.
  ComfyUI calls their class methods, and `EasyUseAnimaAIOGenerator.generate`
  is the sole node-adapter caller of the canonical legacy orchestrator;
- the module also re-exports the two input-context helpers from their existing
  pure owner. Root already imports those helpers directly from input context,
  so their identity and ownership do not move here;
- all 29 resolver names already have canonical owners under common
  serialization, Prompt Data, AiO defaults/normalization/resources/model/
  sampling/input-context/legacy orchestration, or the Python `json` module;
  no provider, process-global state, service, or new contract is required; and
- existing tests freeze `INPUT_TYPES`, hidden JSON defaults, `IS_CHANGED`
  special-seed order, input context construction/copy boundaries, generation
  forwarding/signature, package/flat aliases, mapping identity, workflow
  serialization, and exact errors.

Exact root-resolver ownership:

```text
module/defaults/types:
  json
  AIO_GENERATION_DEFAULT_SETTINGS
  AIO_INPUT_DEFAULT_SETTINGS
  AIO_SPECIAL_SEEDS
  ANIMA_DEFAULT_CLIP_CANDIDATES
  ANIMA_DEFAULT_DIFFUSION_MODEL_CANDIDATES
  ANIMA_DEFAULT_VAE_CANDIDATES
  EASY_USE_ANIMA_INPUT_SCHEMA
  EASY_USE_ANIMA_INPUT_SETTINGS_VERSION
  EASY_USE_ANIMA_INPUT_TYPE
  PROMPT_DATA_TYPE
serialization/signature:
  _aio_generation_settings_json
  _aio_input_settings_json
  _aio_lora_stack_signature
  _copy_prompt_data_for_update
  _json_clone
  _stable_change_key
prompt/settings/resources:
  _normalize_prompt_data
  _prompt_data_json_safe
  _normalize_aio_generation_settings
  _normalize_aio_input_settings
  _comfy_clip_loader_types
  _comfy_diffusion_model_names
  _comfy_text_encoder_names
  _comfy_vae_names
  _preferred_clip_type_default
  _preferred_name_default
execution:
  _resolve_aio_runtime_seed
  _run_aio_legacy_generation
```

Allowed production files:

```text
nodes.py
easyuse_anima/nodes/aio_nodes.py
```

Allowed supporting files are the three d6 replacement-owner tests, Python
compatibility and backend/nodes analyzer gates/fixtures, workflow/package
contract coverage, and the three architecture documents.

Exit:

- the d6 binder definition, root imports/call, `_RUNTIME_RESOLVER`, and
  `_runtime_helper` are absent;
- the adapter imports existing canonical owners directly and owns JSON access;
- both mapped classes and the two serializer root aliases retain exact
  identity in package and flat-import modes;
- only d6 replacement ownership moves from root/binder injection to the
  canonical consumer module; and
- the AiO binder family is empty while Wildcard/NAIA remain the only active
  callback binders. Node inputs, change keys, seed reservation, context,
  generation, mappings, errors, schemas, and workflows remain unchanged.

Implementation result:

- `easyuse_anima.nodes.aio_nodes` imports the existing common, Prompt Data, AiO
  defaults/normalization/resources/model/sampling/input-context/orchestration
  owners directly and owns its existing JSON serialization locally;
- `EASY_USE_ANIMA_INPUT_TYPE` moves from the residual root assignment to the
  canonical node adapter, while root keeps an exact package/flat alias;
- d6 tests patch the canonical consumer instead of installing a process-global
  string resolver. The two mapped classes, hidden serializer aliases, input
  context, generation forwarding, and workflow contracts remain unchanged;
- `_bind_aio_node_runtime`, `_RUNTIME_RESOLVER`, and `_runtime_helper` are
  absent. All six AiO subgroups are retired, leaving only the two explicit
  Wildcard/NAIA callback binders in one active family;
- the active audit has zero string-resolver names, eight unique direct callback
  dependencies, and five repository replacement names across three files; and
- the compatibility inventory contains 291 canonical root bindings, two
  residual root globals, one root implementation import, 93 shipped/reachable
  Python modules, and a 1,142-line root shim.

Forbidden:

- retiring or otherwise changing the Wildcard/NAIA binders;
- changing hidden JSON shape/order/options, input/resource defaults, mutable
  settings or special-seed semantics, `IS_CHANGED`, context copies, generation
  forwarding, node signatures/IDs/mappings, errors, schemas, or workflows;
- beginning #167 Behavior, Wildcard/NAIA, final root-shim, Contract,
  performance, dependency, or broad formatting work.

### B-11c30e — Wildcard/NAIA callback-binder Move

- **State:** COMPLETE IN PR #355
- **Owner:** #184
- **Behavior boundaries:** #167, #236, D-12
- **Type:** Move
- **Base:** `dev@bc59822eb4f1141ffc3697aac352c5fc2c25a0f7`

Pre-edit inventory:

- the only remaining runtime family contains exactly
  `_bind_wildcard_node_runtime` and `_bind_naia_node_runtime`;
- both binders use explicit root-calling closures. They contain no string
  resolver, provider lookup, cache, I/O, or business-state owner;
- the Wildcard binder installs five module globals:
  `_get_workflow_node`, `expand_wildcards`, `normalize_seed`,
  `normalize_wildcard_mode`, and `wildcard_sources_signature`;
- the NAIA binder installs four module globals:
  `resolve_naia_settings`, `_get_workflow_node`, `_post_random`, and
  `_parse_random_response`;
- combined scope is nine direct callback slots over eight unique root names.
  The compatibility audit records five repository replacement names in
  `tests/test_wildcards.py`, `tests/test_naia_settings.py`, and
  `tests/test_node_contracts.py`;
- `easyuse_anima.workflow` already owns `_get_workflow_node`;
  `wildcard_engine` already owns the four Wildcard functions; `settings`
  already owns `resolve_naia_settings`; and `easyuse_anima.naia.client`
  already owns `_post_random` and `_parse_random_response`;
- the Wildcard adapter already imports its legacy engine in relative-package
  and flat fallback modes. The NAIA adapter already imports its client owner
  directly. This Move adds no new owner, service, provider, or contract;
- root imports both mapped classes and both private binder functions in package
  and flat modes, then calls each binder once during module initialization;
- `easyuse_anima.registration` consumes the two mapped classes directly; and
- existing tests freeze Wildcard source signatures, mode/seed normalization,
  expansion and metadata cache behavior, NAIA settings/request/response and
  frozen-output behavior, workflow lookup, exact class aliases, schemas,
  workflows, errors, and HTTP policy.

Allowed production files:

```text
nodes.py
easyuse_anima/nodes/wildcard_nodes.py
easyuse_anima/nodes/naia_nodes.py
```

Allowed supporting files are the three replacement-owner tests, Python
compatibility and backend/nodes analyzer gates/fixtures, workflow/package
contract coverage, and the three architecture documents.

Exit:

- both binder definitions and root imports/calls are absent;
- the adapters import their existing workflow, Wildcard, settings, and NAIA
  owners directly in supported package/flat modes;
- repository tests patch the canonical consumer or true owner rather than root
  callback installation;
- both mapped classes retain exact package/flat root identity;
- runtime binder families, binder calls, string resolvers, and callback
  installations all reach zero; and
- Wildcard modes/seeds/expansion/metadata, NAIA settings/HTTP/cache/result,
  node schemas/mappings, workflows, errors, and optional timing remain
  unchanged.

Implementation result:

- both adapters import `easyuse_anima.workflow._get_workflow_node` directly.
  Wildcard keeps its existing package/flat legacy-engine imports, while NAIA
  imports its existing settings owner with the same package/flat fallback and
  retains direct client imports;
- the two binder definitions and all nine bind-time callback installations are
  absent. Root no longer imports or invokes either binder;
- tests patch the canonical adapter dependency instead of the root callback
  seam. Root mapped-class identity, workflow lookup identity, Wildcard/NAIA
  behavior, and exact package/flat imports remain frozen;
- the runtime audit contains zero binders, families, resolver names, direct
  callback dependencies, and repository replacement names;
- the compatibility inventory contains 289 canonical root bindings, two
  residual root globals, one root implementation import, 93 shipped/reachable
  Python modules, and a 1,123-line root shim; and
- B-11d is the next separate root-shim Move.

Forbidden:

- moving or consolidating `wildcard_engine.py` or `settings.py`;
- changing Wildcard syntax, source discovery, seed/reservation, sequential,
  fixed/reproduce, populated-text, workflow metadata, or cache behavior;
- changing NAIA host policy, request body, response parsing, timeout, frozen
  output, settings, persistence, or errors;
- beginning #167/#236 Behavior, D-12/D-09 consolidation, final root-shim,
  Contract, performance, dependency, or broad formatting work.

### B-11d — Final root shim

- **State:** COMPLETE IN PR #356
- **Owner:** #184
- **Type:** Move

Pre-edit inventory:

- root `nodes.py` is 1,123 lines with two exact relative-package/flat-fallback
  import branches. It contains 289 canonical and 27 legacy direct bindings,
  including the 18 mapped supported class re-exports;
- the two unmapped class aliases are `EasyUseAnimaSAM3Context`, with documented
  historical convenience-node evidence, and unsupported/test-only
  `EasyUseAnimaSAM3Detailer`. ADR-002 keeps both outside the supported
  `__all__`; any future removal remains a separate per-alias review;
- all 297 unsupported/test-only symbols remain audited compatibility debt.
  B-11d does not mass-retire them because ADR-002 requires maintained-consumer
  migration, a published support window, archive evidence, and a separate
  reviewed removal unit;
- root owns zero functions, zero classes, zero binders/resolvers, and two
  residual assigned globals: `logger` and `_TRIGGER_WORD_KEYS`. The preamble
  `logging` import exists only for that unused root logger;
- root `__init__.py` exposes 18 mapped class attributes by importing the
  compatibility `nodes.py`, then imports mapping objects from pure
  `easyuse_anima.registration`, and performs one guarded bootstrap call;
- internal `easyuse_anima` package imports of root `nodes.py` are zero. The
  root package entrypoint is the only production path still consuming the shim;
- 21 repository test files import root `nodes.py`. Their explicit mapped-class
  and compatibility assertions remain allowed; test-only imports do not
  promote private aliases to supported API; and
- package mappings, display order, workflow fixtures, bootstrap idempotence,
  Registry scanner safety, package closure, and the root/canonical identity
  surface are already covered by checked-in gates.

Allowed production files:

```text
nodes.py
__init__.py
```

Allowed supporting files are the Python compatibility and nodes/backend
analyzer gates/fixtures, the public node contract coverage, and the three
architecture documents. Registry metadata, node behavior, canonical feature
modules, frontend files, and release versioning are outside this Move.

Implementation plan:

- remove only the unused root `logging`, `logger`, and `_TRIGGER_WORD_KEYS`
  implementation residue;
- add an explicit root `nodes.py.__all__` containing exactly the 18 mapped
  supported class names in registration order;
- make root `__init__.py` obtain its preserved class attributes from pure
  `easyuse_anima.registration`, not the compatibility shim;
- teach the compatibility gate to classify root `__all__` as shim metadata,
  require exact equality with the mapped classes, and require zero residual
  root implementation; and
- preserve every existing direct alias binding, object identity, package/flat
  fallback, mapping/display order, schema, workflow, error, and optional-import
  behavior.

Implementation result:

- root `logging`, `logger`, and `_TRIGGER_WORD_KEYS` are absent. The
  compatibility audit records zero preamble implementation imports and zero
  residual functions, classes, globals, binders, or resolvers;
- `nodes.py.__all__` contains exactly the 18 mapped classes in registration
  order. All 289 canonical and 27 legacy direct compatibility bindings remain
  unchanged outside that explicit supported surface;
- root `__init__.py` preserves all 18 class attributes through pure
  `easyuse_anima.registration` and no longer imports compatibility `nodes.py`;
- the backend analyzer treats the two shipped root entry modules,
  `__init__.py` and `nodes.py`, independently. All 93 shipped Python modules
  remain in the Registry runtime/archive closure with zero missing or
  unreachable modules;
- root `nodes.py` is a 1,138-line explicit compatibility shim. The added public
  export list accounts for the line increase from the pre-edit 1,123-line
  import-only surface; and
- focused compatibility, analyzer, node-contract, package-skeleton, and runtime
  tests pass without changing node behavior.

Validation result:

- the official full runner passed once: 986 Python tests and the frontend
  checks for 114 JavaScript files;
- `comfy node validate` and `comfy node pack` passed. The 225-entry archive
  contains exactly the 93 expected Python modules with zero missing or
  unexpected Python paths; and
- the isolated ComfyUI v0.27.0 instance exposed all 18 mapped node IDs. Two
  queued `EasyUseAnimaWildcard` executions with the same text and seed both
  completed successfully with the same `blue flower` result.

Exit:

- root `nodes.py` contains explicit supported direct re-exports and `__all__`;
- no node execution, host discovery, prompt processing, sampling, cache,
  preview, save, or metadata implementation remains;
- mapped class identity and workflow fixtures pass;
- registration remains pure;
- bootstrap/runtime initialization is idempotent;
- package-to-root production imports are zero;
- actual package/Registry archive closure passes; and
- representative live ComfyUI execution is recorded.

Forbidden:

- removing or promoting any of the audited private/test-only aliases;
- changing `NODE_CLASS_MAPPINGS`, display names/order, node schemas, workflows,
  class identity, package/flat import targets, or optional dependency timing;
- moving or consolidating `wildcard_engine.py`, `settings.py`,
  `prompt_translation.py`, or `anima_prompt`;
- changing bootstrap, route, wildcard initialization, runtime provider, seed,
  Wildcard, NAIA, Prompt, AiO, cache, or persistence behavior; and
- beginning #167/#169 Behavior, Phase D consolidation, release, dependency,
  performance, or broad quality cleanup.

S167-01a / PR #344 supplies the behavior-preserving reserved-seed owner, and
B-11c30c2b / PR #345 consumes it directly from both canonical adapters. The
root aliases remain compatibility surface; S167-02 Behavior is still separate.

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
COMPLETE: B-11c30c2b Advanced / Regional adapter Move / PR #345
COMPLETE: B-11c30d AiO binder split gate / PR #346
COMPLETE: B-11c30d1 AiO cache-state binder Move / PR #347
COMPLETE: B-11c30d0a output-settings owner Move / PR #348
COMPLETE: B-11c30d2 normalization/planning binder Move / PR #349
COMPLETE: B-11c30d3 I/O-boundary binder Move / PR #350
COMPLETE: B-11c30d4 execution-service Move / PR #351
COMPLETE: B-11c30d0b input-context owner Move / PR #352
COMPLETE: B-11c30d5 legacy-orchestration Move / PR #353
COMPLETE: B-11c30d6 node-adapter Move / PR #354
COMPLETE: B-11c30e Wildcard/NAIA callback binder Move / PR #355
COMPLETE: B-11d final root shim / PR #356

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
