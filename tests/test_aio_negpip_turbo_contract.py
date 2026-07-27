from __future__ import annotations

import json
import re
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Any

_FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "aio_negpip_turbo_contract.v1.json"
)
_OPEN_TO_CLOSE = {"(": ")", "{": "}", "[": "]"}
_CLOSE_TO_OPEN = {value: key for key, value in _OPEN_TO_CLOSE.items()}
_NUMERIC_WEIGHT_RE = re.compile(
    r"(?P<prefix>:\s*)"
    r"(?P<sign>[+-]?)"
    r"(?P<number>(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
    r"(?P<suffix>\s*)(?=\))"
)


class TurboContractError(RuntimeError):
    pass


def _is_escaped(text: str, index: int) -> bool:
    slash_count = 0
    cursor = index - 1
    while cursor >= 0 and text[cursor] == "\\":
        slash_count += 1
        cursor -= 1
    return slash_count % 2 == 1


def _line_ending(line: str) -> str:
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith("\n"):
        return "\n"
    if line.endswith("\r"):
        return "\r"
    return ""


def _strip_comments_and_validate(text: str, reason_code: str) -> str:
    stack: list[str] = []
    output: list[str] = []
    for line in text.splitlines(keepends=True):
        if not stack and line.lstrip(" \t").startswith("#"):
            output.append(_line_ending(line))
            continue

        for index, char in enumerate(line):
            if _is_escaped(line, index):
                continue
            if char in _OPEN_TO_CLOSE:
                stack.append(char)
            elif char in _CLOSE_TO_OPEN:
                if not stack or stack[-1] != _CLOSE_TO_OPEN[char]:
                    raise TurboContractError(reason_code)
                stack.pop()
        output.append(line)

    if stack:
        raise TurboContractError(reason_code)
    return "".join(output)


def _split_top_level_items(text: str) -> list[str]:
    stack: list[str] = []
    items: list[str] = []
    start = 0
    for index, char in enumerate(text):
        if _is_escaped(text, index):
            continue
        if char in _OPEN_TO_CLOSE:
            stack.append(char)
        elif char in _CLOSE_TO_OPEN:
            stack.pop()
        elif not stack and char in ",\r\n":
            item = text[start:index].strip()
            if item:
                items.append(item)
            start = index + 1
    final_item = text[start:].strip()
    if final_item:
        items.append(final_item)
    return items


def _toggle_numeric_weight(match: re.Match[str]) -> str:
    sign = "" if match.group("sign") == "-" else "-"
    return (
        f"{match.group('prefix')}{sign}{match.group('number')}"
        f"{match.group('suffix')}"
    )


def _reference_transform(negative_prompt: str, policy: dict[str, Any]) -> str:
    reason_code = str(policy["malformed_reason_code"])
    cleaned = _strip_comments_and_validate(negative_prompt, reason_code)
    items = _split_top_level_items(cleaned)
    if not items:
        return ""
    prompt = ", ".join(items)
    prompt = _NUMERIC_WEIGHT_RE.sub(_toggle_numeric_weight, prompt)
    return f"({prompt}:-1)"


def _reference_conditioning(
    *,
    clip: object,
    positive_prompt: str,
    negative_prompt: str,
    policy: dict[str, Any],
    encode,
) -> tuple[object, object, str]:
    derived = _reference_transform(negative_prompt, policy)
    positive_execution_prompt = ", ".join(
        part for part in (positive_prompt, derived) if part
    )
    positive = encode(clip, positive_execution_prompt)
    negative = encode(clip, str(policy["neutral_negative_prompt"]))
    return positive, negative, positive_execution_prompt


def _reference_effective_cfg(
    case: dict[str, Any], policy: dict[str, Any]
) -> float | None:
    if case["stage"] in policy["sampling_stages"]:
        return 1.0
    return case["stored_cfg"]


class AIONegPipTurboContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.policy = cls.fixture["policy"]

    def test_contract_identity_and_ownership_are_fixed(self):
        self.assertEqual(
            self.fixture["schema"],
            "easyuse_anima_aio_negpip_turbo_contract",
        )
        self.assertEqual(self.fixture["version"], 1)
        self.assertEqual(self.policy["mode"], "turbo")
        self.assertEqual(self.policy["policy_revision"], 1)
        self.assertEqual(self.policy["negative_scale"], -1.0)
        self.assertEqual(self.policy["composition"], "whole_prompt_group")
        self.assertEqual(
            self.policy["input_phase"],
            "after_translation_and_wildcard_expansion",
        )
        self.assertEqual(self.policy["neutral_negative_prompt"], "")
        self.assertEqual(self.policy["malformed_policy"], "fail_closed")
        self.assertEqual(
            self.policy["rejected_composition"],
            "per_top_level_item",
        )

    def test_prompt_golden_covers_items_nesting_escapes_weights_and_empty(self):
        observed_ids = set()
        for case in self.fixture["prompt_cases"]:
            with self.subTest(case=case["id"]):
                observed_ids.add(case["id"])
                self.assertEqual(
                    _reference_transform(
                        case["negative_prompt"],
                        self.policy,
                    ),
                    case["derived_negative_contribution"],
                )

        self.assertEqual(
            observed_ids,
            {
                "top_level_comma",
                "top_level_newline_empty_and_comment",
                "nested_delimiters",
                "existing_numeric_weights",
                "escaped_delimiters",
                "inline_hash_is_prompt_text",
                "empty",
                "comment_only",
            },
        )

    def test_malformed_prompt_fails_closed_without_mutating_source(self):
        for case in self.fixture["malformed_cases"]:
            with self.subTest(case=case["id"]):
                source = case["negative_prompt"]
                with self.assertRaisesRegex(
                    TurboContractError,
                    self.policy["malformed_reason_code"],
                ):
                    _reference_transform(source, self.policy)
                self.assertEqual(case["negative_prompt"], source)

    def test_conditioning_uses_same_patched_clip_and_neutral_empty_prompt(self):
        patched_clip = object()
        for case in self.fixture["conditioning_cases"]:
            calls: list[tuple[object, str]] = []
            encoded: list[dict[str, object]] = []

            def encode(clip: object, prompt: str) -> dict[str, object]:
                calls.append((clip, prompt))
                result = {
                    "conditioning": prompt,
                    "shape": (1, 512, 2048),
                    "metadata": {"source": "patched_clip"},
                }
                encoded.append(result)
                return result

            with self.subTest(case=case["id"]):
                positive_source = case["positive_prompt"]
                negative_source = case["negative_prompt"]
                positive, negative, execution_prompt = _reference_conditioning(
                    clip=patched_clip,
                    positive_prompt=positive_source,
                    negative_prompt=negative_source,
                    policy=self.policy,
                    encode=encode,
                )

                self.assertEqual(
                    execution_prompt,
                    case["positive_execution_prompt"],
                )
                self.assertEqual(
                    calls,
                    [
                        (patched_clip, case["positive_execution_prompt"]),
                        (patched_clip, case["negative_execution_prompt"]),
                    ],
                )
                self.assertIs(positive, encoded[0])
                self.assertIs(negative, encoded[1])
                self.assertEqual(negative["shape"], (1, 512, 2048))
                self.assertEqual(
                    negative["metadata"],
                    {"source": "patched_clip"},
                )
                self.assertEqual(case["positive_prompt"], positive_source)
                self.assertEqual(case["negative_prompt"], negative_source)

    def test_sampling_cfg_is_runtime_only_and_saved_values_are_preserved(self):
        cases = self.fixture["stage_cfg_cases"]
        saved = deepcopy(cases)
        observed = {
            case["stage"]: _reference_effective_cfg(case, self.policy)
            for case in cases
        }

        self.assertEqual(
            observed,
            {
                "first_pass": 1.0,
                "highres": 1.0,
                "detailer": 1.0,
                "upscale_usdu": 1.0,
                "upscale_resshift": None,
                "postprocess": None,
                "save_output": None,
            },
        )
        self.assertEqual(cases, saved)
        self.assertEqual(
            set(self.policy["sampling_stages"]),
            {"first_pass", "highres", "detailer", "upscale_usdu"},
        )
        self.assertEqual(
            set(self.policy["non_sampling_stages"]),
            {"upscale_resshift", "postprocess", "save_output"},
        )


if __name__ == "__main__":
    unittest.main()
