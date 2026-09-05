# Easy Save Image / Easy Image Metadata

These two nodes work with any ComfyUI diffusion workflow and use EasyUse's native
image writer. They do not require ComfyUI-Image-Saver.

Connect the final `IMAGE` to **Easy Save Image**. Choose the output subfolder,
filename without extension, PNG/JPG/JPEG/WebP format, and compression controls.
`quality` applies to JPEG/WebP; PNG is lossless. `lossless_webp` enables lossless
WebP and `optimize_png` trades encoding time for a smaller PNG. Existing images
and workflow sidecars are preserved using numbered filenames. The subfolder
must stay inside ComfyUI's configured output directory.

To include generation metadata, connect the same final `IMAGE` to **Easy Image
Metadata**, fill its positive/negative prompts, model name, seed, steps, CFG,
sampler, scheduler, denoise and optional CLIP skip/custom text, then connect
`exif_metadata` to the saver. Dimensions come from the final image. The optional
`parameters` text output exposes the generated A1111 parameters for inspection.
Model names are resolved only through ComfyUI's inventory for local hashes;
this node does not contact Civitai or load models. It records the values you
supply and does not infer sampling settings from the image pixels.
The metadata seed is recorded as supplied and never randomized after saving.

PNG stores `parameters` as text; JPEG and WebP store it in EXIF `UserComment`.
On **Easy Save Image**, `embed_workflow` includes the save execution's ComfyUI prompt and workflow, and
`save_workflow_as_json` writes a same-stem workflow JSON. A JPEG workflow that
exceeds EXIF capacity falls back to a sidecar; load that JSON to restore it.
These controls work independently of the metadata socket. Disconnect metadata
and turn both controls off to save pixels only. Easy Image Metadata retains only
A1111 generation data, with no workflow data or save options. Changing a saver's
workflow options does not invalidate the upstream metadata node's inputs.
ComfyUI's global `disable_metadata`
setting suppresses all metadata and sidecars, including previously cached node
metadata, and skips metadata resource hashing.

Existing pre-release workflows move their metadata node's workflow options to
connected savers on load. Previously disconnected savers keep both options off;
new savers default to workflow embedding on and JSON sidecars off. Existing API
prompts should move `embed_workflow` and `save_workflow_as_json` to saver inputs.

**Easy Civitai Lookup** accepts a model-file hash or a versioned Civitai AIR such
as `urn:air:sd1:checkpoint:civitai:4384@128713`. It outputs AutoV3, SHA256, AIR,
model/version names, trigger words and `additional_hashes`. Connect the latter
to Easy Image Metadata's `additional_hashes` socket to include resource hashes;
`weight` supplies that resource's recorded weight. The metadata node includes
these weights in the A1111 text's `Resource weights` JSON field, independently
of workflow embedding. Lookup does not load or download
models or images. It retains a bounded cache of selected text fields only and
reports unavailable resources or network errors rather than emitting false hashes.

The lookup uses Civitai's [model-version API](https://developer.civitai.com/site/reference).

The new nodes leave existing AiO settings and node identifiers unchanged.
See [native output contracts](../architecture/native-image-output.md) for the
shared path containment, publication and metadata limits.
