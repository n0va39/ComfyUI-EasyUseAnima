from __future__ import annotations

from typing import Any

from ..common.serialization import _json_clone, _json_object
from ..common.values import _as_bool, _as_float, _as_int, _choice
from ..infrastructure.comfy.capabilities import (
    _comfy_sampler_names,
    _comfy_scheduler_names,
    _impact_scheduler_names,
)
from ..infrastructure.comfy.wiring import resolve_comfy_host_helper
from ..prompt.artist_mix import (
    _bounded_artist_mix_float,
    _bounded_artist_mix_int,
)
from ..prompt.conditioning import _normalize_anima_mod_guidance_profile
from ..prompt.data import _prompt_data_json_safe
from ..seed.reservation import (
    SEED_CONTROL_FIXED,
    SEED_SELECTION_DECREMENT,
    SEED_SELECTION_INCREMENT,
    SEED_SELECTION_RANDOMIZE,
)
from .generation_defaults import (
    AIO_GENERATION_DEFAULT_SETTINGS,
    AIO_SPECIAL_SEED_RANDOM,
)
from .generation_defaults import (
    AIO_SPECIAL_SEED_DECREMENT as AIO_SPECIAL_SEED_DECREMENT,
)
from .generation_defaults import (
    AIO_SPECIAL_SEED_INCREMENT as AIO_SPECIAL_SEED_INCREMENT,
)
from .generation_defaults import AIO_SPECIAL_SEEDS as AIO_SPECIAL_SEEDS
from .generation_migrations import migrate_aio_generation_settings
from .generation_normalization_core import (
    merge_versioned_settings as _core_merge_versioned_settings,
)
from .generation_normalization_core import (
    migrate_supported_aio_generation_settings as _core_migrate_supported_settings,
)
from .generation_normalization_core import (
    normalize_aio_seed as _core_normalize_aio_seed,
)
from .generation_normalization_core import (
    normalize_aio_spectrum_settings as _core_normalize_aio_spectrum_settings,
)
from .generation_normalization_core import (
    normalize_prompt_settings as _core_normalize_prompt_settings,
)
from .generation_normalization_core import (
    normalize_sampler_settings as _core_normalize_sampler_settings,
)
from .generation_normalization_model import (
    _normalize_aio_dit_corrections_settings as _model_normalize_dit_corrections,
)
from .generation_normalization_model import (
    normalize_model_settings as _model_normalize_settings,
)
from .generation_normalization_stages import (
    AIO_DETAILER_CUSTOM_RE as _STAGES_AIO_DETAILER_CUSTOM_RE,
)
from .generation_normalization_stages import (
    AIO_DETAILER_RESERVED_KEYS as _STAGES_AIO_DETAILER_RESERVED_KEYS,
)
from .generation_normalization_stages import (
    aio_detailer_has_enabled_targets as _stages_detailer_has_enabled_targets,
)
from .generation_normalization_stages import (
    aio_detailer_target_defaults as _stages_detailer_target_defaults,
)
from .generation_normalization_stages import (
    aio_detailer_target_order as _stages_detailer_target_order,
)
from .generation_normalization_stages import (
    is_aio_detailer_target_name as _stages_is_detailer_target_name,
)
from .generation_normalization_stages import (
    normalize_stage_settings as _stages_normalize_settings,
)
from .generation_settings import (
    round_trip_aio_generation_settings as _round_trip_aio_generation_settings,
)
from .output_settings import (
    _normalize_aio_civitai_hash_fetchers,
    _normalize_aio_hash_bundles,
)

# Exact legacy backend clamp retained locally until the shared seed constants
# receive their own Contract lane. Importing wildcard_engine here would also
# import NumPy during side-effect-free package discovery.
MAX_SEED = 0xFFFFFFFFFFFFFFFF
SEED_CONTROL_MODES = (
    SEED_CONTROL_FIXED,
    SEED_SELECTION_RANDOMIZE,
    SEED_SELECTION_INCREMENT,
    SEED_SELECTION_DECREMENT,
)
_AIO_DETAILER_CUSTOM_RE = _STAGES_AIO_DETAILER_CUSTOM_RE
_AIO_DETAILER_RESERVED_KEYS = _STAGES_AIO_DETAILER_RESERVED_KEYS


def _missing_host_helper(name: str):
    raise RuntimeError(
        f"[EasyUseAnima] AiO generation normalization Comfy host helper is unavailable: {name}"
    )


def _comfy_max_resolution() -> int:
    helper = resolve_comfy_host_helper(
        "_comfy_max_resolution",
        _missing_host_helper,
    )
    return helper()


def _is_aio_detailer_target_name(name: str) -> bool:
    return _stages_is_detailer_target_name(name, custom_re=_AIO_DETAILER_CUSTOM_RE)


def _aio_detailer_target_defaults(target_name: str) -> dict[str, Any]:
    return _stages_detailer_target_defaults(
        target_name,
        default_settings=AIO_GENERATION_DEFAULT_SETTINGS,
        json_clone=_json_clone,
    )


def _aio_detailer_target_order(detailer_settings: dict[str, Any]) -> list[str]:
    return _stages_detailer_target_order(
        detailer_settings,
        is_target_name=_is_aio_detailer_target_name,
        reserved_keys=_AIO_DETAILER_RESERVED_KEYS,
    )


def _aio_detailer_has_enabled_targets(detailer_settings: dict[str, Any]) -> bool:
    return _stages_detailer_has_enabled_targets(
        detailer_settings,
        as_bool=_as_bool,
        target_order=_aio_detailer_target_order,
    )


def _normalize_aio_seed(value, default: int = AIO_SPECIAL_SEED_RANDOM) -> int:
    return _core_normalize_aio_seed(
        value,
        default,
        as_int=_as_int,
        max_seed=MAX_SEED,
        min_seed=AIO_SPECIAL_SEED_DECREMENT,
    )


def _merge_versioned_settings(defaults: dict[str, Any], value) -> dict[str, Any]:
    return _core_merge_versioned_settings(
        defaults,
        value,
        json_clone=_json_clone,
        json_object=_json_object,
        json_safe=_prompt_data_json_safe,
    )


def _migrate_supported_aio_generation_settings(value):
    return _core_migrate_supported_settings(
        value,
        migrate=migrate_aio_generation_settings,
    )


def _normalize_aio_spectrum_settings(
    value,
    defaults: dict[str, Any],
) -> dict[str, Any]:
    return _core_normalize_aio_spectrum_settings(
        value,
        defaults,
        as_bool=_as_bool,
        as_float=_as_float,
        as_int=_as_int,
        choice=_choice,
    )


def _normalize_aio_dit_corrections_settings(
    value,
    defaults: dict[str, Any],
) -> dict[str, Any]:
    return _model_normalize_dit_corrections(
        value,
        defaults,
        as_bool=_as_bool,
        as_float=_as_float,
        as_int=_as_int,
        choice=_choice,
    )


def _normalize_aio_generation_settings(value) -> dict[str, Any]:
    settings = _merge_versioned_settings(
        AIO_GENERATION_DEFAULT_SETTINGS,
        _migrate_supported_aio_generation_settings(value),
    )
    _core_normalize_sampler_settings(
        settings,
        as_bool=_as_bool,
        as_float=_as_float,
        as_int=_as_int,
        choice=_choice,
        json_clone=_json_clone,
        sampler_names=_comfy_sampler_names,
        scheduler_names=_comfy_scheduler_names,
        normalize_seed=_normalize_aio_seed,
        normalize_spectrum=_normalize_aio_spectrum_settings,
        normalize_corrections=_normalize_aio_dit_corrections_settings,
        seed_control_modes=SEED_CONTROL_MODES,
    )
    _model_normalize_settings(
        settings,
        as_bool=_as_bool,
        as_float=_as_float,
        as_int=_as_int,
        choice=_choice,
    )
    _core_normalize_prompt_settings(
        settings,
        as_bool=_as_bool,
        as_float=_as_float,
        as_int=_as_int,
        choice=_choice,
        normalize_mod_profile=_normalize_anima_mod_guidance_profile,
        bounded_artist_float=_bounded_artist_mix_float,
        bounded_artist_int=_bounded_artist_mix_int,
    )
    return _stages_normalize_settings(
        settings,
        as_bool=_as_bool,
        as_float=_as_float,
        as_int=_as_int,
        choice=_choice,
        sampler_names=_comfy_sampler_names,
        scheduler_names=_comfy_scheduler_names,
        impact_scheduler_names=_impact_scheduler_names,
        max_resolution_value=_comfy_max_resolution,
        target_order=_aio_detailer_target_order,
        target_defaults=_aio_detailer_target_defaults,
        normalize_spectrum=_normalize_aio_spectrum_settings,
        normalize_corrections=_normalize_aio_dit_corrections_settings,
        normalize_hash_bundles=_normalize_aio_hash_bundles,
        normalize_hash_fetchers=_normalize_aio_civitai_hash_fetchers,
        round_trip=_round_trip_aio_generation_settings,
    )


__all__ = ()
