from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import nodes
from easyuse_anima.aio import first_pass_cache


class AIOFirstPassCacheMoveTests(unittest.TestCase):
    def setUp(self):
        first_pass_cache._clear_aio_first_pass_cache()

    def tearDown(self):
        first_pass_cache._clear_aio_first_pass_cache()

    def test_root_state_and_functions_are_direct_canonical_aliases(self):
        self.assertFalse(
            hasattr(first_pass_cache, "_bind_aio_first_pass_cache_runtime")
        )
        for name in (
            "AIO_FIRST_PASS_CACHE_MAX_ENTRIES",
            "_AIO_FIRST_PASS_CACHE",
            "_AIO_FIRST_PASS_CACHE_ORDER",
            "_clone_aio_cache_value",
            "_aio_first_pass_cache_key",
            "_get_aio_first_pass_cache",
            "_put_aio_first_pass_cache",
        ):
            with self.subTest(name=name):
                self.assertIs(getattr(nodes, name), getattr(first_pass_cache, name))

    def test_clone_preserves_nested_shape_tensor_clone_and_cpu_failure(self):
        calls = []

        class Tensor:
            def __init__(self, name):
                self.name = name

            def detach(self):
                calls.append((self.name, "detach"))
                return self

            def clone(self):
                calls.append((self.name, "clone"))
                return TensorClone(self.name + "-clone")

        class TensorClone:
            def __init__(self, name):
                self.name = name

            def cpu(self):
                calls.append((self.name, "cpu"))
                raise RuntimeError("cpu unavailable")

        passthrough = object()
        original = {
            "list": [Tensor("tensor"), passthrough],
            "tuple": ({"value": 3},),
        }
        cloned = first_pass_cache._clone_aio_cache_value(original)

        self.assertIsNot(cloned, original)
        self.assertIsNot(cloned["list"], original["list"])
        self.assertIsNot(cloned["tuple"], original["tuple"])
        self.assertIsNot(cloned["tuple"][0], original["tuple"][0])
        self.assertEqual(cloned["list"][0].name, "tensor-clone")
        self.assertIs(cloned["list"][1], passthrough)
        self.assertEqual(
            calls,
            [("tensor", "detach"), ("tensor", "clone"), ("tensor-clone", "cpu")],
        )

    def test_recursive_clone_re_resolves_canonical_helper_for_nested_items(self):
        replacement = Mock(side_effect=lambda value: f"cloned:{value}")
        clone_value = first_pass_cache._clone_aio_cache_value
        with patch.object(first_pass_cache, "_clone_aio_cache_value", replacement):
            result = clone_value({"a": 1, "b": 2})

        self.assertEqual(result, {"a": "cloned:1", "b": "cloned:2"})
        self.assertEqual([call.args for call in replacement.call_args_list], [(1,), (2,)])

    def test_key_preserves_exact_payload_order_values_and_exclusions(self):
        captured = []
        json_safe = Mock(side_effect=lambda value: {"safe": value})
        lora_signature = Mock(return_value=[{"name": "lora"}])

        def stable_change_key(payload):
            captured.append(payload)
            return "cache-key"

        settings = {
            "mode": "txt2img",
            "sampler": {"seed": 42},
            "model_patches": {"dave": True},
            "mod_guidance": {"mode": "enabled"},
            "artist_mix": {"mode": "off"},
            "highres": {"excluded": True},
            "detailer": {"excluded": True},
            "upscale": {"excluded": True},
            "postprocess": {"excluded": True},
            "preview": {"excluded": True},
            "save": {"excluded": True},
        }
        with (
            patch.object(
                first_pass_cache,
                "_stable_change_key",
                side_effect=stable_change_key,
            ),
            patch.object(first_pass_cache, "_prompt_data_json_safe", json_safe),
            patch.object(
                first_pass_cache,
                "_aio_lora_stack_signature",
                lora_signature,
            ),
        ):
            result = first_pass_cache._aio_first_pass_cache_key(
                cache_scope=0,
                context={"resource_info": {"model": "a"}, "input_settings": {"loader": "b"}},
                prompt_data={"positive": "p"},
                lora_stack="loras",
                settings=settings,
                positive_prompt=0,
                negative_prompt=None,
                quality_tags="quality",
                quality_neg="bad",
                use_anima_mod_guidance=1,
                use_negative_anima_mod_guidance=0,
                width="768",
                height=1024,
            )

        self.assertEqual(result, "cache-key")
        payload = captured[0]
        self.assertEqual(
            list(payload),
            [
                "schema", "version", "scope", "mode", "resource_info", "input_settings",
                "prompt_data", "lora_stack", "sampler", "model_patches", "mod_guidance",
                "artist_mix", "positive_prompt", "negative_prompt", "quality_tags",
                "quality_neg", "use_anima_mod_guidance", "use_negative_anima_mod_guidance",
                "width", "height",
            ],
        )
        self.assertEqual(payload["schema"], "easyuse_anima_aio_first_pass_cache")
        self.assertEqual(payload["version"], 1)
        self.assertEqual(payload["scope"], "")
        self.assertEqual(payload["lora_stack"], [{"name": "lora"}])
        self.assertEqual(payload["positive_prompt"], "")
        self.assertEqual(payload["negative_prompt"], "")
        self.assertTrue(payload["use_anima_mod_guidance"])
        self.assertFalse(payload["use_negative_anima_mod_guidance"])
        self.assertEqual((payload["width"], payload["height"]), (768, 1024))
        self.assertTrue(
            {"highres", "detailer", "upscale", "postprocess", "preview", "save"}.isdisjoint(payload)
        )
        self.assertEqual(
            [call.args[0] for call in json_safe.call_args_list],
            [
                {"model": "a"}, {"loader": "b"}, {"positive": "p"}, {"seed": 42},
                {"dave": True}, {"mode": "enabled"}, {"mode": "off"},
            ],
        )
        lora_signature.assert_called_once_with("loras")

    def test_replacement_state_clear_and_falsey_miss_are_call_time(self):
        cache = {"empty": {}}
        order = ["empty"]
        with (
            patch.object(first_pass_cache, "_AIO_FIRST_PASS_CACHE", cache),
            patch.object(first_pass_cache, "_AIO_FIRST_PASS_CACHE_ORDER", order),
        ):
            self.assertIsNone(first_pass_cache._get_aio_first_pass_cache("empty"))
            self.assertEqual(order, ["empty"])
            first_pass_cache._clear_aio_first_pass_cache()

        self.assertEqual(cache, {})
        self.assertEqual(order, [])

    def test_put_get_clone_isolation_lru_refresh_overwrite_and_eviction(self):
        latent = {"samples": [1]}
        image = [2]
        first_pass_cache._put_aio_first_pass_cache("a", latent, image)
        latent["samples"].append(99)
        image.append(99)

        cached_latent, cached_image = first_pass_cache._get_aio_first_pass_cache("a")
        self.assertEqual(cached_latent, {"samples": [1]})
        self.assertEqual(cached_image, [2])
        cached_latent["samples"].append(88)
        cached_image.append(88)
        self.assertEqual(
            first_pass_cache._get_aio_first_pass_cache("a"),
            ({"samples": [1]}, [2]),
        )

        first_pass_cache._put_aio_first_pass_cache("b", {"samples": [2]}, [2])
        first_pass_cache._get_aio_first_pass_cache("a")
        self.assertEqual(first_pass_cache._AIO_FIRST_PASS_CACHE_ORDER, ["b", "a"])
        first_pass_cache._put_aio_first_pass_cache("c", {"samples": [3]}, [3])
        self.assertNotIn("b", first_pass_cache._AIO_FIRST_PASS_CACHE)
        self.assertEqual(first_pass_cache._AIO_FIRST_PASS_CACHE_ORDER, ["a", "c"])

        first_pass_cache._put_aio_first_pass_cache("a", {"samples": [4]}, [4])
        self.assertEqual(first_pass_cache._AIO_FIRST_PASS_CACHE_ORDER, ["c", "a"])
        self.assertEqual(
            first_pass_cache._get_aio_first_pass_cache("a"),
            ({"samples": [4]}, [4]),
        )

    def test_replacement_max_and_state_control_oldest_first_eviction(self):
        cache = {}
        order = []
        with (
            patch.object(first_pass_cache, "_AIO_FIRST_PASS_CACHE", cache),
            patch.object(first_pass_cache, "_AIO_FIRST_PASS_CACHE_ORDER", order),
            patch.object(first_pass_cache, "AIO_FIRST_PASS_CACHE_MAX_ENTRIES", 1),
        ):
            first_pass_cache._put_aio_first_pass_cache("a", "latent-a", "image-a")
            first_pass_cache._put_aio_first_pass_cache("b", "latent-b", "image-b")

        self.assertEqual(cache, {"b": {"latent": "latent-b", "image": "image-b"}})
        self.assertEqual(order, ["b"])


if __name__ == "__main__":
    unittest.main()
