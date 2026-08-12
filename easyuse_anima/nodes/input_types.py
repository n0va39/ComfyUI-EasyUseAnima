"""Shared private ComfyUI input type helpers."""

from __future__ import annotations

__all__ = ()


class _AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False


class _FlexibleOptionalInputType(dict):
    def __init__(self, input_type, values=None):
        super().__init__(values or {})
        self.input_type = input_type

    def __getitem__(self, key):
        if dict.__contains__(self, key):
            return dict.__getitem__(self, key)
        return (self.input_type,)

    def __contains__(self, key):
        return True


_ANY_TYPE = _AnyType("*")
