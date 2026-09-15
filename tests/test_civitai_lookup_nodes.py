from __future__ import annotations

import json
import unittest
import weakref
from dataclasses import FrozenInstanceError, fields
from unittest.mock import Mock, patch

from easyuse_anima.aio import civitai_lookup as lookup
from easyuse_anima.aio import native_civitai as transport
from easyuse_anima.aio.native_resource_hashes import _manual_resource_hashes
from easyuse_anima.nodes.civitai_nodes import EasyUseAnimaCivitaiLookup

MATCH_HASH = "ABCDEF012345"
PRIMARY_HASH = "FEDCBA987654"
MATCH_SHA = "A" * 64
PRIMARY_SHA = "B" * 64
AIR = "urn:air:sdxl:lora:civitai:42@321"


def model_version():
    return {
        "id": 321,
        "modelId": 42,
        "air": AIR,
        "name": "v2",
        "model": {"name": "Color: Study, 푸른", "type": "LORA"},
        "trainedWords": ["color study", "푸른"],
        "files": [
            {
                "type": "Model", "primary": False,
                "hashes": {"AutoV3": MATCH_HASH, "SHA256": MATCH_SHA},
            },
            {
                "type": "Model", "primary": True,
                "hashes": {"AutoV3": PRIMARY_HASH, "SHA256": PRIMARY_SHA},
            },
        ],
        "images": [{"url": "https://example.invalid/unused-preview"}],
        "downloadUrl": "https://example.invalid/never-follow-this",
    }


def response_for(data=None, *, status=200, raw=None, headers=None):
    response = Mock(status_code=status, headers=headers or {})
    payload = raw if raw is not None else json.dumps(data, ensure_ascii=False).encode("utf-8")
    response.iter_content.return_value = [payload]
    return response


class CivitaiLookupNodeTests(unittest.TestCase):
    def setUp(self):
        lookup._cached_civitai_lookup.cache_clear()
        self.addCleanup(lookup._cached_civitai_lookup.cache_clear)
        self.node = EasyUseAnimaCivitaiLookup()
        http_patch = patch.object(transport, "_default_civitai_transport")
        self.http = http_patch.start()
        self.addCleanup(http_patch.stop)
        self.http.side_effect = AssertionError("Unexpected network call in lookup test")

    def serve(self, data=None):
        response = response_for(model_version() if data is None else data)
        self.http.side_effect = None
        self.http.return_value = response
        return response

    def test_node_contract_and_hash_matched_file_outputs_are_strings(self):
        inputs = self.node.INPUT_TYPES()
        self.assertEqual(set(inputs["required"]), {"identifier"})
        self.assertEqual(inputs["required"]["identifier"][0], "STRING")
        self.assertEqual(set(inputs["optional"]), {"weight"})
        weight_type, options = inputs["optional"]["weight"]
        self.assertEqual(weight_type, "FLOAT")
        self.assertEqual((options["default"], options["min"], options["max"]), (1.0, -100.0, 100.0))
        self.assertEqual(self.node.FUNCTION, "lookup")
        self.assertEqual(self.node.RETURN_TYPES, ("STRING",) * 7)
        self.assertEqual(self.node.RETURN_NAMES, (
            "autov3_hash", "sha256", "air", "model_name", "version_name",
            "trigger_words", "additional_hashes",
        ))

        data = model_version()
        data["files"].reverse()  # The primary file must not win a hash lookup.
        response = self.serve(data)
        result = self.node.lookup("  " + MATCH_SHA.lower() + "  ", weight=-0.75)
        self.assertIsInstance(result, tuple)
        self.assertTrue(all(isinstance(value, str) for value in result))
        self.assertEqual(result[:6], (
            MATCH_HASH, MATCH_SHA, AIR, "Color: Study, 푸른", "v2", "color study, 푸른",
        ))
        resources = _manual_resource_hashes(result[6])
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0].sha256, MATCH_HASH)
        self.assertEqual(resources[0].weight, -0.75)
        self.assertEqual(resources[0].display_name, "Color  Study  푸른")
        self.assertEqual(self.http.call_args.args, (
            "https://civitai.com/api/v1/model-versions/by-hash/" + MATCH_SHA.lower(),
        ))
        self.assertIsNone(self.http.call_args.kwargs["params"])
        self.assertEqual(self.http.call_args.kwargs["timeout"], (3.05, 10.0))
        self.assertEqual(transport.CivitaiLookupBudget().timeout_seconds, 12.0)
        response.close.assert_called_once_with()

    def test_air_uses_primary_file_and_weight_is_not_part_of_remote_cache(self):
        self.serve()
        first = self.node.lookup(AIR)
        second = self.node.lookup(AIR.upper(), weight=100.0)
        self.assertEqual(first[:2], (PRIMARY_HASH, PRIMARY_SHA))
        self.assertEqual(first[:6], second[:6])
        self.assertEqual(_manual_resource_hashes(first[6])[0].weight, 1.0)
        self.assertEqual(_manual_resource_hashes(second[6])[0].weight, 100.0)
        self.http.assert_called_once()
        self.assertEqual(self.http.call_args.args, (
            "https://civitai.com/api/v1/model-versions/321",
        ))

    def test_air_preserves_server_canonical_diffusion_model_type(self):
        data = model_version()
        data["air"] = "urn:air:anima:diffusionmodel:civitai:42@321"
        data["files"][1]["type"] = "Diffusion Model"
        self.serve(data)
        result = self.node.lookup("urn:air:anima:checkpoint:civitai:42@321")
        self.assertEqual(result[0], PRIMARY_HASH)
        self.assertEqual(result[2], data["air"])

    def test_exact_hash_match_is_required_and_failed_identity_can_be_retried(self):
        for hashes in ({"SHA256": MATCH_SHA + "00"}, {"AutoV3": PRIMARY_HASH}, [MATCH_SHA]):
            with self.subTest(hashes=hashes):
                data = model_version()
                data["files"] = [{"primary": True, "hashes": hashes}]
                self.serve(data)
                with self.assertRaisesRegex(RuntimeError, "exact requested file hash"):
                    self.node.lookup(MATCH_SHA)
                self.assertEqual(lookup._cached_civitai_lookup.cache_info().currsize, 0)
        self.serve()
        self.assertEqual(self.node.lookup(MATCH_SHA)[0], MATCH_HASH)
        self.assertEqual(self.http.call_count, 4)

    def test_air_model_and_version_ids_must_match_before_caching(self):
        for changes in (
            {"id": 322}, {"modelId": 43}, {"modelId": None}, {"id": True},
            {"air": "urn:air:sdxl:lora:civitai:42@322"},
            {"air": "urn:air:sdxl:lora:huggingface:42@321"},
        ):
            with self.subTest(changes=changes):
                data = model_version()
                data.update(changes)
                self.serve(data)
                with self.assertRaisesRegex(RuntimeError, "identity|IDs"):
                    self.node.lookup(AIR)
                self.assertEqual(lookup._cached_civitai_lookup.cache_info().currsize, 0)
        self.serve()
        self.assertEqual(self.node.lookup(AIR)[0], PRIMARY_HASH)

    def test_air_does_not_fall_back_to_an_unmarked_or_unhashed_file(self):
        for files_value in (
            None, [], [None],
            [{"hashes": {"AutoV3": MATCH_HASH}}],
            [{"primary": "true", "hashes": {"AutoV3": MATCH_HASH}}],
            [{"primary": True, "hashes": []}],
            [{"primary": True, "hashes": {"AutoV3": "invalid", "SHA256": "a" * 10}}],
        ):
            with self.subTest(files=files_value):
                data = model_version()
                data["files"] = files_value
                self.serve(data)
                with self.assertRaisesRegex(RuntimeError, "primary model file|hash"):
                    self.node.lookup(AIR)
                self.assertEqual(lookup._cached_civitai_lookup.cache_info().currsize, 0)

    def test_invalid_identifiers_and_weights_never_start_http(self):
        for identifier in (
            "", " ", None, 123, "abcdefg0", "a" * 7, "a" * 129,
            "https://civitai.com/models/42?modelVersionId=321",
            "https://example.invalid/model", "//civitai.com/api/v1/models/42",
            "urn:air:sdxl:lora:huggingface:42@321", "urn:air:sdxl:lora:civitai:42",
            "air:sdxl:lora:civitai:42@321", "urn:air:sdxl:lora:civitai:0@321",
            "urn:air:sdxl:lora:civitai:42@-1", AIR + "+123", AIR + ".safetensor",
            AIR + "/../../models", AIR + "?url=https://example.invalid",
            AIR + "\n", "urn:air:" + "x" * 513, "a" * 64 + "\x00",
        ):
            with self.subTest(identifier=identifier):
                with self.assertRaises(ValueError):
                    self.node.lookup(identifier)
        for weight in (float("nan"), float("inf"), -float("inf"), 100.01, -100.01, "bad", None, True):
            with self.subTest(weight=weight):
                with self.assertRaisesRegex(ValueError, "finite number"):
                    self.node.lookup(AIR, weight)
        self.http.assert_not_called()
        self.assertEqual(lookup._cached_civitai_lookup.cache_info().currsize, 0)

    def test_transport_errors_raise_and_successful_retry_is_cached(self):
        response = response_for(model_version())
        self.http.side_effect = [OSError("private proxy details"), response]
        with self.assertRaisesRegex(RuntimeError, "request failed") as raised:
            self.node.lookup(MATCH_HASH)
        self.assertNotIn("private proxy details", str(raised.exception))
        self.assertEqual(lookup._cached_civitai_lookup.cache_info().currsize, 0)
        result = self.node.lookup(MATCH_HASH)
        self.assertEqual(self.node.lookup(MATCH_HASH.lower()), result)
        self.assertEqual(self.http.call_count, 2)
        response.close.assert_called_once_with()

    def test_http_json_and_size_errors_are_not_outputs_or_cache_entries(self):
        bad_responses = (
            response_for({"error": "missing"}, status=404),
            response_for({}, status=302, headers={"Location": "https://example.invalid"}),
            response_for(raw=b"not JSON"),
            response_for(raw=b"[]"),
            response_for({}, headers={"Content-Length": str(transport._CIVITAI_RESPONSE_LIMIT + 1)}),
        )
        for bad in bad_responses:
            with self.subTest(status=bad.status_code):
                self.http.side_effect = [bad, response_for(model_version())]
                with self.assertRaises(RuntimeError):
                    self.node.lookup(AIR)
                self.assertEqual(lookup._cached_civitai_lookup.cache_info().currsize, 0)
                self.assertEqual(self.node.lookup(AIR)[0], PRIMARY_HASH)
                bad.close.assert_called_once_with()
                lookup._cached_civitai_lookup.cache_clear()

    def test_missing_optional_fields_stay_strings_and_metadata_hash_has_fallback(self):
        data = model_version()
        data.update({"model": {"name": "model"}, "name": None, "air": None, "trainedWords": {}})
        data["files"][1]["hashes"] = {"SHA256": PRIMARY_SHA}
        self.serve(data)
        result = self.node.lookup(AIR)
        self.assertEqual(result[:3], ("", PRIMARY_SHA, AIR))
        self.assertEqual(result[4:6], ("", ""))
        resources = _manual_resource_hashes(result[6])
        self.assertEqual(resources[0].display_name, "Civitai resource")
        self.assertEqual(resources[0].sha256, PRIMARY_SHA)

        lookup._cached_civitai_lookup.cache_clear()
        data["model"] = None
        data["files"] = [{"hashes": {"CRC32": "AABBCCDD"}}]
        self.serve(data)
        result = self.node.lookup("AABBCCDD", -100)
        self.assertEqual(result[:4], ("", "", "", ""))
        self.assertEqual(_manual_resource_hashes(result[6])[0].sha256, "aabbccdd")

    def test_cache_is_bounded_immutable_and_does_not_retain_http_payloads(self):
        class RemotePayload(dict):
            pass

        payload_refs = []

        def request(endpoint):
            version_id = int(endpoint.rsplit("/", 1)[-1])
            data = RemotePayload(model_version())
            data.update({
                "id": version_id, "air": f"urn:air:sdxl:lora:civitai:42@{version_id}",
                "description": "unused" * 100_000,
                "images": [{"url": "unused" * 100_000}],
                "trainedWords": ["x" * 512] * 10_000,
            })
            payload_refs.append(weakref.ref(data))
            return data

        with patch.object(lookup, "_request_civitai_json", side_effect=request) as mocked:
            selected = lookup.lookup_civitai_identifier(AIR)
            original_model_name = selected.model_name
            with self.assertRaises(FrozenInstanceError):
                selected.model_name = "changed"
            self.assertEqual(selected.model_name, original_model_name)
            self.assertFalse(hasattr(selected, "__dict__"))
            self.assertTrue(all(isinstance(getattr(selected, item.name), str) for item in fields(selected)))
            self.assertEqual(len(fields(selected)), 7)
            self.assertLessEqual(len(selected.trigger_words), lookup._MAX_LOOKUP_TRIGGER_TEXT)
            self.assertLess(sum(len(getattr(selected, item.name)) for item in fields(selected)), 6000)
            for version_id in range(1, 130):
                self.node.lookup(f"urn:air:sdxl:lora:civitai:42@{version_id}")
            self.assertEqual(lookup._cached_civitai_lookup.cache_info().currsize, 128)
            self.assertEqual(lookup._cached_civitai_lookup.cache_info().maxsize, 128)
            self.assertTrue(all(reference() is None for reference in payload_refs))
            self.node.lookup(AIR)  # The oldest selection was evicted.
            self.assertEqual(mocked.call_count, 131)
        self.http.assert_not_called()

    def test_remote_text_and_file_scan_limits_bound_selected_fields(self):
        data = model_version()
        data["model"]["name"] = "x" * 513
        data["name"] = "bad\nname"
        data["trainedWords"] = [None, "bad\nword", "x" * 513, "valid"]
        self.serve(data)
        result = self.node.lookup(AIR)
        self.assertEqual(result[3:6], ("", "", "valid"))
        self.assertEqual(len(_manual_resource_hashes(result[6])), 1)

        lookup._cached_civitai_lookup.cache_clear()
        data["files"] = [{}] * transport._MAX_REMOTE_FILES + [data["files"][1]]
        self.serve(data)
        with self.assertRaisesRegex(RuntimeError, "primary model file"):
            self.node.lookup(AIR)


if __name__ == "__main__":
    unittest.main()
