# Translation canonical package move

- Owner issue: [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186)
- Prerequisite behavior owner:
  [#164](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/164) — complete
- Roadmap unit: D-01
- PR type: Move
- Baseline: `dev@d002a9bea1b268d7a79d7c5bbd7c73f2a62f2d77`
- State: VALIDATED in PR #381
- Behavior changes: forbidden

## Responsibility boundary

The root `prompt_translation.py` currently combines four cohesive translation
responsibilities:

1. settings, provider, error, and limit contracts;
2. `%{...}` marker parsing;
3. the lazy Google provider adapter; and
4. provider reuse, bounded cache/single-flight state, and translation service.

D-01 moves that one feature surface under `easyuse_anima.translation` while
separating those responsibilities into `contracts`, `markers`, `providers.google`,
and `service`. This is one behavior-preserving Move, not a translation behavior,
async, cache, API, or dependency-policy change.

## Symbol inventory

Supported root compatibility symbols are the module-owned public constants,
types, classes, and functions:

- provider/default/marker constants:
  `PROMPT_TRANSLATION_PROVIDER_OFF`,
  `PROMPT_TRANSLATION_PROVIDER_GOOGLE`, `PROMPT_TRANSLATION_PROVIDERS`,
  `DEFAULT_PROMPT_TRANSLATION_SOURCE`, `DEFAULT_PROMPT_TRANSLATION_TARGET`,
  and `PROMPT_TRANSLATION_MARKER_LABEL`;
- service/provider limits:
  `MAX_PROMPT_TRANSLATION_MARKERS`,
  `MAX_PROMPT_TRANSLATION_MARKER_CHARACTERS`,
  `MAX_PROMPT_TRANSLATION_TOTAL_CHARACTERS`,
  `PROMPT_TRANSLATION_CACHE_MAX_ENTRIES`,
  `PROMPT_TRANSLATION_CACHE_TTL_SECONDS`, and
  `PROMPT_TRANSLATION_PROVIDER_TIMEOUT_SECONDS`;
- contracts and errors:
  `PromptTranslationSettings`, `PromptTranslationError`,
  `PromptTranslationLimitError`, `TranslationMarkerCountError`,
  `TranslationMarkerSizeError`, `TranslationTotalSizeError`,
  `TranslationProviderUnavailableError`, `TranslationTimeoutError`,
  `TranslationCancelledError`, `TranslationBusyError`,
  `TranslationUpstreamError`, `TranslationProvider`, and
  `TranslationCacheKey`;
- provider/service classes:
  `GoogleTranslationProvider`, `BoundedTranslationCache`, and
  `PromptTranslationService`; and
- functions:
  `normalize_prompt_translation_provider`,
  `normalize_prompt_translation_language`,
  `iter_prompt_translation_markers`,
  `has_prompt_translation_markers`, `get_translation_provider`,
  `google_translate_text`, `strip_prompt_translation_markers`, and
  `translate_prompt_markers`.

The root shim must list these names explicitly in `__all__` and bind each name
as the identical canonical object. It must not wrap, proxy, subclass, or use
`import *`.

Unsupported private/test-only seams are `_is_escaped`, `_looks_like_timeout`,
`_TRANSLATION_PROVIDER_FACTORIES`, `_TRANSLATION_PROVIDER_INSTANCES`,
`_TRANSLATION_PROVIDER_LOCK`, `_CACHE_MISS`, `_TranslationFlight`,
`_translate_segment`, and `_DEFAULT_TRANSLATION_SERVICE`. Canonical tests may
patch the owning canonical module; these private names are not added to the
root compatibility surface.

## Caller and alias inventory

Production consumers:

- `api.py`: public translation errors and `translate_prompt_markers`;
- `settings.py`: provider/default constants, settings type, and normalizers;
- `autocomplete_dataset.py`: `iter_prompt_translation_markers`;
- root `nodes.py`: marker detection and translation execution;
- `easyuse_anima.prompt.correction`: marker detection/execution; and
- `easyuse_anima.prompt.advanced`: marker detection.

D-01 changes these internal imports to precise canonical modules. Root
compatibility imports remain only for external/legacy consumers and direct
identity tests.

Test consumers:

- `tests/test_prompt_translation.py` currently imports the root module and
  patches root private/provider seams. It will become the canonical service and
  provider test, with a separate direct root/canonical identity assertion.
- `tests/test_prompt_translation_api.py` discovers the owner module through
  `translate_prompt_markers.__module__`; it must continue to observe the
  canonical service owner without changing route behavior.
- package, analyzer, import-boundary, and compatibility fixtures must reflect
  the new shipped modules and direct shim.

## Global state and lifecycle inventory

- Provider factories, provider instances, and their `RLock` are process-local
  service state. Provider construction remains lazy and one instance is reused
  per provider name.
- `GoogleTranslationProvider` owns one lazy client and one per-instance
  `RLock`; importing the module must not import `googletrans` or create a
  client.
- `BoundedTranslationCache` owns its ordered entries and lock.
- `PromptTranslationService` owns per-key single-flight entries and lock.
- The default service remains one process-local instance with the same bounded
  cache and single-flight behavior.
- No new initialize/shutdown policy is introduced in this Move; lifecycle
  ownership remains an E-04 follow-up.

## Allowed-file boundary

Production:

- `prompt_translation.py`;
- new modules under `easyuse_anima/translation/`;
- `api.py`, `settings.py`, `autocomplete_dataset.py`, and `nodes.py`, import
  lines only; and
- `easyuse_anima/prompt/correction.py` and
  `easyuse_anima/prompt/advanced.py`, import lines only.

Supporting:

- translation focused/identity tests;
- Python package skeleton, import-boundary, backend analyzer, and their exact
  fixtures;
- `docs/architecture/python-compatibility-shims.md`;
- this document; and
- `docs/architecture/python-backend-execution-roadmap.md`.

## Forbidden changes

- marker syntax, escaping, normalization, limit values, provider selection,
  timeout detection, error types/status/messages, HTML unescape, cache key,
  TTL/LRU, single-flight, deduplication, call order, or output text;
- API route, worker, response, request ID, cancellation, busy, timeout, or
  executor behavior;
- settings keys/defaults, node/workflow contracts, frontend, dependency
  metadata, Registry, release, or instance files;
- eager optional dependency import, client creation at import time, server,
  browser, model, or external translation calls; and
- D-02 or E-04 behavior/lifecycle work.

## Validation and exit

- focused translation service, API, package skeleton, compatibility identity,
  import-boundary, and backend analyzer tests;
- root/canonical identity for every supported `__all__` symbol;
- provider-off package import with no `googletrans` import/client creation;
- package/archive closure through the repository-owned gates;
- official full runner once at the PR checkpoint; and
- root `prompt_translation.py` contains only explicit direct re-exports,
  internal production translation imports are canonical, and all behavior
  fixtures remain unchanged.

## Validation result

- Focused translation service, API, package skeleton, import-boundary,
  corrector integration, nodes analyzer, and compatibility-surface checks
  passed.
- Focused Pyright passed with 0 errors for the new contracts and Google
  provider modules.
- The final official full runner passed: Pyright baseline ratchet, seven
  completed import-boundary groups, 1,129 Python tests, 112 frontend
  JavaScript files with TypeScript 6.0.3, and `git diff --check`.
- No server, browser, model, optional provider client, or external translation
  request was started.
