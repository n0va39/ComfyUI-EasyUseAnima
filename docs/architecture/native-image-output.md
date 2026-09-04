# Native AiO image output

- Owner issue: [#678](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/678)
- Runtime owner: `easyuse_anima.aio.native_image_output`
- Publication owner: `easyuse_anima.aio.native_output_publication`
- Remote metadata owner: `easyuse_anima.aio.native_civitai`
- Metadata budget owner: `easyuse_anima.aio.native_metadata_budget`
- JPEG import owners: `web/js/aio/jpeg_workflow_metadata.js` and
  `web/js/aio/jpeg_workflow_import.js`

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
`extra_pnginfo` are compared case-insensitively and ignored so caller-provided
aliases cannot replace the A1111 block, serialized ComfyUI prompt, or canonical
lowercase `workflow`. Keys beginning with an owned name plus `:` are reserved
too because EXIF serializes the key and JSON value with that delimiter.
Unrelated extra metadata is preserved.

`Save workflow JSON` writes the workflow as a same-stem UTF-8 JSON sidecar for
all formats. If JPEG EXIF would exceed its safe size, serialization first drops
the redundant execution prompt. If the payload is still too large, it removes
the embedded workflow, preserves the A1111 block, and forces the JSON sidecar
before any image is committed. If the A1111 block alone is too large, the save
fails without publishing an image.

## JPEG restore contract

ComfyUI frontend v1.49.6 does not route `image/jpeg` through its workflow
metadata parser. EasyUse therefore wraps the current `app.handleFile` function
with a chain-preserving JPEG-only adapter. A JPEG with valid EasyUse EXIF loads
the workflow first, or the API prompt when no valid workflow is present. The
filename, open source, and deferred-warning option are forwarded to the same
ComfyUI graph/API loaders used by the stock handler.

The adapter reads at most the first 256 KiB, accepts only a bounded JPEG APP1
EXIF segment, and rejects TIFF directories above 256 entries or field values
above 65,535 bytes. Invalid offsets, truncated segments, malformed JSON,
metadata-free JPEGs, and every non-JPEG input delegate to the exact previous
handler with the original receiver and arguments. PNG and WebP therefore stay
on ComfyUI's native parser path. Exact lowercase `workflow:` and `prompt:` EXIF
fields take priority over case-insensitive compatibility aliases regardless of
directory order. Malformed exact candidates do not hide a later valid exact
field, but the presence of any exact candidate disables alias fallback for that
field. Installation is idempotent and is skipped when
the host exposes a native `getJpegMetadata` capability or declares JPEG in its
handler metadata MIME types; the same capability is checked again for each
file so a later host upgrade also wins.

When the writer moves an oversized JPEG workflow to a JSON sidecar, the image
does not contain that workflow. Load the same-stem `.json` file directly to
restore it; dropping only the JPEG cannot reconstruct data that was deliberately
removed from EXIF.

## Metadata resource budgets

Workflow-controlled metadata is validated before Pillow or the publication
transaction receives it. JSON validation is iterative and rejects circular
data, nesting deeper than 64 levels, more than 100,000 values/keys, or any
single string above 1 MiB. Serialization uses bounded `iterencode` output rather
than materializing an already-known oversized JSON string.

| Payload | Limit |
| --- | ---: |
| A1111 parameters | 512 KiB |
| execution prompt JSON | 2 MiB |
| workflow JSON, embedded or sidecar | 4 MiB |
| aggregate `extra_pnginfo` JSON | 6 MiB and 128 top-level keys |
| embedded metadata per image | 8 MiB |
| embedded plus sidecar metadata per save batch | 64 MiB |

Cross-field and batch limits count repeated metadata for every image. Exceeding
a limit fails the save before image encoding/publication instead of silently
writing partial metadata. JPEG may still drop optional embedded prompt/extras
and preserve its workflow in a bounded sidecar. PNG and WebP retain no separate
pretty workflow string when a sidecar was not requested; their one compact
workflow representation is reused for embedded metadata.

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

One save performs at most 32 unique local resource lookup/hash attempts across
the selected model, applied LoRAs, and embedding references. Missing resources
consume the same budget as successful lookups, repeated embedding requests are
deduplicated before lookup, and the ComfyUI embedding inventory is indexed once
per save.

SHA-256 values keep a 128-entry process cache and a bounded cross-session cache
at `easyuse_anima/cache/resource-hashes.v1.json` under ComfyUI's user-data
directory. Cache keys contain an opaque digest of the resolved path rather than
the path itself. A hit must match size, modification/change timestamps, device,
and file identity; uncached reads report byte progress through ComfyUI. Cache
files are size/schema validated and atomically replaced. Corruption or write
failure, including excessively nested JSON, causes a safe recomputation, and no
cache file is written beside a model, LoRA, or embedding.

Locally calculated SHA-256 values use the first ten characters in the
A1111/Civitai-compatible fields. Manual hash and hash-bundle settings preserve
the supplied validated value, do not accept file paths, and cannot claim the
reserved locally owned `model` key.

Saved hash-bundle and Civitai-fetcher JSON is limited to 512 KiB before parsing.
Normalization examines at most 64 candidates and retains the first 32 valid
rows in order. A hash-bundle row and the final joined hash text are each limited
to 8 KiB of UTF-8; joining keeps only complete comma-delimited rows. Only string
field values are accepted. Civitai fields remain limited to 200 Unicode code
points and 800 UTF-8 bytes and reject malformed surrogates plus Unicode control,
format, and line-separator characters. The Save dialog applies the same limits
before creating controls or serializing edited rows. Failure logs replace those
unsafe characters and show no more than 80 characters from an untrusted field
or exception.

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

Template inputs and rendered results are limited to 1,024 characters, and the
time-format setting is limited to 256 characters. Every custom time, padded
counter, and fixed placeholder substitution checks its projected result length
before constructing that intermediate string. Time formats are rendered in
bounded segments after rejecting excessive numeric field widths, and integer
placeholders verify their decimal digit count before string formatting. Repeated
large replacement values therefore cannot amplify beyond the accepted template
budget.

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
