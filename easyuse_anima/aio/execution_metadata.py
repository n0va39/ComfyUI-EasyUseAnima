"""Freeze AiO execution settings for image metadata without changing the prompt graph."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from ..common.values import _single_value
from ..workflow import _get_workflow_node

_AIO_NODE_TYPE = "EasyUseAnimaAIOGenerator"
_EXECUTIONS_KEY = "easyuse_anima_executions"
_MISSING_INPUT = object()


def _settings_json(settings: dict[str, Any]) -> str:
    return json.dumps(settings, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def _update_prompt_snapshot(prompt, node_id: str, settings: dict[str, Any]) -> None:
    if not isinstance(prompt, dict):
        return
    node = prompt.get(node_id)
    if not isinstance(node, dict) or node.get("class_type") != _AIO_NODE_TYPE:
        return
    inputs = node.get("inputs")
    if isinstance(inputs, dict):
        inputs["generation_settings"] = _settings_json(settings)


def _prompt_settings_input(prompt, node_id: str):
    node = prompt.get(node_id) if isinstance(prompt, dict) else None
    inputs = node.get("inputs") if isinstance(node, dict) else None
    return inputs.get("generation_settings", _MISSING_INPUT) if isinstance(inputs, dict) else _MISSING_INPUT


def _parsed_settings_input(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            pass
    return value


def _source_input_fingerprint(value) -> str | None:
    if value is _MISSING_INPUT:
        return None
    serialized = json.dumps(
        _parsed_settings_input(value), ensure_ascii=True, allow_nan=False,
        sort_keys=True, separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _record_matches_prompt(prompt, node_id: str, settings: dict[str, Any], record: dict) -> bool:
    current = _prompt_settings_input(prompt, node_id)
    parsed = _parsed_settings_input(current)
    if isinstance(parsed, dict) and parsed == settings:
        return True
    source_fingerprint = record.get("source_input_sha256")
    return isinstance(source_fingerprint, str) and source_fingerprint == _source_input_fingerprint(current)


def _workflow(extra_pnginfo):
    pnginfo = _single_value(extra_pnginfo)
    if not isinstance(pnginfo, dict):
        return None
    workflow = pnginfo.get("workflow")
    return workflow if isinstance(workflow, dict) else None


def _editable_workflow_graph(extra_pnginfo, node_id: str):
    workflow = _workflow(extra_pnginfo)
    if workflow is None:
        return None
    parts = node_id.split(":")
    if len(parts) == 1:
        return workflow
    definitions = workflow.get("definitions")
    subgraphs = definitions.get("subgraphs") if isinstance(definitions, dict) else None
    if not isinstance(subgraphs, list):
        return None
    graphs = [workflow, *(graph for graph in subgraphs if isinstance(graph, dict))]
    containing_graph = None
    for index in range(1, len(parts)):
        parent = _get_workflow_node(extra_pnginfo, ":".join(parts[:index]))
        if not isinstance(parent, dict):
            return None
        graph_type = parent.get("type")
        # A shared definition cannot express different per-instance widget or
        # link values. Keep it intact instead of changing another instance.
        instances = sum(
            1
            for graph in graphs
            for node in graph.get("nodes", [])
            if isinstance(node, dict) and node.get("type") == graph_type
        )
        if instances != 1:
            return None
        containing_graph = next(
            (graph for graph in subgraphs if isinstance(graph, dict) and str(graph.get("id")) == str(graph_type)),
            None,
        )
        if containing_graph is None:
            return None
    return containing_graph


def _link_details(link):
    if isinstance(link, (list, tuple)) and len(link) >= 5:
        return link[0], link[1], link[2], link[3], link[4]
    if isinstance(link, dict):
        return tuple(link.get(key) for key in ("id", "origin_id", "origin_slot", "target_id", "target_slot"))
    return None


def _freeze_connected_settings(graph, node) -> None:
    inputs = node.get("inputs")
    if not isinstance(inputs, list):
        return
    for slot, input_info in enumerate(inputs):
        if not isinstance(input_info, dict):
            continue
        widget = input_info.get("widget")
        if input_info.get("name") != "generation_settings" and not (
            isinstance(widget, dict) and widget.get("name") == "generation_settings"
        ):
            continue
        link_id = input_info.get("link")
        if link_id is None:
            continue
        input_info["link"] = None
        links = graph.get("links")
        if not isinstance(links, list):
            continue
        retained_links = []
        for link in links:
            details = _link_details(link)
            if details is None or not (
                str(details[0]) == str(link_id)
                and str(details[3]) == str(node.get("id"))
                and details[4] == slot
            ):
                retained_links.append(link)
                continue
            source = next(
                (item for item in graph.get("nodes", []) if isinstance(item, dict) and str(item.get("id")) == str(details[1])),
                None,
            )
            outputs = source.get("outputs") if isinstance(source, dict) else None
            origin_slot = details[2]
            if isinstance(outputs, list) and isinstance(origin_slot, int) and 0 <= origin_slot < len(outputs):
                output = outputs[origin_slot]
                output_links = output.get("links") if isinstance(output, dict) else None
                if isinstance(output_links, list):
                    output["links"] = [value for value in output_links if str(value) != str(link_id)]
        graph["links"] = retained_links


def _record_matches_workflow(extra_pnginfo, node_id: str, settings: dict[str, Any]) -> bool:
    node = _get_workflow_node(extra_pnginfo, node_id)
    if not isinstance(node, dict) or node.get("type") != _AIO_NODE_TYPE:
        return False
    values = node.get("widgets_values")
    if isinstance(values, list) and values:
        stored = values[0]
    elif isinstance(values, dict):
        stored = values.get("generation_settings")
    else:
        return False
    if isinstance(stored, str):
        try:
            stored = json.loads(stored)
        except (ValueError, TypeError):
            return False
    return stored == settings


def snapshot_aio_prompt(workflow_prompt: object | None, extra_pnginfo: object | None) -> Any:
    """Apply recorded executions to a private API prompt copy at a save boundary."""
    prompt_copy = copy.deepcopy(workflow_prompt)
    workflow = _workflow(extra_pnginfo)
    if workflow is None:
        return prompt_copy
    extra = workflow.get("extra")
    executions = extra.get(_EXECUTIONS_KEY) if isinstance(extra, dict) else None
    if isinstance(executions, dict):
        for node_id, record in executions.items():
            settings = record.get("generation_settings") if isinstance(record, dict) else None
            # Image reloads retain old records. A subsequently edited widget is
            # authoritative until that node completes another execution.
            if (
                isinstance(settings, dict)
                and _record_matches_workflow(extra_pnginfo, str(node_id), settings)
                and _record_matches_prompt(workflow_prompt, str(node_id), settings, record)
            ):
                _update_prompt_snapshot(prompt_copy, str(node_id), settings)
    return prompt_copy


def snapshot_aio_execution_metadata(
    workflow_prompt: object | None,
    extra_pnginfo: object | None,
    unique_id: object | None,
    generation_settings: dict[str, Any],
    execution_metadata: dict[str, Any],
) -> tuple[Any, Any]:
    """Publish this node's replay settings and return detached saving snapshots.

    EXTRA_PNGINFO is shared with downstream savers, so its workflow receives the
    completed execution. PROMPT is also the live execution graph and is only
    changed in the returned copy. Records use full API ids for subgraph nodes.
    """
    settings = copy.deepcopy(generation_settings)
    sampler = settings.get("sampler")
    if isinstance(sampler, dict):
        sampler["seed_after_generate"] = "fixed"
    node_id = _single_value(unique_id)
    if node_id is None:
        return snapshot_aio_prompt(workflow_prompt, extra_pnginfo), copy.deepcopy(extra_pnginfo)
    node_id = str(node_id)
    workflow = _workflow(extra_pnginfo)
    if workflow is not None:
        node = _get_workflow_node(extra_pnginfo, node_id)
        graph = _editable_workflow_graph(extra_pnginfo, node_id)
        if isinstance(node, dict) and node.get("type") == _AIO_NODE_TYPE and graph is not None:
            values = node.get("widgets_values", [])
            if isinstance(values, list):
                node["widgets_values"] = [_settings_json(settings), *values[1:]]
            elif isinstance(values, dict):
                node["widgets_values"] = {**values, "generation_settings": _settings_json(settings)}
            _freeze_connected_settings(graph, node)
        extra = workflow.get("extra")
        if not isinstance(extra, dict):
            extra = {}
            workflow["extra"] = extra
        executions = extra.get(_EXECUTIONS_KEY)
        if not isinstance(executions, dict):
            executions = {}
            extra[_EXECUTIONS_KEY] = executions
        executions[node_id] = {
            "generation_settings": settings,
            "execution": copy.deepcopy(execution_metadata),
            "source_input_sha256": _source_input_fingerprint(_prompt_settings_input(workflow_prompt, node_id)),
        }
    prompt_copy = snapshot_aio_prompt(workflow_prompt, extra_pnginfo)
    _update_prompt_snapshot(prompt_copy, node_id, settings)
    return prompt_copy, copy.deepcopy(extra_pnginfo)


__all__ = ("snapshot_aio_execution_metadata", "snapshot_aio_prompt")
