// @ts-check

import {
  findInputEl,
  findWidget,
  firstValue,
} from "./widgets.js";
import {
  WILDCARD_SEED_MAX,
  normalizeWildcardSeedInput,
} from "./wildcard_seed_contract.js";

const WILDCARD_SEED_WIDGET_STATE = "__easyuseAnimaWildcardSeedContract";

function hookWildcardSeedWidget(node) {
  const widget = findWidget(node, "seed");
  if (!widget) {
    return false;
  }
  widget.options ||= {};
  widget.options.min = 0;
  widget.options.max = WILDCARD_SEED_MAX;
  widget.options.step = 1;

  const existing = widget[WILDCARD_SEED_WIDGET_STATE];
  if (existing?.wrapper === widget.callback) {
    existing.previousValue = widget.value;
    return false;
  }

  const state = /** @type {any} */ ({
    originalCallback: widget.callback,
    previousValue: widget.value,
    wrapper: null,
  });
  state.wrapper = function (value, ...args) {
    const candidate = arguments.length ? value : widget.value;
    const normalized = normalizeWildcardSeedInput(candidate);
    if (normalized == null) {
      widget.value = state.previousValue;
      return undefined;
    }
    widget.value = normalized;
    state.previousValue = normalized;
    return state.originalCallback?.apply(this, [normalized, ...args]);
  };
  widget[WILDCARD_SEED_WIDGET_STATE] = state;
  widget.callback = state.wrapper;
  return true;
}

function setRegularWidgetValue(node, name, value, hooks = {}) {
  const widget = findWidget(node, name);
  if (!widget) {
    return false;
  }
  widget.value = value;
  const input = findInputEl(widget);
  if (input) {
    input.value = String(value ?? "");
  }
  widget.callback?.(widget.value);
  hooks.markNodeDirty?.(node);
  return true;
}

function applyWildcardExecutedInputs(node, message, hooks = {}) {
  const payload = firstValue(message?.wildcard, null);
  if (!payload || typeof payload !== "object") {
    return;
  }
  if (payload.populated_text != null) {
    setRegularWidgetValue(node, "populated_text", String(payload.populated_text), hooks);
  }
  if (payload.mode != null) {
    setRegularWidgetValue(node, "mode", String(payload.mode), hooks);
  }
  if (payload.seed != null) {
    setRegularWidgetValue(node, "seed", Number(payload.seed), hooks);
  }
}

export {
  applyWildcardExecutedInputs,
  hookWildcardSeedWidget,
  setRegularWidgetValue,
};
