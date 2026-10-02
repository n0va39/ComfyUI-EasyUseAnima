# LoRA preset trigger controls

Base: dev 104b1a71629555952fe8e3bda0ad31d3276c0bfa.

Goal: independently enable LoRA weights and each row's trigger words.
Scope: preset backend, frontend row/menu controls, profile normalization,
focused tests, and Korean/English node documentation.

## Compatibility contract

- Preserve node IDs, output slots, comma-separated trigger output, stack
  tuples, style prompts, and external-stack behavior.
- Missing or true `use_trigger_words` means enabled. Only false is stored by
  frontend normalization, retaining legacy profile snapshots.
- LoRA disabled: neither weights nor triggers. Trigger disabled: weights remain.
- Input stacks do not carry trigger flags. A consuming preset continues to read
  their metadata independently of the upstream preset's trigger output.
- The T+/T− row control and localized context menu edit the same profile field.
- Preserve the field across profile changes, file save/load, LoRA path repair,
  and workflow serialization. No file-format migration is required.

## External integration decision

Dedicated TriggerWord Toggle (LoraManager) synchronization is excluded at the
user's request. Its 1.2.1 implementation can reuse stored toggle values when
the connected runtime string becomes empty. Supporting arbitrary upstream
computations would require a separate external-node change. This feature adds
no external imports, patches, event bridge, or metadata endpoint.
The existing STRING output and metadata lookup remain available.

## Verification

Focused tests: legacy defaults, all-off, unchanged stack/style outputs, profile
snapshots, row pointer controls, and profile persistence. Verify workflow
save/reload and actual queued output on Legacy Canvas and Node 2.0, then finish
the required full gate. Stop on an incompatible persisted/output contract or
a failed stable test-instance update. User-instance installation and releases
are outside this task.

## Final validation (2026-10-02)

- Full workspace runner passed: 1,721 Python tests (3 existing skips), frontend
  semantic checks, 125 JavaScript syntax checks, TypeScript 6.0.3, and diff check.
- Isolated runtime: ComfyUI v0.38.0, frontend 1.53.6.
- Legacy Canvas and Node 2.0: real row-button clicks preserved enabled weights
  and strength while changing output from all words to one LoRA's words and
  then an empty string. All queues completed successfully.
- Saved workflow files were read back and reloaded; the disabled trigger flag
  survived, and changing profiles restored each profile's own trigger state.
- Node 2.0 setting restored; temporary model fixtures and test server removed.
- User installation, release, and external LoraManager integration not applied.
