from __future__ import annotations

import json
import unittest

import nodes as easy_nodes
from nodes import (
    EasyUseAnimaRegionalConditioning,
    EasyUseAnimaPromptStudioRegional,
    REGIONAL_CONFIG_WORKFLOW_PROPERTY,
    REGIONAL_FIELDS_WORKFLOW_PROPERTY,
    REGIONAL_PROMPT_DATA_TYPE,
)


class PromptStudioRegionalTests(unittest.TestCase):
    def test_defaults_return_global_prompts_and_regional_payload(self):
        result = EasyUseAnimaPromptStudioRegional().build(
            "",
            "",
            resolution_bucket="Custom",
            resolution_size="",
            resolution_custom_width=896,
            resolution_custom_height=1152,
        )

        self.assertIn("masterpiece", result["result"][0])
        self.assertEqual(result["result"][1], "")
        self.assertEqual(result["result"][2], 896)
        self.assertEqual(result["result"][3], 1152)

        regional_data = result["result"][4]
        self.assertEqual(regional_data["canvas"]["width"], 896)
        self.assertEqual(regional_data["canvas"]["height"], 1152)
        self.assertEqual(regional_data["mask_authoring"]["storage_space"], "normalized_canvas")
        self.assertEqual(regional_data["masks"], [])
        self.assertFalse(regional_data["regional_enabled"])
        self.assertIn("global_prompt", regional_data)
        self.assertIn("model_patch_data", regional_data)

    def test_mask_scoped_positive_field_stays_out_of_global_positive_prompt(self):
        fields = [
            {
                "id": "global_quality",
                "pane": "positive",
                "type": "quality",
                "label": "Quality",
                "text": "masterpiece",
                "enabled": True,
            },
            {
                "id": "masked_general",
                "pane": "positive",
                "type": "general",
                "label": "Masked prompt",
                "text": "red dress",
                "enabled": True,
                "mask_ids": [1],
            },
            {
                "id": "negative_general",
                "pane": "negative",
                "type": "general",
                "label": "Negative",
                "text": "bad hands",
                "enabled": True,
            },
        ]
        config = {
            "next_mask_id": 2,
            "masks": [
                {
                    "mask_id": 1,
                    "label": "Mask 1",
                    "name": "face",
                    "color": "#22c55e",
                    "enabled": True,
                    "geometry": {"type": "rect", "x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4},
                }
            ],
        }

        result = EasyUseAnimaPromptStudioRegional().build(
            json.dumps(fields),
            json.dumps(config),
        )

        self.assertEqual(result["result"][0], "masterpiece, red dress")
        self.assertEqual(result["result"][1], "bad hands")

        regional_data = result["result"][4]
        self.assertEqual(regional_data["global_prompt"], "masterpiece")
        self.assertNotIn("red dress", regional_data["global_prompt"])
        self.assertEqual(regional_data["negative_prompt"], "bad hands")
        self.assertTrue(regional_data["regional_enabled"])
        self.assertEqual(regional_data["mask_prompts"][0]["field_id"], "masked_general")
        self.assertEqual(regional_data["mask_prompts"][0]["prompt"], "red dress")
        self.assertEqual(regional_data["mask_prompts"][0]["valid_mask_ids"], [1])

        model_patch_data = regional_data["model_patch_data"]
        self.assertTrue(model_patch_data["regional_attention"]["enabled"])
        self.assertEqual(model_patch_data["regional_attention"]["assignments"][0]["mask_ids"], [1])

    def test_build_mirrors_regional_state_into_workflow_metadata(self):
        fields = [
            {
                "id": "masked_general",
                "pane": "positive",
                "type": "general",
                "label": "Masked prompt",
                "text": "blue eyes",
                "enabled": True,
                "mask_ids": [1],
            }
        ]
        config = {
            "next_mask_id": 2,
            "masks": [
                {
                    "mask_id": 1,
                    "label": "Mask 1",
                    "name": "eyes",
                    "color": "#3b82f6",
                    "enabled": True,
                    "geometry": {"type": "rect", "x": 0.25, "y": 0.25, "width": 0.25, "height": 0.25},
                }
            ],
        }
        workflow_prompt = {"42": {"inputs": {}}}
        extra_pnginfo = {
            "workflow": {
                "nodes": [
                    {
                        "id": 42,
                        "type": "EasyUseAnimaPromptStudioRegional",
                        "widgets_values": [],
                        "properties": {},
                    }
                ]
            }
        }

        result = EasyUseAnimaPromptStudioRegional().build(
            json.dumps(fields),
            json.dumps(config),
            workflow_prompt=workflow_prompt,
            extra_pnginfo=extra_pnginfo,
            unique_id=42,
        )

        payload = result["ui"]["prompt_studio_regional"][0]
        workflow_node = extra_pnginfo["workflow"]["nodes"][0]
        self.assertEqual(workflow_prompt["42"]["inputs"]["regional_fields"], payload["regional_fields"])
        self.assertEqual(workflow_prompt["42"]["inputs"]["regional_config"], payload["regional_config"])
        self.assertEqual(workflow_node["widgets_values"][0], payload["regional_fields"])
        self.assertEqual(workflow_node["widgets_values"][1], payload["regional_config"])
        self.assertEqual(workflow_node["properties"][REGIONAL_FIELDS_WORKFLOW_PROPERTY], payload["regional_fields"])
        self.assertEqual(workflow_node["properties"][REGIONAL_CONFIG_WORKFLOW_PROPERTY], payload["regional_config"])

    def test_regional_conditioning_encodes_global_negative_and_masked_positive(self):
        try:
            import torch  # noqa: F401
        except ImportError:
            self.skipTest("torch is required for regional mask generation")

        payload = {
            "canvas": {"width": 64, "height": 48},
            "global_prompt": "masterpiece",
            "negative_prompt": "bad hands",
            "regional_enabled": True,
            "masks": [
                {
                    "mask_id": 1,
                    "label": "Mask 1",
                    "enabled": True,
                    "geometry": {"type": "rect", "x": 0.25, "y": 0.25, "width": 0.5, "height": 0.5},
                }
            ],
            "mask_prompts": [
                {
                    "field_id": "masked_general",
                    "prompt": "red dress",
                    "valid_mask_ids": [1],
                }
            ],
        }
        original_encode = easy_nodes._encode_with_comfy_clip
        try:
            easy_nodes._encode_with_comfy_clip = lambda clip, text: [[f"cond:{text}", {"encoded_text": text}]]

            positive, negative = EasyUseAnimaRegionalConditioning().encode(
                payload,
                clip=object(),
                mask_strength=0.75,
                set_cond_area="mask bounds",
            )
        finally:
            easy_nodes._encode_with_comfy_clip = original_encode

        self.assertEqual(positive[0][1]["encoded_text"], "masterpiece")
        self.assertEqual(positive[1][1]["encoded_text"], "red dress")
        self.assertEqual(tuple(positive[1][1]["mask"].shape), (1, 48, 64))
        self.assertEqual(positive[1][1]["mask_strength"], 0.75)
        self.assertFalse(positive[1][1]["set_area_to_bounds"])
        self.assertEqual(positive[1][1]["area"], (3, 4, 2, 2))
        self.assertEqual(negative[0][1]["encoded_text"], "bad hands")

    def test_regional_prompt_data_uses_dedicated_socket_type(self):
        regional_input = EasyUseAnimaRegionalConditioning.INPUT_TYPES()["required"]["regional_prompt_data"]

        self.assertEqual(EasyUseAnimaPromptStudioRegional.RETURN_TYPES[4], REGIONAL_PROMPT_DATA_TYPE)
        self.assertEqual(regional_input[0], REGIONAL_PROMPT_DATA_TYPE)
        self.assertTrue(regional_input[1]["forceInput"])


if __name__ == "__main__":
    unittest.main()
