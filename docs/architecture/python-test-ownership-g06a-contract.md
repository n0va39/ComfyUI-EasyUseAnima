# Python Test Ownership G-06A Contract

## Status and scope

- Status: completed G-06A Contract/gate.
- Owner: Issue #188.
- Production changes: none.
- Test moves or duplicates: none.
- Executable map: `tests/fixtures/python_test_ownership_contract.v1.json`.
- Direct gate: `tests/test_python_test_ownership_contract.py`.

G-06A names the smallest existing owner set needed to choose focused evidence. It does
not reclassify or relocate every historical test for cosmetic package symmetry.

## Ownership categories

Each of the 15 canonical feature packages plus the `runtime-bootstrap` composition
surface maps to all five roadmap categories:

| Category | Meaning |
| --- | --- |
| `pure_service_unit` | deterministic feature or service owner |
| `adapter_api_node_integration` | API, node, ComfyUI, or composition boundary |
| `migration_compatibility` | persisted migration, root alias, or lifecycle compatibility |
| `package_archive` | package/no-host import and shipped archive closure |
| `live_host` | host-visible matrix, executed only when its trigger changes |

Every group has an existing direct `unittest` owner for the first two categories.
Package/archive and live/host ownership is referenced through shared named matrices so
the same expensive or cross-cutting evidence is not duplicated per feature.

## Single-owner shared matrices

The fixture assigns exactly one owner to each matrix:

- AiO settings migration — `tests/test_aio_generation_migrations.py`;
- profile migration — `tests/test_profile_contract.py`;
- supported root compatibility — `tests/test_python_compatibility_surface.py`;
- package/no-host import closure — `tests/test_python_package_skeleton.py`;
- Registry archive surface — `tests/test_registry_scanner_safety.py`;
- triggered Legacy Canvas / Node 2.0 live evidence —
  `docs/development/browser-smoke-matrix.md`;
- triggered release/runtime terminal lifecycle smoke —
  `docs/architecture/python-api-papi01-e09-lifecycle-gate.md`.

A reference to the live matrix does not trigger it for every package change. The
repository test-escalation policy still requires live evidence only for a host-visible
boundary.

## Compatibility and lifecycle guards

New ordinary tests import the canonical owner. Tests that intentionally exercise a
supported root surface remain owned by the existing compatibility fixture/test; G-06A
does not silently convert those tests or claim that every historical root import is
ordinary feature ownership.

E-09 integration stays with:

- `tests/test_runtime_services.py` for service lifetime;
- `tests/test_python_bootstrap.py` for composition/initialize/shutdown integration;
- `tests/test_python_runtime_lifecycle_contract.py` for the fixed lifecycle contract;
- `tests/test_python_runtime_test_isolation_contract.py` for no-reload, private-state,
  and no-hot-reinitialize guards.

API registrar callbacks exercised by those tests do not move lifecycle ownership into
an API feature test.

## Runner and maintenance

The official Python runner remains `python -m unittest discover -s tests`; pytest is
not introduced. Adding a new top-level canonical package causes the ownership gate to
fail until its direct pure/service and adapter owners plus all five category mappings
are added. New matrices require one named existing owner and must be referenced by at
least one group.

Focused work selects the direct owner for the changed boundary, then escalates to a
shared matrix only when the matrix trigger applies. Package/live evidence is never
inferred from a same-name feature test.
