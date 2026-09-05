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
`embed_workflow` includes the save execution's ComfyUI prompt and workflow, and
`save_workflow_as_json` writes a same-stem workflow JSON. A JPEG workflow that
exceeds EXIF capacity falls back to a sidecar; load that JSON to restore it.
Unconnected metadata saves pixels only. ComfyUI's global `disable_metadata`
setting suppresses all metadata and sidecars, including previously cached node
metadata, and skips metadata resource hashing.

The new nodes leave existing AiO settings and node identifiers unchanged.
See [native output contracts](../architecture/native-image-output.md) for the
shared path containment, publication and metadata limits.
