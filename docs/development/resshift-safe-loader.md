# ResShift safe local model adapter (#679)

## Task card

- Class: ADAPTER. Base: `acd53db04bff571601a92efe379da4459b29176b` (dev).
- Goal: run AiO ResShift using locally selected checkpoints and ComfyUI safe loading.
- Owner: https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/679
- Allowed: ResShift loader/stage adapter, existing student selector labels, direct tests,
  backend inventory, and ResShift integration documentation.
- Preserve: node IDs, `upscale.resshift` keys, scale/dtype/tile/seed meanings, external
  inference, USDU and other stages. Spectrum remains an external dependency.
- Checks: model inventory containment, safe loading of both networks, metadata,
  missing/malformed models, stage dispatch and fixed-seed output; existing frontend
  dialog tests; full, package closure and isolated GPU/two-canvas smoke.
- Stop: do not fall back to unsafe deserialization, downloads or another backend.
  Report an unsupported external API/model or failed environment check explicitly.
- No release/version change or user-instance installation.

## Integration decision

The existing optional ResShift pack still owns the network definitions, inference
configuration and `ResShiftUpscale.upscale` operation. EasyUse owns selection and
safe checkpoint loading. For #679, this is a narrow exception to delegating model
loading to the external public node method: that method also performs downloads
and delegates checkpoint loading without an explicit safe-loading contract.
No upstream network implementation or model weights are copied into this package.

Both checkpoints must exist in ComfyUI's registered `resshift` model folders.
The student comes from the existing Student selector. The companion VQGAN file is
`autoencoder_vq_f4.pth`. Existing `(auto-download)` settings resolve locally to
`rsd_student_18k.safetensors` for x2 or `rsd_student_final.safetensors` for x4.
No network request is made by the AiO adapter, including when a file is missing.
Select the scale matching the student's training scale, as in the external node.

The adapter uses `comfy.utils.load_torch_file(..., safe_load=True)` for student
and VQGAN weights, including safetensors metadata and compatible weights-only
PyTorch checkpoints. Unsupported pickle objects fail without unsafe retry.
Paths must match the registered inventory and remain inside a registered root.

ResShift's own code/assets retain their licenses: its wrapper is CC BY-NC-SA 4.0
with an academic-use statement, and its vendored network and weights have S-Lab
non-commercial terms. Installing/selecting those separately does not change their
terms or relicense them under EasyUse's MIT license.

Validation results and the tested upstream commit will be recorded before PR completion.
