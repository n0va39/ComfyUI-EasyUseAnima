# Native AiO image output

- Owner issue: [#678](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/678)
- Runtime owner: `easyuse_anima.aio.native_image_output`
- Publication owner: `easyuse_anima.aio.native_output_publication`
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

The selected diffusion model, applied LoRAs, and `embedding:name` references in
the positive or negative prompt are resolved only through ComfyUI's model
inventory. Embedding subdirectories are supported; an extension may be omitted,
but an ambiguous basename or path-like value containing traversal components is
not hashed. ComfyUI's prompt parser supplies embedding attention weights, such
as `0.8` in `(embedding:styles/example:0.8)`.

SHA-256 values keep a 128-entry process cache and a bounded cross-session cache
at `easyuse_anima/cache/resource-hashes.v1.json` under ComfyUI's user-data
directory. Cache keys contain an opaque digest of the resolved path rather than
the path itself. A hit must match size, modification/change timestamps, device,
and file identity; uncached reads report byte progress through ComfyUI. Cache
files are size/schema validated and atomically replaced. Corruption or write
failure causes a safe recomputation, and no cache file is written beside a
model, LoRA, or embedding.

Locally calculated SHA-256 values use the first ten characters in the
A1111/Civitai-compatible fields. Manual hash and hash-bundle settings preserve
the supplied validated value, do not accept file paths, and cannot claim the
reserved locally owned `model` key.

Local hashes do not require network access. `Civitai data` is disabled by
default; explicitly enabling it adds remote resource descriptors, and enabled
Civitai Hash Fetcher rows resolve an AutoV3 value. Both paths use fixed
`https://civitai.com/api/v1` endpoints:

- no user-provided URL is accepted;
- redirects are disabled and normal TLS verification remains enabled;
- connect/read timeouts are bounded, and all Civitai paths in one save share a
  12-second wall-clock deadline plus a 16-request HTTP-call budget;
- response bodies are streamed with a 2 MiB hard limit;
- one AutoV3 row consumes one call for model search and, when matched, one more
  for its selected version; those calls share the same budget as local/manual
  resource enrichment;
- once either budget ends, remaining remote lookups are skipped and the image
  is still saved with hashes and metadata already available;
- a timed-out transport may finish on one daemon worker, but a process-wide
  single request slot prevents abandoned slow streams from accumulating;
- one save considers at most 32 distinct local or manual resources and at most
  32 enabled hash-fetcher rows before the stricter shared budgets apply;
- remote names and identifiers are length/control-character validated;
- a by-hash response is accepted only when one returned file contains an exact
  match for the requested full or short hexadecimal hash;
- successful lookups cache only a small validated hash string or descriptor in
  memory, after whitespace trimming and case normalization of cache keys;
- transport, HTTP, size, and parse failures are logged as metadata misses and
  never block image saving.

## Filesystem and failure contract

Templates are expanded before output-path validation. Both the output subfolder
and filename must remain relative to the active ComfyUI output root. The writer
rechecks the created folder's resolved path before use.

Batch and collision suffixes are allocated while holding a process lock. When
a workflow sidecar is required, both the image and JSON names participate in
collision checks. A late image or sidecar target is never overwritten: the
transaction treats it as a collision, preserves that file, reallocates the
remaining suffixes, and retries up to a bounded limit.

Images and sidecars are encoded through descriptors that stay open from
exclusive temporary-file creation through commit. Pillow never reopens a
temporary pathname. POSIX publication uses a bound directory descriptor and
same-directory no-replace hard links. Windows publication renames the open file
handle without replacement, retains a directory handle during the transaction,
and verifies the committed file handle's final parent before accepting it.
Temporary-name replacement and output-directory identity changes abort the
transaction. If either member of an image/sidecar pair fails, only files whose
identity belongs to that transaction are removed.

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
