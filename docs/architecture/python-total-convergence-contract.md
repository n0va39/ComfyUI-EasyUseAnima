# Python Total Convergence Contract

## Status and authority

- Status: PTC-01 through PTC-10 complete in the current change.
- PTC-09B base: `a281e3c5f6ee52e214dca89226aed69075810112`.
- Technical owner: Issue #593; parent architecture owner: Issue #185.
- Lifecycle authority: E-09 / Issue #187.
- Compatibility inventory: Issue #186 and
  [`python-compatibility-shims.md`](python-compatibility-shims.md).
- Machine-readable owners:
  `tests/fixtures/python_file_disposition_contract.v1.json` and
  `tests/fixtures/python_support_ownership_contract.v1.json`.

This Contract extends, rather than discards, FC-01 through FC-05. Those tasks completed
canonical ownership, role-aware imports, typed boundaries, API application composition
and E-09 lifecycle ownership. They did not classify every shipped Python file or make
large-module disposition a completion blocker.

The completion meaning is now stricter: every shipped production `.py` has one reviewed
role, final owner and disposition, every reviewed size exception has a final verdict,
and the repository root contains only the ComfyUI entrypoint. Legacy root and
`anima_prompt` import paths are intentionally retired after their callers and tests use
canonical modules. This import-path break is accepted; node IDs, workflows, settings,
profiles and HTTP behavior are not.

## Review verdict

`ROADMAP_EXTENSION_REQUIRED` is accepted with one user-directed correction.

- Retain the current 16-group import gate, canonical API application, root entrypoint,
  E-09 lifecycle and completed FC evidence.
- Make the former optional large-module lane blocking.
- Classify all 183 baseline production files explicitly.
- Add 16 responsibility-owned canonical modules through cohesive Move tasks.
- Delete the 9 non-entrypoint root modules and 7 `anima_prompt` compatibility modules
  after a canonical entrypoint/caller cutover.
- Do not keep a new compatibility facade merely to preserve the removed import paths.

PTC-10 corrects the final target to 181: 183 baseline files, plus 16 canonical targets,
minus 16 legacy compatibility files and the two unregistered node adapters that have no
production caller.

## Structural references

No external repository is a template. The pinned references establish useful and
rejected patterns only.

| Reference | Commit | Accepted | Rejected |
| --- | --- | --- | --- |
| [ComfyUI-Easy-Use](https://github.com/yolain/ComfyUI-Easy-Use/tree/595e0738a9e3f8d0d9c4d875461b2d2c9e7559c7) | `595e0738` | broad feature, node and route topology | root import-time configuration/file work and dynamic scanning |
| [ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack/tree/429d0159ad429e64d2b3916e6e7be9c22d025c3c) | `429d0159` | explicit companion custom-node boundary | root star imports, import-time workers and global server/model coupling |
| [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes/tree/eb356e6cd5dedac54bb84bc54b8da8f185fa8472) | `eb356e6c` | domain-grouped small related nodes | allowing a domain file to grow without an executable disposition |
| [rgthree-comfy](https://github.com/rgthree/rgthree-comfy/tree/6b76ee6f2c5a007710b5a16f97c94330d6ecc871) | `6b76ee6f` | independent files for complex public nodes and route families | import-time cleanup/scanning and weaker lifecycle ownership |

EasyUse Anima deliberately keeps stronger executable architecture gates, deterministic
registration, compatibility inventory during the migration, package/no-host proof and
the E-09 single lifecycle owner.

## Baseline and final disposition

| Disposition | Baseline files | Final files | Meaning |
| --- | ---: | ---: | --- |
| `permanent_entrypoint` | 1 | 1 | root `__init__.py` only |
| `cohesive_retain` | 155 | 155 | current canonical path and owner remain |
| `split` | 9 | 25 | current facade/class owner remains and 16 exact targets are added |
| `delete` | 18 | 0 | canonical callers replace legacy paths or prove an adapter unregistered and callerless, then files are removed |
| **Total** | **183** | **181** | zero unclassified shipped Python files |

The fixture lists all 183 baseline paths explicitly. It has no wildcard/default entry.
Each split records its exact targets, role, G-06 owner group, direct tests, task and
rollback unit. Each deletion records the canonical replacement owner, current
compatibility-registry key, caller-migration tests, task and rollback unit.

### Mandatory split boundaries

| Task | Current owner | Added canonical targets |
| --- | --- | --- |
| PTC-02 | `aio/generation_normalization.py` | `generation_normalization_core.py`, `generation_normalization_model.py`, `generation_normalization_stages.py` |
| PTC-03 | `aio/legacy_generation.py` | `legacy_detailer.py`, `legacy_upscale.py` |
| PTC-04 | `prompt/advanced.py`, `prompt/regional.py` | `advanced_fields.py`, `advanced_builder.py`, `regional_builder.py` |
| PTC-05 | `prompt/artist_mix.py` | `artist_mix_config.py`, `artist_mix_planning.py`, `artist_mix_conditioning.py` |
| PTC-06 | `nodes/naia_nodes.py` | `naia/random_prompt.py` |
| PTC-07A | Advanced and Regional node adapters | `prompt_advanced_execution.py`, `regional_conditioning_adapter.py` |
| PTC-07B | PromptData and Artist Mix node adapters | `prompt_data_conditioning_adapter.py`, `artist_mix_conditioning_adapter.py` |

Public node class definitions remain in their current canonical node modules. Helper
movement must not change class identity, `__module__`, registration mappings, socket
order or workflow class IDs.

### Mandatory legacy retirement

| Legacy path | Canonical replacement owner |
| --- | --- |
| `api.py` | `easyuse_anima/api/application.py` plus bootstrap-owned composition |
| `api_contract.py` | canonical `easyuse_anima/api` request/response/error modules |
| `autocomplete_dataset.py` | `easyuse_anima/autocomplete/dataset.py` |
| `autocomplete_index.py` | `easyuse_anima/autocomplete/index.py` |
| `nodes.py` | `easyuse_anima/registration.py` and symbol-owning canonical modules |
| `prompt_translation.py` | `easyuse_anima/translation/service.py` |
| `settings.py` | `easyuse_anima/settings/service.py` and repository/schema owners |
| `storage.py` | `easyuse_anima/infrastructure/filesystem/atomic_json.py` |
| `wildcard_engine.py` | `easyuse_anima/wildcard/service.py` and symbol-owning modules |
| `anima_prompt/` seven modules | matching `easyuse_anima/prompt/anima/` modules |

PTC-09B removes these paths only after production and test callers use canonical
owners. A deleted aggregator does not create a replacement aggregator: private helper
tests import the exact symbol owner, while ComfyUI loads the root `__init__.py` and
canonical registration/application owners.

## Size-exception closure

The original PTC-01 review classified 11 module and 20 function exceptions. Completed
PTC-02 through PTC-10 work resolved ten overages, so the current
`python_size_complexity_contract.v1.json` contains seven module and fourteen function
exceptions. All current 21 records are linked exactly once by ID and have completed
owners; the deleted root `nodes.py` and unregistered Impact node-adapter exceptions are
no longer in the active ledger.
The final verdict families are:

- split: AiO normalization and legacy orchestration, NAIA/Advanced/PromptData/Regional
  node adapters, Advanced/Artist Mix services, and Regional output construction;
- move then cohesive retain: DiT correction normalization, legacy USDU execution and
  Artist Mix config projection;
- cohesive retain: `bootstrap.initialize`, atomic JSON transaction, save-output stage,
  Spectrum sampling, Torch Compile recommendation, SAM3 detailer and declarative node
  schemas;
- delete after canonical cutover: root `nodes.py`.

The checker rejects an unlinked exception, a final owner outside the target plan, a
large retain without an executable direct contract, and any growth still rejected by
the existing size ratchet.

## Machine-readable rules

`tools/check_python_file_dispositions.py` reuses four authoritative sources:

1. `python_backend_baseline.json` for the shipped production inventory;
2. `python_test_ownership_contract.v1.json` for canonical role/test/package owners;
3. `python_size_complexity_contract.v1.json` for reviewed overages; and
4. `python-compatibility-shims.md` for current legacy surfaces.

It fails closed on:

- missing, duplicate or unclassified production paths;
- a planned target present without the task status update;
- a completed target missing from the analyzer inventory;
- owner-group ambiguity or an ownerless new target;
- target collisions;
- missing task, direct test or rollback for structural work;
- missing compatibility-registry linkage for a legacy deletion;
- any current size exception not classified exactly once; and
- new generic `util`, `utils`, `helper`, `helpers` or `misc` buckets.

Tests, tools, fixtures, runners and manual/live matrices remain support artifacts. PTC-08
classifies the exact 210-file support scope in
`python_support_ownership_contract.v1.json`. Each entry declares its kind, canonical
owner, concrete purpose, production group, execution mode and generated status. The
checker reuses the 16 G-06 production groups and its two manual-on-trigger matrices,
fails on an unclassified path or owner outside the inventory, and is registered once in
the official Python quality runner. Support files are not rearranged to mirror the
production package.

## Preserved contracts

Every implementation task preserves:

- public node IDs, display mappings, class definitions, input/output schemas and saved
  workflows;
- API routes, payloads, status/error mapping and request correlation;
- settings/profile/workflow schema, migrations, revisions and atomic persistence;
- deterministic registration and package/no-host imports;
- optional provider and external custom-node failure containment;
- repeated initialize runtime identity and route refresh;
- bootstrap as the only lifecycle owner, one lock, one atexit registration and terminal
  idempotent shutdown;
- the exact translation executor identity, executor shutdown as cleanup item 1, fixed
  seven-step cleanup, expected-identity rollback and original startup error; and
- no route deregistration/marker clear, file-I/O limiter cleanup, provider close, reset
  API or hot reinitialize.

Root/canonical object identity is preserved only until PTC-09B. After that task,
canonical identities and ComfyUI entrypoint behavior are preserved; removed root import
paths intentionally fail instead of silently recreating a compatibility layer.

## Ordered execution

```text
COMPLETE  FC-01 through FC-05
COMPLETE  PTC-01  total inventory, target and deletion Contract
COMPLETE  PTC-02 through PTC-07B behavior-preserving Moves
COMPLETE  PTC-08  size and support-ownership closure Contract
COMPLETE  PTC-09A root canonical-entrypoint/caller cutover Contract
COMPLETE  PTC-09B canonical cutover and 16-file legacy deletion
COMPLETE  PTC-10  total Python convergence audit and dead-adapter retirement
EVENT     ordinary release; no automatic compatibility shim recreation
```

One task is merged before the next starts. PTC-02 through PTC-07B are behavior-preserving
Move PRs. PTC-08 and PTC-09A are production-free Contracts. PTC-09B is one cohesive
entrypoint/import-surface change with a single rollback boundary. PTC-10 changes only
contracts, ledgers and current documentation unless it finds a production correction.
The audit found one: the two shipped standalone SAM3/Impact node adapters were neither
registered nor imported by production, while AiO already uses the canonical image and
resource owners. PTC-10 deletes both adapters and retains direct tests on those owners.

## Completed PTC-10 task card

```text
Task / Issue: #593 / PTC-10
Base SHA: 603a7bac1547fe0574c6a6d171724fa0a1dc6161
Goal: close the exact two runtime-unreachable shipped modules without synthetic imports
      or restoration of a retired root path.
Production deletion:
  easyuse_anima/nodes/impact_detailer_nodes.py
  easyuse_anima/nodes/sam3_nodes.py
Preserve:
  registration and locale surfaces; AiO SAM3 context/detailer behavior; canonical
  image/resource owners; import boundaries; package entrypoint; every E-09 invariant.
Focused evidence:
  canonical SAM3 services; node/Comfy adapters; analyzer/disposition/size/support;
  package skeleton; import boundaries; Registry scanner; locale non-registration.
Promotion:
  official full once; validate/pack/archive and extracted no-host import; reuse the
  PTC-09B isolated ComfyUI execution because no registered host-visible surface changes.
Rollback:
  revert the cohesive PTC-10 dead node-adapter retirement PR.
Result:
  shipped modules 181; runtime closure 181; unreachable shipped modules 0.
```

## Completed PTC-09A task card

```text
Task ID: PTC-09A
Owner: Issue #593, parent #185
Class: CONTRACT
Base: 5ab3f54c4d6eba930de5bf7a813d0fd89654ad01
Goal: select the one canonical entrypoint/application sequence that deletes the exact
      16 legacy paths while preserving every E-09 lifecycle invariant.
Allowed:
  docs/architecture/python-ptc09-root-cutover-contract.md
  current total-convergence roadmap/contract/compatibility/index status
Forbidden:
  production/test/tool/shared-fixture changes
  PTC-09B implementation, release/tag/Registry work
Preserve:
  production source and behavior, canonical identities, G-06 groups, E-09 lifecycle
Focused:
  targeted entrypoint/application/bootstrap/router/registration source consistency
  E-09 and FC-04 lifecycle Contract consistency
  exact 16-path disposition consistency
  git diff --check
Promotion:
  documentation-only; no official full
Package/live:
  not triggered
Rollback:
  revert the one PTC-09A documentation PR
Stop:
  multiple E-09-safe cutover shapes remain, or a supported legacy consumer requires
  retention of one of the exact 16 import paths
Next:
  PTC-09B cohesive canonical cutover and exact 16-file deletion
```

## Root cutover gate

PTC-09A resolves the exact E-09-safe sequence in
[`python-ptc09-root-cutover-contract.md`](python-ptc09-root-cutover-contract.md):

```text
ComfyUI imports root __init__.py
  -> root calls private bootstrap package startup
  -> bootstrap composes the canonical API application before initialize
  -> initialize receives the canonical registrar
  -> runtime cleanup plan observes the same translation executor as item 1
  -> repeated startup keeps one application/runtime and refreshes routes
```

The selected private bootstrap function is not public. Application construction remains
before and outside `initialize`; the obsolete root route-table mirror is replaced by a
stateless private sink, not another state cell. Root `api.py` and all other legacy paths
are deleted without replacement. No second lock, atexit, cleanup registry, reset API,
hot reinitialize, route deregistration or canonical-to-root import is introduced.

PTC-09B migrates root-importing tests to exact canonical owners, updates package and
ownership fixtures, changes root `__init__.py` to the selected canonical call, and
deletes the 16 legacy files. The post-cutover analyzer also exposes
`nodes/impact_detailer_nodes.py` and `nodes/sam3_nodes.py` as the exact two shipped
canonical modules outside the entrypoint runtime closure. PTC-10 must classify and
close that residual without reopening the retired root paths.

PTC-10 classifies both as callerless, unregistered node adapters and deletes them. The
public registration map already excluded `EasyUseAnimaSAM3Context` and
`EasyUseAnimaSAM3Detailer`; AiO retains SAM3 context loading in `aio/resources.py` and
detailer execution in `image/sam3_detailer.py`. The final analyzer has 181 shipped
modules, a 181-module runtime closure and zero unreachable shipped modules.

Because entrypoint, registration and archive closure change, PTC-09B requires official
full, validate/pack/archive, extracted no-host import and one representative isolated
ComfyUI API/node execution smoke.

## Final Definition of Done

- [x] Every shipped production `.py` is classified exactly once; unclassified count is
      zero.
- [x] The final target tree has 181 files: one root entrypoint and 180 canonical package
      files.
- [x] No root production `.py` remains except `__init__.py`; `anima_prompt/` is absent.
- [x] Every retained file has an exact role and G-06 owner.
- [x] Every split/delete has an implemented task, direct test and rollback unit.
- [x] All 31 originally reviewed size exceptions have a final verdict; every current
      ledger exception is linked exactly once and no unexplained overage remains.
- [x] No generic bucket or service locator is introduced.
- [x] All canonical production paths pass the role-aware import gate with no cycle.
- [x] Public node/workflow/API/data behavior and all E-09 invariants pass.
- [x] Support ownership has zero orphan test/tool/fixture/runner entries.
- [x] Official full passes once on the final candidate.
- [x] Validate, actual pack/archive/CRC/import closure and no-host import pass.
- [x] The root-entrypoint change passes representative isolated ComfyUI execution.
- [x] Release/tag/Registry evidence remains a separate release operation.
