# Python Public API G-04A Coverage Audit

## Decision

G-04 is complete with the existing deterministic owners. No G-04B fixture or tool is
required.

The repository already separates three different contracts that a single replacement
snapshot would blur:

- the root compatibility and mapped-node surface;
- feature-owned serialized schema, result, and error contracts;
- the shipped Python archive and runtime import closure.

This audit records how those owners compose. It does not copy their node definitions,
payload schemas, or import graphs into another manifest.

## Required surface

| Required surface | Classification | Existing owner and direct evidence |
| --- | --- | --- |
| Permanent package entrypoint | covered / permanent | Root `__init__.py` declares exactly `NODE_CLASS_MAPPINGS`, `NODE_DISPLAY_NAME_MAPPINGS`, and `WEB_DIRECTORY`. `python_compatibility_surface.v1.json` and `PythonCompatibilitySurfaceTests` freeze the three-name `__all__` and their permanent-entrypoint classification. |
| Mapped node classes | covered / supported | `node_contracts_0_5_2.json`, `PublicNodeContractTests`, and the compatibility-surface fixture freeze the 18 mapped classes, display names, public root re-exports, and exact root/canonical object identity. The two intentionally unmapped implementation classes remain private/transitional and are not promoted to supported nodes. |
| Root and canonical `__all__` | covered | `PythonCompatibilitySurfaceTests` owns the root entrypoint and public node aliases. `PythonPackageSkeletonTests` imports the canonical package modules in isolation and checks every declared `__all__`, including the intentionally empty package surface and the explicit feature-module exports, without host imports or I/O side effects. `ApiContractCompatibilityTests` separately freezes the root/canonical API-contract identity and exports. |
| Settings, profile, and workflow schemas | covered / supported serialized boundary | The settings projection and long-text response owners, profile v2 envelope/list/mutation contracts, legacy additive-read tests, and the versioned node/workflow fixtures freeze the externally serialized shapes. Raw legacy/future workflow input remains the intentional migration/adapter boundary recorded by F-01. |
| API request, result, error, and correlation | covered / supported serialized boundary | API request/schema tests freeze parsing and response envelopes; profile and translation route tests freeze concrete mappings and the two named compatibility seams; request-correlation tests freeze `X-Request-ID`. The root/canonical API compatibility test preserves object identity without duplicating the payload schema. |
| Prompt, Wildcard, and Autocomplete | covered / supported serialized boundary | Prompt correction and Prompt Data owner tests freeze the typed models and serialized Advanced fields. Wildcard model/service/API tests freeze expansion results and list/source signatures. Autocomplete dataset/index/search/classification and API tests freeze source, status, search, and classification results. Raw host/workflow values stay intentional adapters. |
| AiO settings, request, state, and result | covered / supported serialized boundary | The v1-v4 settings and surface-coverage fixtures, `AIOGenerationConfigTests`, migration tests, and `AIOStagePipelineContractTests` freeze settings v4, typed request/state/stage ownership, migrations, and final serialization. ComfyUI model/tensor objects remain host adapter values. |
| Common feature errors | covered / supported semantic boundary | `python_feature_error_contract.v1.json` and `PythonFeatureErrorContractTests` cover the seven categories, 24 feature errors, 15 HTTP mappings, two explicit exclusions, and the named profile/translation compatibility seams. |
| Packed canonical/shim closure | covered | The generated backend analyzer fixture owns the shipped Python runtime-import closure and records no missing or unreachable shipped modules. `RegistryScannerSafetyTests` proves the package skeleton and API/autocomplete runtime files are tracked and not excluded by `.comfyignore`; package-skeleton imports prove the canonical modules load directly. Existing final package evidence is reused because G-04A changes no package or import surface. |

## Root-name classification

The executable compatibility fixture remains the single inventory owner:

- **permanent:** the three ComfyUI root entrypoint names;
- **supported:** the 18 mapped public node-class aliases with exact canonical identity;
- **transitional:** the fixture-owned compatibility names and the compatibility-ledger
  shims retained by current production, release-window, consumer, or rollback gates;
- **unsupported:** no additional root name is admitted to the supported surface; private
  implementation bindings and the two unmapped classes remain excluded.

This classification does not authorize deletion or deprecation. Retirement remains an
Issue #186 / ADR-002 decision after the relevant evidence gates.

## Gap assessment

There is no uncovered public surface that belongs in a new machine-readable owner.
Every F-01 handoff row maps to an existing deterministic fixture or direct contract,
and the archive closure is already analyzer-owned. A G-04B snapshot would only copy
schemas and identities whose current owners are more direct.

Result:

```text
G-04A COMPLETE
G-04B NOT REQUIRED
next: P-WC-01 wildcard pure-shim feasibility Contract
```

No production file, public export, payload, migration, package, release, or Registry
state changes in this audit.
