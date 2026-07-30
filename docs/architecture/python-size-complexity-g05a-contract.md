# Python Size and Complexity G-05A Contract

## Status and scope

- Status: completed G-05A Contract/tool.
- Owner: Issue #188.
- Production behavior: unchanged.
- Metric owner: `tools/analyze_python_backend.py` schema 3.
- Blocking gate: `tools/check_python_size_complexity.py` through the ordinary Python
  quality runner.

G-05A is an incremental review ratchet. It is not a mandate to split a cohesive
module or function merely because a line trigger is exceeded.

## Metric and inventory ownership

The existing AST-only backend analyzer remains the only shipped-Python inventory. Its
module records now include deterministic function/method records with qualified name,
definition span, async/kind classification, and line count. Decorators are included in
the definition span; nested functions and methods are recorded; duplicate qualified
names receive a stable source-order suffix.

`python_size_complexity_contract.v1.json` is a compact projection containing only the
current reviewed overages. It is not a second file inventory. The initial line-based
review triggers are:

| Owner type | Trigger |
| --- | ---: |
| ordinary production module | 800 lines |
| API/node/composition/infrastructure adapter module | 400 lines |
| production function or method | 120 lines |

The adapter classification is deterministic: root `__init__.py`, `api.py`, `nodes.py`,
canonical bootstrap/registration, and canonical API, node, and infrastructure package
paths. Changing that classification is a contract change reviewed under Issue #188.

## Ratchet rules

- A current metric at or below its trigger passes without a ledger entry.
- A new over-trigger module/function fails until a reviewed exception names an owner
  issue and a concrete decomposition boundary.
- A reviewed overage may stay equal or decrease. Growth above its checked-in
  `baseline_loc` fails.
- Deleting or renaming a reviewed path or qualified function leaves a stale-ledger
  failure. A deliberate Move updates the ledger in the same reviewed PR.
- Raising a reviewed cap is an explicit fixture diff; it does not happen implicitly
  from analyzer regeneration.
- The checker does not read Git history, import production modules, or write state.

The initial G-05A contract is line-based. It does not invent a cyclomatic threshold or
authorize broad cleanup that the owning roadmap did not request.

## E-09 non-regression

`easyuse_anima/bootstrap.py` and `initialize` use Issue #187 as their reviewed owner.
Their decomposition boundary keeps the E-09 lifecycle lock, initialization, rollback,
fixed cleanup plan, repeated-initialize identity, terminal shutdown, and cleanup order
cohesive. G-05A therefore cannot be used to create a second lifecycle owner or a hot
reset/reinitialize API.

## Direct evidence and maintenance

- `tests/test_python_backend_analyzer.py` owns deterministic metric identity and the
  repository analyzer fixture.
- `tests/test_python_size_complexity.py` owns threshold, decrease, growth, new-owner,
  rename, and exception-metadata behavior.
- `tests/test_python_quality_contract.py` owns the exactly-once quality-runner call.

When production Python changes, run the checker before updating an exception. Ratchet a
decrease by lowering or removing the affected ledger record. For deliberate
over-trigger growth or a Move, update only the affected record with its reviewed
owner/decomposition evidence, then regenerate the analyzer fixture if the existing
analyzer contract requires it.
