"""ComfyUI adapter for bounded Civitai hash and AIR metadata lookup."""

from __future__ import annotations

import math

from ..aio.civitai_lookup import lookup_civitai_identifier


class EasyUseAnimaCivitaiLookup:
    """Identify a Civitai model version and return metadata for its selected file."""

    DESCRIPTION = (
        "Looks up a hex file hash or a versioned Civitai AIR. Returns metadata without "
        "downloading model files or requiring an API key. Hash lookups select the matching "
        "file; AIR lookups select the version's primary file."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "identifier": ("STRING", {
                    "default": "", "multiline": False,
                    "tooltip": "Hex hash or urn:air:ecosystem:type:civitai:modelId@versionId.",
                }),
            },
            "optional": {
                "weight": ("FLOAT", {
                    "default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01,
                    "tooltip": "Resource weight recorded in additional_hashes.",
                }),
            },
        }

    RETURN_TYPES = ("STRING",) * 7
    RETURN_NAMES = (
        "autov3_hash", "sha256", "air", "model_name", "version_name",
        "trigger_words", "additional_hashes",
    )
    FUNCTION = "lookup"
    CATEGORY = "EasyUse Anima/Image"
    OUTPUT_TOOLTIPS = (
        "AutoV3 hash of the selected file, when available.",
        "Full SHA256 hash of the selected file, when available.",
        "Versioned Civitai AIR identifier, when available.",
        "Civitai model name.",
        "Civitai model version name.",
        "Comma-separated trigger words.",
        "Name:hash:weight entry for Easy Image Metadata's additional_hashes input.",
    )

    def lookup(self, identifier: str, weight: float = 1.0) -> tuple[str, ...]:
        try:
            normalized_weight = float(weight)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("Civitai metadata weight must be a finite number from -100 to 100.") from exc
        if isinstance(weight, bool) or not math.isfinite(normalized_weight) or not -100 <= normalized_weight <= 100:
            raise ValueError("Civitai metadata weight must be a finite number from -100 to 100.")

        result = lookup_civitai_identifier(identifier)
        # The native additional_hashes parser uses commas and colons as delimiters.
        name = result.model_name.replace(":", " ").replace(",", " ").strip()
        if not name or name.casefold() == "model":
            name = "Civitai resource"
        additional_hashes = f"{name}:{result.resource_hash}:{normalized_weight}"
        return (
            result.autov3_hash, result.sha256, result.air, result.model_name,
            result.version_name, result.trigger_words, additional_hashes,
        )
