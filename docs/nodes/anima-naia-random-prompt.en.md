# Anima NAIA Random Prompt

Category: `NAIA Bridge/API`

Outputs:

- `prompt`
- `negative_prompt`
- `width`
- `height`

This node requests prompt, negative prompt, width, and height from the NAIA
remote API. It does not import or override `comfyui-naia-bridge`; it only uses
the same remote API style.

## Main Behavior

- `use_naia_bridge=false` bypasses NAIA and returns the input values as-is.
- `freeze_naia_output=true` reuses cached output when it is valid.
- `show_preview=false` hides the large read-only preview widget.
- The endpoint and Prompt Engineering values come from the global EasyUse Anima
  Settings. `Use Desktop Prompt Engineering` controls whether those global
  overrides are sent to NAIA.
- Saved-image workflows record cached output values with `freeze_naia_output=true`
  so reloaded workflows reproduce the same output.

## Notes

The `remove_*` preprocessing options are advanced inputs. The NAIA service must
expose the `POST /api/comfyui/random` endpoint.

The node still declares the legacy `use_naia_settings`, `pre_prompt`,
`post_prompt`, `auto_hide`, preprocessing, `host`, and `port` input names so
existing workflows keep the same schema. The front-end hides these compatibility
values and the backend does not use their stored values. Configure the endpoint,
Prompt Engineering, and remote API permission in the global EasyUse Anima
Settings. Remote hosts remain blocked unless the global `Allow Remote API`
security setting is enabled.
