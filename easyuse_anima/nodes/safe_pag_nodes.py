"""Standalone Anima Safe PAG adapter; shares the AiO engine."""


class EasyAnimaSafePAG:
    DESCRIPTION = (
        "Applies Safe PAG to Anima/Cosmos/Predict2-style models without extra weights. "
        "Connect after the model loader (and DAVE if used), before the sampler. "
        "Temporarily perturbs selected self-attention blocks and restores them after inference."
    )
    OUTPUT_TOOLTIPS = (
        "Anima MODEL with Safe PAG guidance; original MODEL is preserved.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "scale": (
                    "FLOAT",
                    {
                        "default": 4.0,
                        "min": 0.0,
                        "max": 100.0,
                        "step": 0.1,
                        "round": 0.01,
                    },
                ),
                "block_indices": ("STRING", {"default": "18", "multiline": False}),
                "perturbation_strength": (
                    "FLOAT",
                    {
                        "default": 0.75,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.01,
                        "round": 0.001,
                    },
                ),
                "head_indices": ("STRING", {"default": "", "multiline": False}),
                "start_percent": (
                    "FLOAT",
                    {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.001},
                ),
                "end_percent": (
                    "FLOAT",
                    {"default": 0.7, "min": 0.0, "max": 1.0, "step": 0.001},
                ),
                "rescale": (
                    "FLOAT",
                    {"default": 0.2, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
                "rescale_mode": (["full", "partial"], {"default": "full"}),
            }
        }

    RETURN_TYPES = ("MODEL",)
    FUNCTION = "patch"
    RETURN_NAMES = ("model",)
    CATEGORY = "EasyUse Anima/Model Patches"

    def patch(
        self,
        model,
        scale=4.0,
        block_indices="18",
        perturbation_strength=0.75,
        head_indices="",
        start_percent=0.0,
        end_percent=0.7,
        rescale=0.2,
        rescale_mode="full",
    ):
        from ..aio.safe_pag import NativeSafePAG

        return NativeSafePAG().patch(
            model,
            scale,
            block_indices,
            perturbation_strength,
            head_indices,
            start_percent,
            end_percent,
            rescale,
            rescale_mode,
        )
