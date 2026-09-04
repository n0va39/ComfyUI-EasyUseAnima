# Native AiO image output

- Owner issue: [#678](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/678)
- Runtime owner: `easyuse_anima.aio.native_image_output`
- Remote metadata owner: `easyuse_anima.aio.native_civitai`

The AiO Generator owns its rich image output path. It no longer imports or
looks up `ComfyUI-Image-Saver`. Existing settings remain compatible: the
serialized backend ID is still `image_saver`, and its settings object remains
at `save.image_saver`. The UI presents that compatibility ID as
`EasyUse Native`.

## Format contract

| Format | A1111 parameters | ComfyUI prompt/workflow | Loss controls |
| --- | --- | --- | --- |
| PNG | `parameters` text chunk | `prompt` plus `workflow` text chunks | optional PNG optimization |
| JPEG/JPG | EXIF `UserComment` | EXIF `Model`/`Make` fields | quality 1-100 |
| WebP | EXIF `UserComment` | EXIF `Model`/`Make` fields | quality 1-100 or lossless |

The writer owns the `parameters` and `prompt` metadata keys. Matching keys in
`extra_pnginfo` are ignored so caller-provided extras cannot replace the A1111
block or the serialized ComfyUI prompt.

`Save workflow JSON` writes the workflow as a same-stem UTF-8 JSON sidecar for
all formats. If JPEG EXIF would exceed its safe size, serialization first drops
the redundant execution prompt. If the payload is still too large, it removes
the embedded workflow, preserves the A1111 block, and forces the JSON sidecar
before any image is committed. If the A1111 block alone is too large, the save
fails without publishing an image.

ComfyUI's global `disable_metadata` flag suppresses A1111, prompt, workflow,
and sidecar metadata. It also skips local hashing and Civitai requests; the
image encoder still writes the selected format.

## A1111 and Civitai metadata

The human-readable `parameters` block contains the positive and negative
prompts, steps, sampler/scheduler mapping, CFG, seed, final dimensions,
denoising strength when applicable, clip skip, custom text, model name, model
hash, resource hashes, optional Civitai resource identifiers, and
`Version: ComfyUI`.

The selected diffusion model and applied LoRAs are resolved only through
ComfyUI's model inventory. SHA-256 values are cached in memory by resolved path,
size, and modification time; no cache file is written beside a model. The
first ten hash characters are written in the A1111/Civitai-compatible fields.
Manual hash and hash-bundle settings remain supported without accepting file
paths.

Local hashes do not require network access. `Civitai data` is disabled by
default; explicitly enabling it adds remote resource descriptors, and enabled
Civitai Hash Fetcher rows resolve an AutoV3 value. Both paths use fixed
`https://civitai.com/api/v1` endpoints:

- no user-provided URL is accepted;
- redirects are disabled and normal TLS verification remains enabled;
- connect/read timeouts are bounded;
- response bodies are streamed with a 2 MiB hard limit;
- one save performs remote enrichment for at most 32 local resources and processes at most 32 enabled hash-fetcher rows;
- remote names and identifiers are length/control-character validated;
- successful lookups cache only a small validated hash string or descriptor in memory;
- transport, HTTP, size, and parse failures are logged as metadata misses and
  never block image saving.

## Filesystem and failure contract

Templates are expanded before output-path validation. Both the output subfolder
and filename must remain relative to the active ComfyUI output root. The writer
rechecks the created folder's resolved path before use.

Batch and collision suffixes are allocated while holding a process lock. When
a workflow sidecar is required, both the image and JSON names participate in
collision checks. Images and sidecars are completed in same-directory temporary
files and atomically replaced. If a requested sidecar fails after the image is
committed, the just-created image is removed so the call does not report a
partial save.

The UI result retains ComfyUI's normal image record shape:
`filename`, output-root-relative `subfolder`, and `type: output`.

## Compatibility boundary

- `comfy_save_image` remains the built-in PNG alternative.
- Existing `image_saver` backend and `save.image_saver` profile/workflow data
  load without migration or silent backend changes.
- Existing serialized `download_civitai_data: true` values remain enabled; only
  new or missing settings use the safer disabled default.
- Filename templates, WebP/JPEG quality, lossless WebP, PNG optimization,
  workflow embedding/sidecars, manual hashes, Civitai rows, easy-remix, and
  custom metadata keep their existing setting keys.
- Historical standalone example workflows that contain explicit third-party
  Image Saver nodes still require that node pack; only current AiO examples
  remove it from their required-pack metadata.
