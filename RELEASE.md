# Release Notes

## 0.1.6

### Added

- Added an autocomplete mode setting with `off`, `easyuse_nodes`, and
  `compatible_global` modes.
- Added shared frontend i18n helpers so custom DOM labels, buttons, tooltips,
  alerts, prompts, and settings follow the ComfyUI language setting.
- Added Korean custom-node locale definitions for node descriptions, input
  labels, input tooltips, output labels, and output tooltips.
- Added regression coverage for literal manual trigger text, LoRA trigger text,
  Advanced trigger fields, and Detailer Align Hook alignment values.

### Changed

- Prompt Studio Advanced now uses editor-level scrolling for long prompts
  instead of per-textarea vertical scrollbars.
- Prompt Studio highlight overlays copy more font metrics from the source input
  so highlights stay aligned when font settings differ.
- Autocomplete insertion, Prompt Studio previews, and Prompt Corrector output
  share the same prompt text rules.
- EasyUse Anima no longer exposes a separate language setting. UI language is
  selected from ComfyUI's own language setting.
- The 0.1.6 detailer scope is the Impact-compatible `Anima Detailer Align Hook`;
  SAM3 convenience-node cleanup and `MaskToSEGS` delegation cleanup were left
  out of this release scope.

### Validation

- `python -m unittest discover -s tests`
- `python -m compileall -q .`
- `git diff --check`
- `powershell -ExecutionPolicy Bypass -File tools\check_custom_node.ps1 -Project ComfyUI-EasyUseAnima`
- JavaScript syntax checks for EasyUse Anima frontend extensions
