import unittest
from unittest.mock import patch

from nodes import EasyUseAnimaNAIARandomPrompt


def settings(**overrides):
    base = {
        "host": "settings-host",
        "port": 8123,
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
    def test_request_uses_global_naia_settings_instead_of_node_values(self):
        calls = []

        def fake_post(host, port, body):
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


if __name__ == "__main__":
    unittest.main()
