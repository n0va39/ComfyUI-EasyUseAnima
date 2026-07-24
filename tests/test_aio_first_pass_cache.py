from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from unittest.mock import Mock, patch

import nodes
from easyuse_anima.aio import first_pass_cache


class _SizedTensor:
    def __init__(
        self,
        *,
        count: int,
        item_bytes: int,
        fail_numel: bool = False,
        fallback_nbytes: int | None = None,
        clone_calls: list[int] | None = None,
    ):
        self.count = count
        self.item_bytes = item_bytes
        self.fail_numel = fail_numel
        self.nbytes = fallback_nbytes
        self.clone_calls = clone_calls

    def detach(self):
        return self

    def clone(self):
        if self.clone_calls is not None:
            self.clone_calls.append(self.count * self.item_bytes)
        return _SizedTensor(
            count=self.count,
            item_bytes=self.item_bytes,
            fail_numel=self.fail_numel,
            fallback_nbytes=self.nbytes,
            clone_calls=self.clone_calls,
        )

    def cpu(self):
        return self

    def numel(self):
        if self.fail_numel:
            raise RuntimeError("numel unavailable")
        return self.count

    def element_size(self):
        return self.item_bytes


class AIOFirstPassCacheMoveTests(unittest.TestCase):
    def setUp(self):
        first_pass_cache._set_aio_first_pass_cache_enabled(True)
        first_pass_cache._clear_aio_first_pass_cache()

    def tearDown(self):
        first_pass_cache._set_aio_first_pass_cache_enabled(True)
        first_pass_cache._clear_aio_first_pass_cache()

    def test_default_count_and_byte_policy_are_explicit(self):
        self.assertEqual(first_pass_cache.AIO_FIRST_PASS_CACHE_MAX_ENTRIES, 2)
        self.assertEqual(
            first_pass_cache.AIO_FIRST_PASS_CACHE_MAX_BYTES,
            512 * 1024 * 1024,
        )
        self.assertEqual(
            first_pass_cache.AIO_FIRST_PASS_CACHE_MAX_ENTRY_BYTES,
            256 * 1024 * 1024,
        )
        self.assertEqual(
            first_pass_cache.AIO_FIRST_PASS_CACHE_TTL_SECONDS,
            300.0,
        )
        self.assertTrue(first_pass_cache._AIO_FIRST_PASS_CACHE_ENABLED)

    def test_put_and_get_read_clock_once_and_replace_last_access(self):
        clock = Mock(side_effect=[10.0, 20.0])
        with patch.object(
            first_pass_cache,
            "_aio_first_pass_cache_now",
            clock,
        ):
            first_pass_cache._put_aio_first_pass_cache(
                "entry",
                {"samples": [1]},
                [2],
            )
            captured = first_pass_cache._AIO_FIRST_PASS_CACHE["entry"]
            self.assertEqual(
                (captured.created_at, captured.last_access_at),
                (10.0, 10.0),
            )

            self.assertEqual(
                first_pass_cache._get_aio_first_pass_cache("entry"),
                ({"samples": [1]}, [2]),
            )

        accessed = first_pass_cache._AIO_FIRST_PASS_CACHE["entry"]
        self.assertIsNot(accessed, captured)
        self.assertEqual(
            (accessed.created_at, accessed.last_access_at),
            (10.0, 20.0),
        )
        self.assertEqual(clock.call_count, 2)

    def test_absolute_ttl_hits_before_and_expires_at_or_after_boundary(self):
        for elapsed, expected_hit in (
            (299.999, True),
            (300.0, False),
            (301.0, False),
        ):
            with self.subTest(elapsed=elapsed):
                first_pass_cache._clear_aio_first_pass_cache()
                clock = Mock(side_effect=[100.0, 100.0 + elapsed])
                with patch.object(
                    first_pass_cache,
                    "_aio_first_pass_cache_now",
                    clock,
                ):
                    first_pass_cache._put_aio_first_pass_cache(
                        "entry",
                        "latent",
                        "image",
                    )
                    result = first_pass_cache._get_aio_first_pass_cache(
                        "entry"
                    )

                self.assertEqual(result is not None, expected_hit)
                self.assertEqual(clock.call_count, 2)
                if expected_hit:
                    self.assertIn(
                        "entry",
                        first_pass_cache._AIO_FIRST_PASS_CACHE,
                    )
                    self.assertEqual(
                        first_pass_cache._AIO_FIRST_PASS_CACHE_ORDER,
                        ["entry"],
                    )
                else:
                    self.assertNotIn(
                        "entry",
                        first_pass_cache._AIO_FIRST_PASS_CACHE,
                    )
                    self.assertEqual(
                        first_pass_cache._AIO_FIRST_PASS_CACHE_ORDER,
                        [],
                    )

    def test_last_access_does_not_extend_absolute_ttl(self):
        clock = Mock(side_effect=[0.0, 200.0, 301.0])
        with patch.object(
            first_pass_cache,
            "_aio_first_pass_cache_now",
            clock,
        ):
            first_pass_cache._put_aio_first_pass_cache(
                "entry",
                "latent",
                "image",
            )
            self.assertEqual(
                first_pass_cache._get_aio_first_pass_cache("entry"),
                ("latent", "image"),
            )
            self.assertIsNone(
                first_pass_cache._get_aio_first_pass_cache("entry")
            )

        self.assertEqual(clock.call_count, 3)
        self.assertEqual(first_pass_cache._AIO_FIRST_PASS_CACHE, {})
        self.assertEqual(first_pass_cache._AIO_FIRST_PASS_CACHE_ORDER, [])

    def test_disable_clears_and_skips_get_put_work_until_reenabled(self):
        first_pass_cache._put_aio_first_pass_cache(
            "entry",
            "latent",
            "image",
        )
        mapping = first_pass_cache._AIO_FIRST_PASS_CACHE
        order = first_pass_cache._AIO_FIRST_PASS_CACHE_ORDER
        first_pass_cache._set_aio_first_pass_cache_enabled(False)

        self.assertIs(first_pass_cache._AIO_FIRST_PASS_CACHE, mapping)
        self.assertIs(first_pass_cache._AIO_FIRST_PASS_CACHE_ORDER, order)
        self.assertEqual(mapping, {})
        self.assertEqual(order, [])
        self.assertFalse(first_pass_cache._AIO_FIRST_PASS_CACHE_ENABLED)

        estimator = Mock(side_effect=AssertionError("estimator called"))
        clone = Mock(side_effect=AssertionError("clone called"))
        clock = Mock(side_effect=AssertionError("clock called"))
        with (
            patch.object(
                first_pass_cache,
                "_aio_cache_pair_size_bytes",
                estimator,
            ),
            patch.object(
                first_pass_cache,
                "_clone_aio_cache_value",
                clone,
            ),
            patch.object(
                first_pass_cache,
                "_aio_first_pass_cache_now",
                clock,
            ),
        ):
            self.assertIsNone(
                first_pass_cache._get_aio_first_pass_cache("entry")
            )
            first_pass_cache._put_aio_first_pass_cache(
                "entry",
                "latent",
                "image",
            )

        estimator.assert_not_called()
        clone.assert_not_called()
        clock.assert_not_called()
        self.assertEqual(mapping, {})
        self.assertEqual(order, [])

        first_pass_cache._set_aio_first_pass_cache_enabled(True)
        first_pass_cache._put_aio_first_pass_cache(
            "entry",
            "latent",
            "image",
        )
        self.assertEqual(
            first_pass_cache._get_aio_first_pass_cache("entry"),
            ("latent", "image"),
        )

    def test_explicit_clear_is_idempotent_and_preserves_enabled_state(self):
        first_pass_cache._clear_aio_first_pass_cache()
        first_pass_cache._clear_aio_first_pass_cache()
        self.assertTrue(first_pass_cache._AIO_FIRST_PASS_CACHE_ENABLED)

        first_pass_cache._set_aio_first_pass_cache_enabled(False)
        first_pass_cache._clear_aio_first_pass_cache()
        first_pass_cache._clear_aio_first_pass_cache()
        self.assertFalse(first_pass_cache._AIO_FIRST_PASS_CACHE_ENABLED)

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
        resource_revision = Mock(return_value={"revision": "files"})

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
            patch.object(
                first_pass_cache,
                "_aio_first_pass_resource_revision",
                resource_revision,
            ),
        ):
            result = first_pass_cache._aio_first_pass_cache_key(
                cache_scope=0,
                context={
                    "resource_info": {
                        "unet_name": "unet.safetensors",
                        "vae_name": "vae.safetensors",
                        "clip_name": "clip.safetensors",
                    },
                    "input_settings": {"loader": "b"},
                },
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
                "schema", "version", "scope", "mode", "resource_info",
                "resource_revision", "input_settings", "prompt_data", "lora_stack", "sampler",
                "model_patches", "mod_guidance", "artist_mix", "positive_prompt",
                "negative_prompt", "quality_tags", "quality_neg",
                "use_anima_mod_guidance", "use_negative_anima_mod_guidance", "width",
                "height",
            ],
        )
        self.assertEqual(payload["schema"], "easyuse_anima_aio_first_pass_cache")
        self.assertEqual(payload["version"], 2)
        self.assertEqual(payload["scope"], "")
        self.assertEqual(payload["resource_revision"], {"revision": "files"})
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
                {
                    "unet_name": "unet.safetensors",
                    "vae_name": "vae.safetensors",
                    "clip_name": "clip.safetensors",
                },
                {"loader": "b"}, {"positive": "p"}, {"seed": 42}, {"dave": True},
                {"mode": "enabled"}, {"mode": "off"},
            ],
        )
        lora_signature.assert_called_once_with("loras")
        resource_revision.assert_called_once_with(
            {
                "unet_name": "unet.safetensors",
                "vae_name": "vae.safetensors",
                "clip_name": "clip.safetensors",
            },
            [{"name": "lora"}],
        )

    def test_resource_revision_maps_base_resources_and_loras_in_signature_order(self):
        revisions = Mock(
            side_effect=lambda folder_name, filename: (
                f"{folder_name}:{filename}"
            )
        )
        with patch.object(
            first_pass_cache,
            "_comfy_resource_file_revision",
            revisions,
        ):
            result = first_pass_cache._aio_first_pass_resource_revision(
                {
                    "unet_name": "unet.safetensors",
                    "vae_name": "vae.safetensors",
                    "clip_name": "clip.safetensors",
                },
                [
                    {"name": "style/a.safetensors"},
                    {"name": "style/b.safetensors"},
                ],
            )

        self.assertEqual(
            result,
            {
                "unet": "diffusion_models:unet.safetensors",
                "vae": "vae:vae.safetensors",
                "clip": "text_encoders:clip.safetensors",
                "loras": [
                    "loras:style/a.safetensors",
                    "loras:style/b.safetensors",
                ],
            },
        )
        self.assertEqual(
            [call.args for call in revisions.call_args_list],
            [
                ("loras", "style/a.safetensors"),
                ("loras", "style/b.safetensors"),
                ("diffusion_models", "unet.safetensors"),
                ("vae", "vae.safetensors"),
                ("text_encoders", "clip.safetensors"),
            ],
        )

    def test_key_changes_for_base_and_lora_file_revision_but_not_same_descriptor(self):
        settings = {
            "mode": "txt2img",
            "sampler": {"seed": 42},
            "model_patches": {},
            "mod_guidance": {},
            "artist_mix": {},
        }
        key_args = {
            "cache_scope": "node",
            "context": {
                "resource_info": {
                    "unet_name": "unet.safetensors",
                    "vae_name": "vae.safetensors",
                    "clip_name": "clip.safetensors",
                },
                "input_settings": {},
            },
            "prompt_data": {"positive": "prompt"},
            "lora_stack": [
                {
                    "name": "style.safetensors",
                    "strength_model": 1.0,
                    "strength_clip": 1.0,
                }
            ],
            "settings": settings,
            "positive_prompt": "prompt",
            "negative_prompt": "",
            "quality_tags": "",
            "quality_neg": "",
            "use_anima_mod_guidance": False,
            "use_negative_anima_mod_guidance": False,
            "width": 1024,
            "height": 1024,
        }
        baseline = {
            ("diffusion_models", "unet.safetensors"): {
                "path": "models/unet.safetensors",
                "size": 100,
                "mtime_ns": 1000,
            },
            ("vae", "vae.safetensors"): {
                "path": "models/vae.safetensors",
                "size": 200,
                "mtime_ns": 2000,
            },
            ("text_encoders", "clip.safetensors"): {
                "path": "models/clip.safetensors",
                "size": 300,
                "mtime_ns": 3000,
            },
            ("loras", "style.safetensors"): {
                "path": "models/style.safetensors",
                "size": 400,
                "mtime_ns": 4000,
            },
        }

        def key_for(revisions):
            with patch.object(
                first_pass_cache,
                "_comfy_resource_file_revision",
                side_effect=lambda folder_name, filename: revisions[
                    (folder_name, filename)
                ],
            ):
                return first_pass_cache._aio_first_pass_cache_key(**key_args)

        first = key_for(baseline)
        self.assertEqual(key_for(dict(baseline)), first)

        for field, value in (
            ("path", "models/replaced-unet.safetensors"),
            ("size", 101),
            ("mtime_ns", 1001),
        ):
            with self.subTest(base_field=field):
                changed = {
                    key: dict(revision)
                    for key, revision in baseline.items()
                }
                changed[("diffusion_models", "unet.safetensors")][field] = value
                self.assertNotEqual(key_for(changed), first)

        changed_lora = {
            key: dict(revision)
            for key, revision in baseline.items()
        }
        changed_lora[("loras", "style.safetensors")]["mtime_ns"] = 4001
        self.assertNotEqual(key_for(changed_lora), first)

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

    def test_nonempty_legacy_mapping_entry_remains_readable_and_isolated(self):
        cache = {
            "legacy": {
                "latent": {"samples": [1]},
                "image": [2],
            }
        }
        order = ["legacy"]
        with (
            patch.object(first_pass_cache, "_AIO_FIRST_PASS_CACHE", cache),
            patch.object(first_pass_cache, "_AIO_FIRST_PASS_CACHE_ORDER", order),
            patch.object(
                first_pass_cache,
                "_aio_first_pass_cache_now",
                side_effect=AssertionError("legacy entry read clock"),
            ),
        ):
            latent, image = first_pass_cache._get_aio_first_pass_cache("legacy")
            latent["samples"].append(99)
            image.append(99)

        self.assertEqual(
            cache,
            {
                "legacy": {
                    "latent": {"samples": [1]},
                    "image": [2],
                }
            },
        )
        self.assertEqual(order, ["legacy"])

    def test_frozen_entry_checkout_and_overwrite_are_copy_on_write(self):
        first_pass_cache._put_aio_first_pass_cache(
            "entry",
            {"samples": [1]},
            [2],
        )
        original_entry = first_pass_cache._AIO_FIRST_PASS_CACHE["entry"]

        self.assertIsInstance(
            original_entry,
            first_pass_cache._AIOFirstPassCacheEntry,
        )
        with self.assertRaises(FrozenInstanceError):
            setattr(original_entry, "latent", {"samples": [99]})

        latent, image = first_pass_cache._get_aio_first_pass_cache("entry")
        accessed_entry = first_pass_cache._AIO_FIRST_PASS_CACHE["entry"]
        self.assertIsNot(accessed_entry, original_entry)
        self.assertEqual(
            (accessed_entry.created_at, accessed_entry.size_bytes),
            (original_entry.created_at, original_entry.size_bytes),
        )
        self.assertGreaterEqual(
            accessed_entry.last_access_at,
            original_entry.last_access_at,
        )
        latent["samples"].append(88)
        image.append(88)
        self.assertEqual(
            original_entry.checkout(),
            ({"samples": [1]}, [2]),
        )

        first_pass_cache._put_aio_first_pass_cache(
            "entry",
            {"samples": [3]},
            [4],
        )
        replacement_entry = first_pass_cache._AIO_FIRST_PASS_CACHE["entry"]
        self.assertIsNot(replacement_entry, original_entry)
        self.assertEqual(
            original_entry.checkout(),
            ({"samples": [1]}, [2]),
        )
        self.assertEqual(
            replacement_entry.checkout(),
            ({"samples": [3]}, [4]),
        )

    def test_payload_byte_estimator_is_recursive_deduplicated_and_best_effort(self):
        tensor = _SizedTensor(count=3, item_bytes=4)
        fallback = _SizedTensor(
            count=0,
            item_bytes=0,
            fail_numel=True,
            fallback_nbytes=9,
        )
        value = {
            "tensor": tensor,
            "shared": [tensor],
            "bytes": b"abc",
            "bytearray": bytearray(4),
            "memoryview": memoryview(b"12345"),
            "fallback": fallback,
            "unknown": object(),
        }

        self.assertEqual(
            first_pass_cache._aio_cache_value_size_bytes(value),
            33,
        )
        self.assertEqual(
            first_pass_cache._aio_cache_pair_size_bytes(tensor, tensor),
            12,
        )
        self.assertEqual(
            first_pass_cache._aio_cache_value_size_bytes(
                _SizedTensor(
                    count=0,
                    item_bytes=0,
                    fail_numel=True,
                    fallback_nbytes=-1,
                )
            ),
            0,
        )

    def test_single_entry_cap_skips_without_mutating_existing_state(self):
        cache = {}
        order = []
        with (
            patch.object(first_pass_cache, "_AIO_FIRST_PASS_CACHE", cache),
            patch.object(first_pass_cache, "_AIO_FIRST_PASS_CACHE_ORDER", order),
            patch.object(
                first_pass_cache,
                "AIO_FIRST_PASS_CACHE_MAX_ENTRY_BYTES",
                8,
            ),
        ):
            first_pass_cache._put_aio_first_pass_cache(
                "entry",
                _SizedTensor(count=1, item_bytes=4),
                _SizedTensor(count=1, item_bytes=4),
            )
            existing = cache["entry"]
            oversize_clone_calls = []
            first_pass_cache._put_aio_first_pass_cache(
                "entry",
                _SizedTensor(
                    count=2,
                    item_bytes=4,
                    clone_calls=oversize_clone_calls,
                ),
                _SizedTensor(
                    count=1,
                    item_bytes=4,
                    clone_calls=oversize_clone_calls,
                ),
            )

        self.assertIs(cache["entry"], existing)
        self.assertEqual(order, ["entry"])
        self.assertEqual(existing.size_bytes, 8)
        self.assertEqual(oversize_clone_calls, [])

    def test_total_byte_budget_evicts_oldest_independently_of_count_cap(self):
        cache = {}
        order = []
        with (
            patch.object(first_pass_cache, "_AIO_FIRST_PASS_CACHE", cache),
            patch.object(first_pass_cache, "_AIO_FIRST_PASS_CACHE_ORDER", order),
            patch.object(first_pass_cache, "AIO_FIRST_PASS_CACHE_MAX_ENTRIES", 3),
            patch.object(
                first_pass_cache,
                "AIO_FIRST_PASS_CACHE_MAX_ENTRY_BYTES",
                8,
            ),
            patch.object(
                first_pass_cache,
                "AIO_FIRST_PASS_CACHE_MAX_BYTES",
                12,
            ),
        ):
            first_pass_cache._put_aio_first_pass_cache(
                "a",
                _SizedTensor(count=1, item_bytes=4),
                _SizedTensor(count=1, item_bytes=4),
            )
            first_pass_cache._put_aio_first_pass_cache(
                "b",
                _SizedTensor(count=1, item_bytes=4),
                _SizedTensor(count=1, item_bytes=4),
            )
            total_bytes = first_pass_cache._aio_first_pass_cache_total_bytes()

        self.assertEqual(set(cache), {"b"})
        self.assertEqual(order, ["b"])
        self.assertEqual(total_bytes, 8)

    def test_legacy_mapping_bytes_participate_in_oldest_eviction(self):
        legacy = {
            "latent": _SizedTensor(count=1, item_bytes=4),
            "image": _SizedTensor(count=1, item_bytes=4),
        }
        cache = {"legacy": legacy}
        order = ["legacy"]
        with (
            patch.object(first_pass_cache, "_AIO_FIRST_PASS_CACHE", cache),
            patch.object(first_pass_cache, "_AIO_FIRST_PASS_CACHE_ORDER", order),
            patch.object(first_pass_cache, "AIO_FIRST_PASS_CACHE_MAX_ENTRIES", 3),
            patch.object(
                first_pass_cache,
                "AIO_FIRST_PASS_CACHE_MAX_ENTRY_BYTES",
                8,
            ),
            patch.object(
                first_pass_cache,
                "AIO_FIRST_PASS_CACHE_MAX_BYTES",
                12,
            ),
        ):
            self.assertEqual(
                first_pass_cache._aio_first_pass_cache_total_bytes(),
                8,
            )
            first_pass_cache._put_aio_first_pass_cache(
                "new",
                _SizedTensor(count=1, item_bytes=4),
                _SizedTensor(count=1, item_bytes=4),
            )

        self.assertEqual(set(cache), {"new"})
        self.assertEqual(order, ["new"])

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

        entry = cache["b"]
        self.assertIsInstance(
            entry,
            first_pass_cache._AIOFirstPassCacheEntry,
        )
        self.assertEqual(
            (entry.latent, entry.image),
            ("latent-b", "image-b"),
        )
        self.assertEqual(order, ["b"])


if __name__ == "__main__":
    unittest.main()
