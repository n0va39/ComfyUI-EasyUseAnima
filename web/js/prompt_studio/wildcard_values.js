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
const WILDCARD_MODE_WIDGET_STATE = "__easyuseAnimaWildcardModeContract";

/** @param {any} value */
function normalizeWildcardNodeMode(value) {
  const normalized = String(value || "").trim().toLowerCase();
  return normalized === "fixed"
    || normalized === "고정"
    || normalized === "reproduce"
    || normalized === "재현"
    ? "고정"
    : "일반";
}

/** @param {any} node */
function nativeSeedControlWidget(node) {
  return (node?.widgets || []).find((widget) => {
    const name = String(widget?.name || "").trim().toLowerCase();
    return name === "control_after_generate" || name === "after_generate";
  }) || null;
}

/** @param {any} node @param {boolean} resetSeedControl */
function syncWildcardNodeControls(node, resetSeedControl = false) {
  const modeWidget = findWidget(node, "mode");
  const populatedWidget = findWidget(node, "populated_text");
  if (!modeWidget || !populatedWidget) {
    return false;
  }
  const mode = normalizeWildcardNodeMode(modeWidget.value);
  modeWidget.value = mode;
  const input = findInputEl(populatedWidget);
  if (input) {
    input.disabled = mode !== "고정";
  }
  const seedControl = nativeSeedControlWidget(node);
  if (resetSeedControl && seedControl) {
    seedControl.value = "fixed";
    seedControl.callback?.(seedControl.value);
  }
  return true;
}

function hookWildcardSeedWidget(node, options = {}) {
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
  } else {
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
  }

  const modeWidget = findWidget(node, "mode");
  if (modeWidget) {
    const modeState = modeWidget[WILDCARD_MODE_WIDGET_STATE];
    if (modeState?.wrapper !== modeWidget.callback) {
      const state = /** @type {any} */ ({ originalCallback: modeWidget.callback, wrapper: null });
      state.wrapper = function (value, ...args) {
        modeWidget.value = normalizeWildcardNodeMode(arguments.length ? value : modeWidget.value);
        const result = state.originalCallback?.apply(this, [modeWidget.value, ...args]);
        syncWildcardNodeControls(node, false);
        return result;
      };
      modeWidget[WILDCARD_MODE_WIDGET_STATE] = state;
      modeWidget.callback = state.wrapper;
    }
  }
  syncWildcardNodeControls(node, options.resetSeedControl === true);
  return true;
}

function syncWildcardSerialization(node, serialized) {
  if (!node?.__easyuseAnimaWildcardHasPopulatedResult || !Array.isArray(serialized?.widgets_values)) {
    return false;
  }
  const modeWidget = findWidget(node, "mode");
  const modeIndex = (node.widgets || []).indexOf(modeWidget);
  if (modeIndex >= 0) {
    serialized.widgets_values[modeIndex] = "고정";
  }
  const seedControl = nativeSeedControlWidget(node);
  const seedControlIndex = (node.widgets || []).indexOf(seedControl);
  if (seedControlIndex >= 0) {
    serialized.widgets_values[seedControlIndex] = "fixed";
  }
  return modeIndex >= 0;
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
    node.__easyuseAnimaWildcardHasPopulatedResult = true;
  }
  if (payload.mode != null) {
    setRegularWidgetValue(node, "mode", String(payload.mode), hooks);
  }
  syncWildcardNodeControls(node, false);
}

export {
  applyWildcardExecutedInputs,
  hookWildcardSeedWidget,
  syncWildcardSerialization,
  setRegularWidgetValue,
};
