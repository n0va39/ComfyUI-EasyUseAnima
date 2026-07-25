
# pyright: strict
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TypeAlias, cast

JsonScalar: TypeAlias = None | bool | int | float | str
JsonNumber: TypeAlias = int | float


@dataclass(frozen=True, slots=True)
class FrozenJsonObject:
    items: tuple[tuple[str, FrozenJsonValue], ...]


@dataclass(frozen=True, slots=True)
class FrozenJsonArray:
    items: tuple[FrozenJsonValue, ...]


FrozenJsonValue: TypeAlias = JsonScalar | FrozenJsonObject | FrozenJsonArray


def freeze_json(value: object) -> FrozenJsonValue:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        mapping = cast(Mapping[object, object], value)
        items: list[tuple[str, FrozenJsonValue]] = []
        for key, child in mapping.items():
            if not isinstance(key, str):
                raise TypeError("AiO generation settings object keys must be strings")
            items.append((key, freeze_json(child)))
        return FrozenJsonObject(tuple(items))
    if isinstance(value, list):
        sequence = cast(list[object], value)
        return FrozenJsonArray(tuple(freeze_json(child) for child in sequence))
    raise TypeError(f"AiO generation settings contain a non-JSON value: {type(value).__name__}")


def thaw_json(value: FrozenJsonValue) -> object:
    if isinstance(value, FrozenJsonObject):
        return {key: thaw_json(child) for key, child in value.items}
    if isinstance(value, FrozenJsonArray):
        return [thaw_json(child) for child in value.items]
    return value


def freeze_object(value: Mapping[str, object]) -> FrozenJsonObject:
    frozen = freeze_json(value)
    if not isinstance(frozen, FrozenJsonObject):
        raise AssertionError("AiO generation settings object did not freeze as an object")
    return frozen


def thaw_object(value: FrozenJsonObject) -> dict[str, object]:
    return {key: thaw_json(child) for key, child in value.items}


def required(source: Mapping[str, object], key: str) -> object:
    if key not in source:
        raise ValueError(f"Normalized AiO generation settings are missing '{key}'")
    return source[key]


def expect_object(value: object, key: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"Normalized AiO generation settings field '{key}' must be an object")
    mapping = cast(Mapping[object, object], value)
    if not all(isinstance(name, str) for name in mapping):
        raise TypeError(f"Normalized AiO generation settings field '{key}' has a non-string key")
    return cast(Mapping[str, object], mapping)


def expect_str(value: object, key: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"Normalized AiO generation settings field '{key}' must be a string")
    return value


def expect_bool(value: object, key: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"Normalized AiO generation settings field '{key}' must be a boolean")
    return value


def expect_int(value: object, key: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"Normalized AiO generation settings field '{key}' must be an integer")
    return value


def expect_number(value: object, key: str) -> JsonNumber:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"Normalized AiO generation settings field '{key}' must be a number")
    return value


def expect_string_list(value: object, key: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise TypeError(f"Normalized AiO generation settings field '{key}' must be an array")
    sequence = cast(list[object], value)
    if not all(isinstance(item, str) for item in sequence):
        raise TypeError(f"Normalized AiO generation settings field '{key}' must contain strings")
    return tuple(cast(list[str], sequence))


def expect_object_list(value: object, key: str) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list):
        raise TypeError(f"Normalized AiO generation settings field '{key}' must be an array")
    sequence = cast(list[object], value)
    return tuple(expect_object(item, f"{key}[]") for item in sequence)


@dataclass(frozen=True, slots=True)
class ObjectState:
    key_order: tuple[str, ...]
    extensions: FrozenJsonObject

    @classmethod
    def from_source(
        cls,
        source: Mapping[str, object],
        known_keys: tuple[str, ...],
    ) -> ObjectState:
        known = frozenset(known_keys)
        return cls(
            key_order=tuple(source),
            extensions=freeze_object(
                {key: value for key, value in source.items() if key not in known}
            ),
        )

    def compose(self, known_values: Mapping[str, object]) -> dict[str, object]:
        extension_values = thaw_object(self.extensions)
        output: dict[str, object] = {}
        for key in self.key_order:
            if key in known_values:
                output[key] = known_values[key]
            elif key in extension_values:
                output[key] = extension_values[key]
            else:
                raise ValueError(f"AiO generation settings lost field '{key}' during typed conversion")
        if len(output) != len(known_values) + len(extension_values):
            raise ValueError("AiO generation settings typed conversion field order is incomplete")
        return output
__all__ = ()
