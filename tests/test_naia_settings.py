import unittest
from unittest.mock import patch

from nodes import (
    LATENT_ALIGN,
    NAI_1MP,
    NAIA_MAX_RESOLUTION,
    EasyUseAnimaNAIARandomPrompt,
    _advanced_resolution_from_selection,
    _build_naia_random_url,
    _fit_to_1mp,
    _parse_random_response,
)


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


class NaiaSettingsTests(unittest.TestCase):
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
            patch("nodes.resolve_naia_settings", lambda: settings()),
            patch("nodes._post_random", fake_post),
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

    def test_desktop_naia_settings_skip_peng_override(self):
        with patch("nodes.resolve_naia_settings", lambda: settings(use_naia_settings=True)):
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
