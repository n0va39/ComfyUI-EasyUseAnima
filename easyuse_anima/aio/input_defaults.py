"""Declarative defaults for the AiO input context."""

EASY_USE_ANIMA_INPUT_SCHEMA = "easy_use_anima_input"
EASY_USE_ANIMA_INPUT_SETTINGS_VERSION = 1

ANIMA_DEFAULT_DIFFUSION_MODEL_CANDIDATES = (
    "anima-base-v1.0.safetensors",
    "ANIMA\\anima_baseV10.safetensors",
)
ANIMA_DEFAULT_VAE_CANDIDATES = (
    "qwen_image_vae.safetensors",
)
ANIMA_DEFAULT_CLIP_CANDIDATES = (
    "qwen_3_06b_base.safetensors",
)
ANIMA_CLIP_TYPES = (
    "stable_diffusion",
    "stable_cascade",
    "sd3",
    "stable_audio",
    "mochi",
    "ltxv",
    "pixart",
    "cosmos",
    "lumina2",
    "wan",
    "hidream",
    "chroma",
    "ace",
    "omnigen2",
    "qwen_image",
    "hunyuan_image",
    "flux2",
    "ovis",
    "longcat_image",
    "cogvideox",
    "lens",
    "pixeldit",
    "ideogram4",
)
ANIMA_UNET_WEIGHT_DTYPES = (
    "default",
    "fp8_e4m3fn",
    "fp8_e4m3fn_fast",
    "fp8_e5m2",
)
ANIMA_CLIP_DEVICES = ("default", "cpu")

AIO_INPUT_DEFAULT_SETTINGS = {
    "schema": EASY_USE_ANIMA_INPUT_SCHEMA,
    "version": EASY_USE_ANIMA_INPUT_SETTINGS_VERSION,
    "resources": {
        "loader_mode": "split",
        "clip_loader": "single",
        "unet_weight_dtype": "default",
        "clip_device": "default",
    },
    "metadata": {},
}


__all__ = ()
