import unittest
from unittest.mock import patch

from easyuse_anima.naia import random_prompt as naia_random_prompt
from easyuse_anima.naia.client import (
    LATENT_ALIGN,
    NAI_1MP,
    NAIA_MAX_RESOLUTION,
    _build_naia_random_url,
    _fit_to_1mp,
    _parse_random_response,
)
from easyuse_anima.naia.resolution import _advanced_resolution_from_selection
from easyuse_anima.nodes import naia_nodes
from easyuse_anima.nodes.naia_nodes import EasyUseAnimaNAIARandomPrompt


def settings(**overrides):
    base = {
        "host": "settings-host",
        "port": 8123,
        "allow_remote_api": False,
        "use_naia_settings": False,
        "pre_prompt": "settings pre",
        "post_prompt": "settings post",
        "auto_hide": "settings hide",
        "preprocessing": {
            "remove_author": "on",
            "remove_work_title": "skip",
            "e621_auto_boost": "off",
        },
    }
    base.update(overrides)
    return base


def request_kwargs(**overrides):
    values = {
        "use_naia_bridge": True,
        "freeze_naia_output": False,
        "show_preview": True,
        "cached_prompt": "",
        "cached_negative_prompt": "",
        "cached_width": 0,
        "cached_height": 0,
        "cached_signature": "",
        "prompt": "input prompt",
        "override_prompt": True,
        "negative_prompt": "input negative",
        "override_negative": True,
        "width": 832,
        "override_width": True,
        "height": 1216,
        "override_height": True,
        "use_naia_settings": True,
        "pre_prompt": "node pre",
        "post_prompt": "node post",
        "auto_hide": "node hide",
        "host": "node-host",
        "port": 9999,
    }
    values.update(overrides)
    return values


class NaiaSettingsTests(unittest.TestCase):
    def test_node_keeps_schema_identity_and_uses_canonical_request_helpers(self):
        self.assertEqual(
            EasyUseAnimaNAIARandomPrompt.request.__module__,
            naia_nodes.__name__,
        )
        self.assertIs(
            EasyUseAnimaNAIARandomPrompt._cached_tuple,
            naia_random_prompt._cached_tuple,
        )
        self.assertIs(
            EasyUseAnimaNAIARandomPrompt._make_signature,
            naia_random_prompt._make_signature,
        )
        self.assertIs(
            EasyUseAnimaNAIARandomPrompt._make_request_body,
            naia_random_prompt._make_request_body,
        )
        self.assertIs(
            EasyUseAnimaNAIARandomPrompt._apply_overrides,
            naia_random_prompt._apply_overrides,
        )
        self.assertIs(EasyUseAnimaNAIARandomPrompt._ui, naia_random_prompt._ui)

    def test_fit_to_1mp_preserves_normal_shapes(self):
        self.assertEqual(_fit_to_1mp(4096, 4096), (1024, 1024))
        self.assertEqual(_fit_to_1mp(832, 1216), (832, 1216))
        self.assertEqual(_fit_to_1mp(1216, 832), (1216, 832))
        self.assertEqual(_fit_to_1mp(4096, 2048), (1440, 728))
        self.assertEqual(_fit_to_1mp(2048, 4096), (728, 1440))

    def test_fit_to_1mp_caps_extreme_aspect_ratios_after_alignment(self):
        cases = (
            ((1_000_000, 2), (131_072, LATENT_ALIGN)),
            ((2, 1_000_000), (LATENT_ALIGN, 131_072)),
            ((1_000_000_000, 1), (131_072, LATENT_ALIGN)),
            ((1, 1_000_000_000), (LATENT_ALIGN, 131_072)),
        )

        for source, expected in cases:
            with self.subTest(source=source):
                fitted = _fit_to_1mp(*source)
                self.assertEqual(fitted, expected)
                self.assertLessEqual(fitted[0] * fitted[1], NAI_1MP)
                self.assertEqual(fitted[0] % LATENT_ALIGN, 0)
                self.assertEqual(fitted[1] % LATENT_ALIGN, 0)

    def test_parse_random_response_rejects_invalid_resolution_bounds(self):
        cases = (
            (0, 1024),
            (-1, 1024),
            (1024, 0),
            (1024, -1),
            (NAIA_MAX_RESOLUTION + 1, 1024),
            (1024, NAIA_MAX_RESOLUTION + 1),
            (1_000_000, 2),
            (1_000_000_000, 1),
        )

        for width, height in cases:
            with self.subTest(width=width, height=height):
                with self.assertRaisesRegex(
                    RuntimeError,
                    rf"Invalid NAIA width/height.*1 to {NAIA_MAX_RESOLUTION}",
                ):
                    _parse_random_response({"width": width, "height": height})

    def test_parse_random_response_accepts_absolute_resolution_boundary(self):
        self.assertEqual(
            _parse_random_response({"width": NAIA_MAX_RESOLUTION, "height": NAIA_MAX_RESOLUTION}),
            ("", "", 1024, 1024),
        )

    def test_parse_random_response_preserves_prompt_cleanup_boundaries(self):
        self.assertEqual(
            _parse_random_response({
                "prompt": "\t# hidden comment\nkeep # inline, , subject",
                "negative_prompt": "bad,  , hands",
                "width": 1024,
                "height": 1024,
            }),
            ("keep # inline, subject", "bad, hands", 1024, 1024),
        )

    def test_resolution_labels_accept_star_x_and_multiplication_sign(self):
        cases = (
            ("1024 * 1024 (1:1)", (1024, 1024)),
            ("896 x 1152 (7:9)", (896, 1152)),
            ("1152 × 896 (9:7)", (1152, 896)),
        )
        for label, expected in cases:
            with self.subTest(label=label):
                self.assertEqual(
                    _advanced_resolution_from_selection("1024", label),
                    expected,
                )

    def test_request_uses_global_naia_settings_instead_of_node_values(self):
        calls = []

        def fake_post(host, port, body, **kwargs):
            calls.append((host, port, body))
            return {
                "prompt": "naia prompt",
                "negative_prompt": "naia negative",
                "width": 1024,
                "height": 1024,
            }

        with (
            patch.object(naia_nodes, "resolve_naia_settings", lambda: settings()),
            patch.object(naia_nodes, "_post_random", fake_post),
        ):
            result = EasyUseAnimaNAIARandomPrompt().request(
                use_naia_bridge=True,
                freeze_naia_output=False,
                show_preview=True,
                cached_prompt="",
                cached_negative_prompt="",
                cached_width=0,
                cached_height=0,
                cached_signature="",
                prompt="input prompt",
                override_prompt=True,
                negative_prompt="input negative",
                override_negative=True,
                width=832,
                override_width=True,
                height=1216,
                override_height=True,
                use_naia_settings=True,
                pre_prompt="node pre",
                post_prompt="node post",
                auto_hide="node hide",
                host="node-host",
                port=9999,
            )

        self.assertEqual(result["result"], ("naia prompt", "naia negative", 1024, 1024))
        self.assertEqual(calls[0][0], "settings-host")
        self.assertEqual(calls[0][1], 8123)
        self.assertEqual(calls[0][2]["peng_override"]["pre_prompt"], "settings pre")
        self.assertEqual(calls[0][2]["peng_override"]["post_prompt"], "settings post")
        self.assertEqual(calls[0][2]["peng_override"]["auto_hide"], "settings hide")
        self.assertEqual(
            calls[0][2]["peng_override"]["preprocessing_options"],
            {"remove_author": True, "e621_auto_boost": False},
        )

    def test_request_preserves_disabled_and_matching_frozen_shortcuts(self):
        node = EasyUseAnimaNAIARandomPrompt()
        current_settings = settings()
        signature = node._make_signature(
            "input prompt",
            True,
            "input negative",
            True,
            832,
            True,
            1216,
            True,
            current_settings["use_naia_settings"],
            current_settings["pre_prompt"],
            current_settings["post_prompt"],
            current_settings["auto_hide"],
            current_settings["host"],
            current_settings["port"],
            current_settings["preprocessing"],
        )

        with (
            patch.object(naia_nodes, "resolve_naia_settings", lambda: current_settings),
            patch.object(naia_nodes, "_post_random") as post_random,
        ):
            disabled = node.request(**request_kwargs(use_naia_bridge=False))
            frozen = node.request(**request_kwargs(
                freeze_naia_output=True,
                cached_prompt="saved prompt",
                cached_negative_prompt="saved negative",
                cached_width=1024,
                cached_height=1024,
                cached_signature=signature,
            ))

        post_random.assert_not_called()
        self.assertEqual(
            disabled["result"],
            ("input prompt", "input negative", 832, 1216),
        )
        self.assertEqual(disabled["ui"]["status"], ["disabled"])
        self.assertEqual(
            frozen["result"],
            ("saved prompt", "saved negative", 1024, 1024),
        )
        self.assertEqual(frozen["ui"]["status"], ["frozen"])

    def test_fresh_request_updates_both_workflow_metadata_forms(self):
        workflow_prompt = {"7": {"inputs": {}}}
        workflow_node = {"id": 7, "widgets_values": []}
        extra_pnginfo = {"workflow": {"nodes": [workflow_node]}}
        response = {
            "request_id": "request-7",
            "prompt": "generated prompt",
            "negative_prompt": "generated negative",
            "width": 1024,
            "height": 1024,
        }

        with (
            patch.object(naia_nodes, "resolve_naia_settings", lambda: settings()),
            patch.object(naia_nodes, "_post_random", return_value=response) as post_random,
        ):
            result = EasyUseAnimaNAIARandomPrompt().request(**request_kwargs(
                workflow_prompt=workflow_prompt,
                extra_pnginfo=extra_pnginfo,
                unique_id="7",
            ))

        post_random.assert_called_once()
        self.assertEqual(
            result["result"],
            ("generated prompt", "generated negative", 1024, 1024),
        )
        self.assertEqual(result["ui"]["status"], ["fresh"])
        prompt_inputs = workflow_prompt["7"]["inputs"]
        self.assertTrue(prompt_inputs["freeze_naia_output"])
        self.assertEqual(prompt_inputs["cached_prompt"], "generated prompt")
        self.assertEqual(prompt_inputs["cached_negative_prompt"], "generated negative")
        self.assertEqual(prompt_inputs["cached_width"], 1024)
        self.assertEqual(prompt_inputs["cached_height"], 1024)
        input_names = EasyUseAnimaNAIARandomPrompt._widget_input_names()
        for name in (
            "freeze_naia_output",
            "cached_prompt",
            "cached_negative_prompt",
            "cached_width",
            "cached_height",
            "cached_signature",
        ):
            self.assertEqual(
                workflow_node["widgets_values"][input_names.index(name)],
                prompt_inputs[name],
            )

    def test_desktop_naia_settings_skip_peng_override(self):
        with patch.object(
            naia_nodes,
            "resolve_naia_settings",
            lambda: settings(use_naia_settings=True),
        ):
            body = EasyUseAnimaNAIARandomPrompt._make_request_body(
                use_naia_settings=True,
                pre_prompt="unused",
                post_prompt="unused",
                auto_hide="unused",
                pp_kwargs={"remove_author": "on"},
            )

        self.assertNotIn("peng_override", body)

    def test_naia_random_url_defaults_to_localhost_only(self):
        self.assertEqual(
            _build_naia_random_url("127.0.0.1", 7243),
            "http://127.0.0.1:7243/api/comfyui/random",
        )
        self.assertEqual(
            _build_naia_random_url("localhost", 7243),
            "http://localhost:7243/api/comfyui/random",
        )
        self.assertEqual(
            _build_naia_random_url("::1", 7243),
            "http://[::1]:7243/api/comfyui/random",
        )
        with self.assertRaisesRegex(RuntimeError, "Remote NAIA API access is disabled"):
            _build_naia_random_url("192.168.0.2", 7243)
        self.assertEqual(
            _build_naia_random_url("192.168.0.2", 7243, allow_remote_api=True),
            "http://192.168.0.2:7243/api/comfyui/random",
        )

    def test_naia_random_url_rejects_url_like_host_values(self):
        for host in ("http://127.0.0.1", "127.0.0.1/api", "host name"):
            with self.subTest(host=host):
                with self.assertRaisesRegex(RuntimeError, "hostname or IP address"):
                    _build_naia_random_url(host, 7243, allow_remote_api=True)


if __name__ == "__main__":
    unittest.main()
