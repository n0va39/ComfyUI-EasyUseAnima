# Custom Node Integration Guidelines

Use this guide when adding features that call another custom node pack, expose a
patched version of an upstream node, or add model-patch options such as Spectrum,
KJNodes, DAVE, or Impact Pack detailer stages.

## Integration Rules

- Treat external custom nodes as runtime dependencies, not Python package
  dependencies, unless their project explicitly ships an importable Python
  package for that use.
- Classify each external node pack as required or optional before implementation:
  - Required dependencies are needed for the documented default workflow path.
  - Optional dependencies are needed only for a selected backend, optimization,
    detailer, saver, or metadata feature.
- Optional dependencies must be guarded twice: lock or disable the UI control
  when the node class is absent, and sanitize queued `generation_settings` so a
  saved workflow cannot call the missing option without user action.
- Resolve external nodes through ComfyUI node classes at execution time with a
  clear missing-pack error that names the required node pack and repository.
- Do not copy upstream node internals into EasyUse Anima. Delegate to the node's
  public node method such as `patch`, `sample`, `save_files`, or `doit`.
- Keep the integration setting in versioned keyed JSON, not positional widget
  storage. Add a nested settings object for the feature, for example
  `model_patches.dave` or `model_patches.kj`.
- Normalize every new stored field on load. Clamp numeric values and preserve
  unknown future keys only when they are intentionally forwarded.
- Avoid adding a dependency path that always runs. Only call the external node
  when the selected mode or enabled option requires it.
- For MODEL patches, document and test the patch order. If an upstream node
  requires a specific order, preserve that order in code and docs.
- Clean up temporary patched model references after generation so ComfyUI can
  unload or reuse models without leak warnings.

## UI And Serialization

- Add the option to the DOM settings UI, not as a visible raw JSON field.
- Hide inactive option groups when a backend or toggle does not use them.
- Add meaningful tooltips for every exposed option in the supported frontend
  languages.
- Keep hidden JSON widgets serialized. Do not remove required hidden widgets
  from `node.widgets`.
- Saved image workflow reload must restore the same selected backend and option
  values.

## Documentation

When an integration is added or changed, update all relevant surfaces:

- `docs/development/<version>.md`: runtime path, dependency, and validation notes.
- `docs/nodes/*.md`: user-facing mode table and required node pack list.
- `docs/example_workflows/*.json`: `extra.easyuse_anima_workflow.required_node_packs`
  with `required_for_sample`, plus any in-workflow download/install notes.
- `docs/example_workflows/README.md`: sample workflow dependency summary when
  the sample uses the integration.
- `RELEASE.md`: release-facing summary when the integration is part of the
  planned release.

## Tests

Add focused tests for each integration:

- settings normalization accepts the new mode and stores defaults.
- missing dependency errors name the required custom node pack.
- dispatch tests prove only the selected backend or patch path is called.
- model-patch tests verify the exact model object passed to the sampler.
- workflow tests verify example metadata lists required node packs.

For live validation, sync changed runtime files to the active ComfyUI instance,
restart ComfyUI, check `/object_info`, and queue at least one small workflow for
each new execution path.
