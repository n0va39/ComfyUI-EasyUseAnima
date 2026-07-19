"""ComfyUI adapter for wildcard expansion."""

from __future__ import annotations

from ..common.serialization import _stable_change_key
from ..common.values import _single_value

try:
    from ...wildcard_engine import (
        MAX_SEED,
        PUBLIC_MAX_SEED,
        SEED_CONTROL_FIXED,
        SEED_CONTROL_INCREMENT,
        SEED_CONTROL_MODES,
        SEED_CONTROL_RANDOMIZE,
        WILDCARD_MODE_FIXED,
        WILDCARD_MODE_LABELS,
        WILDCARD_MODE_POPULATE,
        WILDCARD_MODE_REPRODUCE,
        WILDCARD_MODE_SEQUENTIAL,
        expand_wildcards,
        has_wildcard_syntax,
        next_seed,
        normalize_seed,
        normalize_wildcard_mode,
        wildcard_sources_signature,
    )
except ImportError:
    from wildcard_engine import (
        MAX_SEED,
        PUBLIC_MAX_SEED,
        SEED_CONTROL_FIXED,
        SEED_CONTROL_INCREMENT,
        SEED_CONTROL_MODES,
        SEED_CONTROL_RANDOMIZE,
        WILDCARD_MODE_FIXED,
        WILDCARD_MODE_LABELS,
        WILDCARD_MODE_POPULATE,
        WILDCARD_MODE_REPRODUCE,
        WILDCARD_MODE_SEQUENTIAL,
        expand_wildcards,
        has_wildcard_syntax,
        next_seed,
        normalize_seed,
        normalize_wildcard_mode,
        wildcard_sources_signature,
    )


WILDCARD_SEED_RANGE_NOTE = (
    f"Browser/public editing and next-seed range: 0..{PUBLIC_MAX_SEED}. The Python "
    "backend continues accepting uint64 values for legacy workflow validation, but "
    "values above the public maximum are best-effort in the browser because JavaScript "
    "may already have lost integer precision. Fixed does not intentionally advance a "
    "legacy value; increment, decrement, and randomize return the next seed to the "
    "public range."
)


class _FlexibleOptionalInputType(dict):
    def __init__(self, input_type):
        self.input_type = input_type

    def __getitem__(self, key):
        return (self.input_type,)

    def __contains__(self, key):
        return True


def _unbound_runtime(*_args, **_kwargs):
    raise RuntimeError("Wildcard node runtime dependencies are not bound.")


_get_workflow_node = _unbound_runtime
_consume_reserved_wildcard_next_seed = _unbound_runtime


def _bind_wildcard_node_runtime(*, get_workflow_node, consume_reserved_next_seed, expand, has_syntax, next_seed_value, normalize_seed_value, normalize_mode, sources_signature) -> None:
    global _get_workflow_node, _consume_reserved_wildcard_next_seed
    global expand_wildcards, has_wildcard_syntax, next_seed
    global normalize_seed, normalize_wildcard_mode, wildcard_sources_signature

    _get_workflow_node = get_workflow_node
    _consume_reserved_wildcard_next_seed = consume_reserved_next_seed
    expand_wildcards = expand
    has_wildcard_syntax = has_syntax
    next_seed = next_seed_value
    normalize_seed = normalize_seed_value
    normalize_wildcard_mode = normalize_mode
    wildcard_sources_signature = sources_signature


class EasyUseAnimaWildcard:
    """Expand Impact Pack compatible wildcard and dynamic prompt syntax."""

    DESCRIPTION = (
        "Expands EasyUse Anima wildcard files and dynamic prompt syntax, stores the populated "
        "result for saved workflows, and supports random, sequential, and reproduced output."
    )
    OUTPUT_TOOLTIPS = (
        "Expanded prompt text.",
        "Seed after applying the seed control option.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": (
                        "Source prompt expanded by Populate, Fixed, and Sequential modes. Syntax: "
                        "__name__; {a|b|c}; weighted N::item; {n$$...} or "
                        "{min-max$$separator$$...}; N#__name__; and nested combinations. Wildcard "
                        "names ignore case and support * glob collections. Only lines whose first "
                        "non-space character is # are removed as comments."
                    ),
                }),
                "populated_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": (
                        "Expanded-result cache. Reproduce processes this value through the wildcard "
                        "engine like Impact Pack, falling back to text when it is empty. Populate, "
                        "Fixed, and Sequential ignore the old cache, expand text, and write the "
                        "result here in saved workflow metadata."
                    ),
                }),
                "mode": (WILDCARD_MODE_LABELS, {
                    "default": WILDCARD_MODE_LABELS[0],
                    "tooltip": (
                        "Populate (일반 채우기): expand text with seed-based weighted random choices. "
                        "Fixed (고정): EasyUse compatibility mode; it still expands text, while a "
                        "fixed seed control keeps the same seed. Sequential (순차): choose from each "
                        "option/range with seed modulo its size and force the next seed to increment. "
                        "Reproduce (재현): process populated_text with the current seed, including "
                        "file wildcards, then cache that result; seed_after_generate still controls "
                        "the returned next seed. "
                        "Expanded runs are saved as populated_text in Reproduce mode."
                    ),
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": MAX_SEED,
                    "tooltip": (
                        "Seed for weighted random selection. Sequential uses seed modulo each option "
                        "count (and range width); Reproduce applies the seed to populated_text. "
                        f"{WILDCARD_SEED_RANGE_NOTE}"
                    ),
                }),
                "seed_after_generate": (SEED_CONTROL_MODES, {
                    "default": SEED_CONTROL_FIXED,
                    "tooltip": (
                        "Seed for the next live run: fixed keeps it, randomize chooses a new public-range "
                        "value, and increment/decrement move by one with wraparound. Sequential always "
                        "forces increment. Reproduce processes populated_text with the current seed "
                        "and applies this control to the returned/live next seed."
                    ),
                }),
            },
            "hidden": {
                "workflow_prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
            "optional": _FlexibleOptionalInputType("STRING"),
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("text", "seed")
    FUNCTION = "generate"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def _widget_input_names(cls):
        return tuple(cls.INPUT_TYPES().get("required", {}).keys())

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        mode = normalize_wildcard_mode(kwargs.get("mode", WILDCARD_MODE_LABELS[0]))
        seed_control = str(kwargs.get("seed_after_generate", SEED_CONTROL_FIXED) or "")
        text = str(kwargs.get("text", "") or "")
        if (
            mode in {WILDCARD_MODE_POPULATE, WILDCARD_MODE_FIXED, WILDCARD_MODE_SEQUENTIAL}
            and seed_control == SEED_CONTROL_RANDOMIZE
            and has_wildcard_syntax(text)
        ):
            return float("nan")
        return _stable_change_key({
            "mode": "wildcard",
            "wildcard_sources": wildcard_sources_signature(),
            **{key: str(value) for key, value in sorted(kwargs.items())},
        })

    @classmethod
    def _update_metadata_cache(
        cls,
        workflow_prompt,
        extra_pnginfo,
        unique_id,
        populated_text: str,
        mode: str,
        seed: int,
    ) -> None:
        node_id = _single_value(unique_id)
        if node_id is None:
            return
        node_id = str(node_id)
        updates = {
            "populated_text": populated_text,
            "mode": mode,
            "seed": int(seed),
        }

        if isinstance(workflow_prompt, dict):
            prompt_node = workflow_prompt.get(node_id)
            if isinstance(prompt_node, dict):
                inputs = prompt_node.setdefault("inputs", {})
                for name, value in updates.items():
                    inputs[name] = value

        workflow_node = _get_workflow_node(extra_pnginfo, node_id)
        if workflow_node is None:
            return

        input_names = cls._widget_input_names()
        widgets_values = workflow_node.setdefault("widgets_values", [])
        for name, value in updates.items():
            if name not in input_names:
                continue
            index = input_names.index(name)
            while len(widgets_values) <= index:
                widgets_values.append(None)
            widgets_values[index] = value

    @staticmethod
    def _ui(
        populated_text: str,
        mode: str,
        seed: int,
        status: str,
        used_keys: tuple[str, ...],
        missing_keys: tuple[str, ...],
    ):
        return {
            "wildcard": [{
                "populated_text": populated_text,
                "mode": mode,
                "seed": seed,
                "status": status,
                "used_keys": list(used_keys),
                "missing_keys": list(missing_keys),
            }]
        }

    def generate(
        self,
        text: str,
        populated_text: str,
        mode: str,
        seed: int,
        seed_after_generate: str,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
        **reservation_inputs,
    ):
        mode_key = normalize_wildcard_mode(mode)
        seed_value = normalize_seed(seed)
        used_keys: tuple[str, ...] = ()
        missing_keys: tuple[str, ...] = ()

        if mode_key == WILDCARD_MODE_REPRODUCE:
            expansion = expand_wildcards(
                str(populated_text if populated_text else text or ""),
                seed=seed_value,
                mode=mode_key,
            )
            output_text = expansion.text
            used_keys = expansion.used_keys
            missing_keys = expansion.missing_keys
            status = mode_key
            metadata_mode = str(mode or WILDCARD_MODE_LABELS[3])
        else:
            expansion = expand_wildcards(str(text or ""), seed=seed_value, mode=mode_key)
            output_text = expansion.text
            used_keys = expansion.used_keys
            missing_keys = expansion.missing_keys
            status = WILDCARD_MODE_SEQUENTIAL if mode_key == WILDCARD_MODE_SEQUENTIAL else mode_key
            metadata_mode = WILDCARD_MODE_LABELS[3]

        effective_seed_control = (
            SEED_CONTROL_INCREMENT
            if mode_key == WILDCARD_MODE_SEQUENTIAL
            else seed_after_generate
        )
        reserved_next_seed = _consume_reserved_wildcard_next_seed(
            reservation_inputs,
            workflow_prompt,
            unique_id,
            seed_value,
            mode_key,
            effective_seed_control,
        )
        next_seed_value = (
            reserved_next_seed
            if reserved_next_seed is not None
            else next_seed(seed_value, effective_seed_control)
        )
        self._update_metadata_cache(
            workflow_prompt,
            extra_pnginfo,
            unique_id,
            output_text,
            metadata_mode,
            seed_value,
        )
        return {
            "ui": self._ui(
                output_text,
                str(mode or WILDCARD_MODE_LABELS[0]),
                next_seed_value,
                status,
                used_keys,
                missing_keys,
            ),
            "result": (output_text, next_seed_value),
        }

__all__ = ("EasyUseAnimaWildcard",)
