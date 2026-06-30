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
- `use_naia_settings=false` sends this node's `pre_prompt`, `post_prompt`,
  `auto_hide`, and preprocessing options to NAIA.
- Saved-image workflows record cached output values with `freeze_naia_output=true`
  so reloaded workflows reproduce the same output.

## Notes

The `remove_*` preprocessing options are advanced inputs. The NAIA service must
expose the `POST /api/comfyui/random` endpoint.
