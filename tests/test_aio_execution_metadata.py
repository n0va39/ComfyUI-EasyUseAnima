from __future__ import annotations

import copy
import json
import unittest

from easyuse_anima.aio.execution_metadata import (
    snapshot_aio_execution_metadata,
    snapshot_aio_prompt,
)


def _settings(seed=17, **changes):
    return {
        "schema": "easyuse_anima_aio_generation_settings",
        "version": 4,
        "sampler": {"seed": seed, "seed_after_generate": "randomize", "steps": 28, "cfg": 5.0},
        "highres": {"enabled": True, "scale": 1.5, "denoise": 0.3},
        "save": {"enabled": True, "backend": "image_saver"},
        **changes,
    }


def _graph(*ids):
    original = _settings(-1)
    prompt = {
        str(node_id): {
            "class_type": "EasyUseAnimaAIOGenerator",
            "inputs": {
                "generation_settings": json.dumps(original),
                "easy_use_anima_input": ["source", 0],
            },
        }
        for node_id in ids
    }
    extra = {
        "workflow": {
            "nodes": [
                {
                    "id": node_id,
                    "type": "EasyUseAnimaAIOGenerator",
                    "widgets_values": [json.dumps(original), "preserved trailing widget"],
                    "properties": {"user": "preserved"},
                    "inputs": [{"name": "easy_use_anima_input", "link": 123}],
                }
                for node_id in ids
            ],
            "links": [[123, "source", 0, ids[0], 0, "EASY_USE_ANIMA_INPUT"]],
            "extra": {"user": {"display": "preserved"}},
        },
        "third_party": {"value": "preserved"},
    }
    return prompt, extra


def _connect_settings(graph, node_id, link_id, *, source_id="settings_source", object_link=False):
    target = next(node for node in graph["nodes"] if str(node["id"]) == str(node_id))
    inputs = target.setdefault("inputs", [])
    slot = len(inputs)
    inputs.append({"name": "generation_settings", "type": "STRING", "link": link_id, "widget": {"name": "generation_settings"}})
    source = next((node for node in graph["nodes"] if node["id"] == source_id), None)
    if source is None:
        source = {"id": source_id, "type": "StringSource", "widgets_values": ["source unchanged"], "outputs": [{"name": "STRING", "links": []}]}
        graph["nodes"].append(source)
    source["outputs"][0]["links"].append(link_id)
    link = [link_id, source_id, 0, node_id, slot, "STRING"]
    if object_link:
        link = dict(zip(("id", "origin_id", "origin_slot", "target_id", "target_slot", "type"), link))
    graph.setdefault("links", []).append(link)
    return source, target


class AIOExecutionMetadataTests(unittest.TestCase):
    def test_execution_settings_replace_only_own_saved_widget_and_api_input(self):
        prompt, extra = _graph(7, 8)
        original_prompt = copy.deepcopy(prompt)
        original_other = copy.deepcopy(extra["workflow"]["nodes"][1])
        settings = _settings()
        execution = {"stages": {"first_pass": {"cfg": 1.0}}, "width": 1024}
        saved_prompt, saved_extra = snapshot_aio_execution_metadata(prompt, extra, 7, settings, execution)
        saved_settings = json.loads(saved_prompt["7"]["inputs"]["generation_settings"])
        self.assertEqual(saved_settings["sampler"]["seed"], 17)
        self.assertEqual(saved_settings["sampler"]["seed_after_generate"], "fixed")
        self.assertEqual(saved_settings["highres"], settings["highres"])
        self.assertEqual(prompt, original_prompt)
        self.assertEqual(extra["workflow"]["nodes"][1], original_other)
        self.assertEqual(settings["sampler"]["seed_after_generate"], "randomize")
        node = saved_extra["workflow"]["nodes"][0]
        self.assertEqual(json.loads(node["widgets_values"][0]), saved_settings)
        self.assertEqual(node["widgets_values"][1], "preserved trailing widget")
        self.assertEqual(node["properties"], {"user": "preserved"})
        self.assertEqual(node["inputs"], [{"name": "easy_use_anima_input", "link": 123}])
        self.assertEqual(saved_prompt["7"]["inputs"]["easy_use_anima_input"], ["source", 0])
        self.assertEqual(saved_extra["workflow"]["links"], extra["workflow"]["links"])
        record = saved_extra["workflow"]["extra"]["easyuse_anima_executions"]["7"]
        self.assertEqual(record["generation_settings"], saved_settings)
        self.assertEqual(record["execution"], execution)
        self.assertEqual(len(record["source_input_sha256"]), 64)

    def test_multiple_aio_records_overlay_downstream_saver_prompt_without_mutation(self):
        prompt, extra = _graph(7, 8)
        original = copy.deepcopy(prompt)
        first_prompt, first_extra = snapshot_aio_execution_metadata(prompt, extra, "7", _settings(17), {"node": 7})
        snapshot_aio_execution_metadata(prompt, extra, "8", _settings(29), {"node": 8})
        downstream = snapshot_aio_prompt(prompt, extra)
        self.assertEqual(json.loads(downstream["7"]["inputs"]["generation_settings"])["sampler"]["seed"], 17)
        self.assertEqual(json.loads(downstream["8"]["inputs"]["generation_settings"])["sampler"]["seed"], 29)
        self.assertEqual(json.loads(first_prompt["8"]["inputs"]["generation_settings"])["sampler"]["seed"], -1)
        self.assertNotIn("8", first_extra["workflow"]["extra"]["easyuse_anima_executions"])
        self.assertEqual(prompt, original)

    def test_repeated_node_execution_replaces_all_changed_settings(self):
        prompt, extra = _graph(7)
        first_prompt, first_extra = snapshot_aio_execution_metadata(prompt, extra, "7", _settings(17), {"run": 1})
        changed = _settings(23, highres={"enabled": False}, custom_future_option={"edited": [1, 2]})
        changed["sampler"]["steps"] = 42
        changed["sampler"]["cfg"] = 8.5
        saved_prompt, saved_extra = snapshot_aio_execution_metadata(prompt, extra, "7", changed, {"run": 2})
        actual = json.loads(saved_prompt["7"]["inputs"]["generation_settings"])
        self.assertEqual(actual["sampler"]["steps"], 42)
        self.assertEqual(actual["sampler"]["cfg"], 8.5)
        self.assertEqual(actual["highres"], {"enabled": False})
        self.assertEqual(actual["custom_future_option"], {"edited": [1, 2]})
        self.assertEqual(saved_extra["workflow"]["extra"]["easyuse_anima_executions"]["7"]["execution"], {"run": 2})
        self.assertEqual(first_extra["workflow"]["extra"]["easyuse_anima_executions"]["7"]["execution"], {"run": 1})
        self.assertEqual(json.loads(first_prompt["7"]["inputs"]["generation_settings"])["sampler"]["seed"], 17)

    def test_imported_record_cannot_override_an_edited_node_that_has_not_run(self):
        prompt, extra = _graph(7, 8)
        snapshot_aio_execution_metadata(prompt, extra, "8", _settings(29), {"previous_run": True})
        edited = _settings(53)
        edited["sampler"]["cfg"] = 9.0
        prompt["8"]["inputs"]["generation_settings"] = json.dumps(edited)
        extra["workflow"]["nodes"][1]["widgets_values"][0] = json.dumps(edited)
        saved_prompt, saved_extra = snapshot_aio_execution_metadata(prompt, extra, "7", _settings(17), {})
        actual = json.loads(saved_prompt["8"]["inputs"]["generation_settings"])
        self.assertEqual(actual, edited)
        self.assertEqual(snapshot_aio_prompt(prompt, saved_extra)["8"], prompt["8"])
        # The historical record stays available as history, but is not applied.
        self.assertEqual(saved_extra["workflow"]["extra"]["easyuse_anima_executions"]["8"]["generation_settings"]["sampler"]["seed"], 29)

    def test_api_only_edit_cannot_be_overwritten_by_unchanged_workflow_record(self):
        prompt, extra = _graph(7, 8)
        saved_prompt, saved_extra = snapshot_aio_execution_metadata(prompt, extra, "7", _settings(17), {})
        changed = copy.deepcopy(saved_prompt)
        changed_settings = _settings(99)
        changed["7"]["inputs"]["generation_settings"] = json.dumps(changed_settings)
        downstream = snapshot_aio_prompt(changed, saved_extra)
        self.assertEqual(json.loads(downstream["7"]["inputs"]["generation_settings"]), changed_settings)
        next_prompt, _ = snapshot_aio_execution_metadata(changed, saved_extra, "8", _settings(29), {})
        self.assertEqual(json.loads(next_prompt["7"]["inputs"]["generation_settings"]), changed_settings)

    def test_restored_frozen_input_and_semantically_identical_source_remain_applicable(self):
        prompt, extra = _graph(7)
        saved_prompt, saved_extra = snapshot_aio_execution_metadata(prompt, extra, "7", _settings(17), {})
        self.assertEqual(snapshot_aio_prompt(saved_prompt, saved_extra), saved_prompt)
        equivalent_source = copy.deepcopy(prompt)
        equivalent_source["7"]["inputs"]["generation_settings"] = json.loads(prompt["7"]["inputs"]["generation_settings"])
        self.assertEqual(snapshot_aio_prompt(equivalent_source, saved_extra), saved_prompt)

    def test_late_mutations_cannot_rewrite_handed_off_snapshots_or_records(self):
        prompt, extra = _graph(7)
        settings = _settings()
        execution = {"stages": {"sampler": {"steps": 28}}}
        saved_prompt, saved_extra = snapshot_aio_execution_metadata(prompt, extra, "7", settings, execution)
        expected_prompt = copy.deepcopy(saved_prompt)
        expected_extra = copy.deepcopy(saved_extra)
        settings["highres"]["scale"] = 9
        execution["stages"]["sampler"]["steps"] = 99
        self.assertEqual(extra, expected_extra)
        prompt["7"]["inputs"]["easy_use_anima_input"][0] = "changed"
        extra["workflow"]["nodes"][0]["properties"]["user"] = "changed"
        extra["workflow"]["extra"]["easyuse_anima_executions"]["7"]["generation_settings"]["sampler"]["seed"] = 100
        self.assertEqual(saved_prompt, expected_prompt)
        self.assertEqual(saved_extra, expected_extra)

    def test_subgraph_workflow_node_uses_full_api_id_for_record_and_prompt(self):
        prompt, extra = _graph("parent:7")
        inner = extra["workflow"]["nodes"][0]
        inner["id"] = 7
        extra["workflow"]["nodes"] = [{"id": "parent", "type": "subgraph-uuid", "widgets_values": ["outer"]}]
        extra["workflow"]["definitions"] = {"subgraphs": [{"id": "subgraph-uuid", "nodes": [inner]}]}
        saved_prompt, saved_extra = snapshot_aio_execution_metadata(prompt, extra, "parent:7", _settings(37), {})
        self.assertEqual(json.loads(inner["widgets_values"][0])["sampler"]["seed"], 37)
        self.assertEqual(extra["workflow"]["nodes"][0]["widgets_values"], ["outer"])
        self.assertIn("parent:7", saved_extra["workflow"]["extra"]["easyuse_anima_executions"])
        self.assertEqual(json.loads(saved_prompt["parent:7"]["inputs"]["generation_settings"])["sampler"]["seed"], 37)

    def test_missing_workflow_still_snapshots_current_api_prompt_without_inventing_metadata(self):
        for extra in (None, {}, {"third_party": {"value": 1}}):
            with self.subTest(extra=extra):
                prompt, _ = _graph(7)
                saved_prompt, saved_extra = snapshot_aio_execution_metadata(prompt, extra, "7", _settings(), {})
                self.assertEqual(saved_extra, extra)
                self.assertEqual(json.loads(saved_prompt["7"]["inputs"]["generation_settings"])["sampler"]["seed"], 17)
        self.assertEqual(snapshot_aio_execution_metadata(None, None, None, _settings(), {}), (None, None))

    def test_missing_identity_preserves_metadata_and_does_not_record_execution(self):
        prompt, extra = _graph(7)
        expected = copy.deepcopy(extra)
        saved_prompt, saved_extra = snapshot_aio_execution_metadata(prompt, extra, None, _settings(), {})
        self.assertEqual(saved_prompt, prompt)
        self.assertEqual(saved_extra, expected)
        self.assertEqual(extra, expected)
        self.assertIsNot(saved_prompt, prompt)
        self.assertIsNot(saved_extra, extra)

    def test_prompt_overlay_never_creates_or_retypes_unrelated_nodes(self):
        prompt, extra = _graph(7, 8)
        prompt["8"]["class_type"] = "OtherNode"
        extra["workflow"]["nodes"][1]["type"] = "OtherNode"
        original_other = copy.deepcopy(extra["workflow"]["nodes"][1])
        snapshot_aio_execution_metadata(prompt, extra, "8", _settings(), {})
        saved = snapshot_aio_prompt(prompt, extra)
        self.assertEqual(saved["8"], prompt["8"])
        self.assertEqual(extra["workflow"]["nodes"][1], original_other)
        self.assertEqual(snapshot_aio_prompt({}, extra), {})

    def test_named_widget_values_preserve_other_named_values(self):
        prompt, extra = _graph(7)
        extra["workflow"]["nodes"][0]["widgets_values"] = {"generation_settings": "old", "other": 123}
        snapshot_aio_execution_metadata(prompt, extra, [7], _settings(), {})
        values = extra["workflow"]["nodes"][0]["widgets_values"]
        self.assertEqual(json.loads(values["generation_settings"])["sampler"]["seed"], 17)
        self.assertEqual(values["other"], 123)

    def test_connected_settings_freeze_only_current_link_and_preserve_source_fanout(self):
        for object_link in (False, True):
            with self.subTest(object_link=object_link):
                prompt, extra = _graph(7, 8)
                graph = extra["workflow"]
                source, target = _connect_settings(graph, 7, 201, object_link=object_link)
                _connect_settings(graph, 8, 202, object_link=object_link)
                graph["last_link_id"] = 202
                prompt["7"]["inputs"]["generation_settings"] = ["settings_source", 0]
                prompt["8"]["inputs"]["generation_settings"] = ["settings_source", 0]
                original_prompt = copy.deepcopy(prompt)
                other_node = copy.deepcopy(graph["nodes"][1])
                other_links = copy.deepcopy([graph["links"][0], graph["links"][2]])
                saved_prompt, saved_extra = snapshot_aio_execution_metadata(prompt, extra, 7, _settings(17), {})
                self.assertIsNone(target["inputs"][1]["link"])
                self.assertEqual(source["outputs"][0]["links"], [202])
                self.assertEqual(source["widgets_values"], ["source unchanged"])
                self.assertEqual(graph["links"], other_links)
                self.assertEqual(graph["last_link_id"], 202)
                self.assertEqual(graph["nodes"][1], other_node)
                self.assertEqual(prompt, original_prompt)
                self.assertEqual(saved_prompt["8"]["inputs"]["generation_settings"], ["settings_source", 0])
                self.assertEqual(json.loads(saved_prompt["7"]["inputs"]["generation_settings"])["sampler"]["seed"], 17)
                self.assertEqual(saved_extra["workflow"], graph)

    def test_nested_connected_settings_freeze_in_own_graph_without_touching_root_links(self):
        prompt, extra = _graph("parent:7")
        inner = extra["workflow"]["nodes"][0]
        inner["id"] = 7
        inner["inputs"] = []
        subgraph = {"id": "subgraph-uuid", "nodes": [inner], "links": []}
        source, _ = _connect_settings(subgraph, 7, 301, object_link=True)
        root_links = copy.deepcopy(extra["workflow"]["links"])
        extra["workflow"]["nodes"] = [{"id": "parent", "type": "subgraph-uuid", "widgets_values": ["outer"]}]
        extra["workflow"]["definitions"] = {"subgraphs": [subgraph]}
        prompt["parent:7"]["inputs"]["generation_settings"] = ["parent:settings_source", 0]
        original_prompt = copy.deepcopy(prompt)
        snapshot_aio_execution_metadata(prompt, extra, "parent:7", _settings(37), {})
        self.assertEqual(subgraph["links"], [])
        self.assertEqual(source["outputs"][0]["links"], [])
        self.assertIsNone(inner["inputs"][0]["link"])
        self.assertEqual(extra["workflow"]["links"], root_links)
        self.assertEqual(prompt, original_prompt)

    def test_shared_subgraph_definition_is_not_rewritten_for_another_instance(self):
        prompt, extra = _graph("left:7", "right:7")
        inner = extra["workflow"]["nodes"][0]
        inner["id"] = 7
        inner["inputs"] = []
        subgraph = {"id": "shared-uuid", "nodes": [inner], "links": []}
        _connect_settings(subgraph, 7, 301)
        original_definition = copy.deepcopy(subgraph)
        extra["workflow"]["nodes"] = [{"id": side, "type": "shared-uuid"} for side in ("left", "right")]
        extra["workflow"]["definitions"] = {"subgraphs": [subgraph]}
        saved_prompt, _ = snapshot_aio_execution_metadata(prompt, extra, "left:7", _settings(37), {})
        self.assertEqual(subgraph, original_definition)
        self.assertEqual(json.loads(saved_prompt["left:7"]["inputs"]["generation_settings"])["sampler"]["seed"], 37)
        self.assertEqual(json.loads(saved_prompt["right:7"]["inputs"]["generation_settings"])["sampler"]["seed"], -1)


if __name__ == "__main__":
    unittest.main()
