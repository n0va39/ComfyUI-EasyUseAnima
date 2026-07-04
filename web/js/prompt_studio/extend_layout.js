// @ts-check

import {
  EXTEND_FIELD_NAMES,
} from "./constants.js";
import {
  desiredLegendHeight,
} from "./legend.js";
import {
  studioCurrentHeight,
  widgetHeight,
} from "./studio_textareas.js";
import {
  findInputEl,
  findWidget,
} from "./widgets.js";

function visibleExtendPromptWidgets(node) {
  return EXTEND_FIELD_NAMES
    .map((name) => findWidget(node, name))
    .filter((widget) => widget && !widget.hidden && !widget.__easyuseAnimaExtendHidden);
}

function firstExtendPromptY(node) {
  const visible = visibleExtendPromptWidgets(node);
  const yValues = visible
    .map((widget) => Number(widget.y))
    .filter((value) => Number.isFinite(value) && value > 0);
  if (yValues.length) {
    return Math.min(...yValues);
  }

  const firstIndex = node.widgets?.findIndex((widget) => EXTEND_FIELD_NAMES.includes(widget?.name)) ?? -1;
  if (firstIndex > 0) {
    for (let index = firstIndex - 1; index >= 0; index -= 1) {
      const widget = node.widgets[index];
      if (!widget || widget.hidden || widget.__easyuseAnimaExtendHidden) {
        continue;
      }
      const height = Number(widget.computeSize?.(node.size?.[0])?.[1]) || Number(widget.__height) || 24;
      const y = Number(widget.y);
      if (Number.isFinite(y)) {
        return y + height + 6;
      }
    }
  }
  return 120;
}

function layoutExtendPromptWidgets(node, hooks = {}) {
  if (!hooks.isExtendNode?.(node)) {
    return;
  }

  let cursorY = firstExtendPromptY(node);
  const visible = visibleExtendPromptWidgets(node);
  for (const widget of visible) {
    widget.y = cursorY;
    const input = findInputEl(widget);
    if (input) {
      input.style.height = `${studioCurrentHeight(widget, input)}px`;
    }
    cursorY += widgetHeight(widget, 72);
  }

  const controlsWidget = findWidget(node, "easyuse_anima_extend_slot_controls");
  if (controlsWidget && !controlsWidget.hidden) {
    hooks.refreshExtendSlotControlsSize?.(node);
    controlsWidget.y = cursorY;
    cursorY += Math.max(30, Number(controlsWidget.__height) || 30) + 8;
  }

  const legendWidget = findWidget(node, "easyuse_anima_color_legend");
  if (legendWidget && !legendWidget.hidden) {
    legendWidget.y = cursorY;
    cursorY += Math.max(desiredLegendHeight(), Number(legendWidget.__height) || 0) + 8;
  }

  const minHeight = Math.ceil(cursorY + 8);
  if (Number(node.size?.[1]) < minHeight) {
    node.setSize?.([node.size?.[0] || node.computeSize?.()[0] || 300, minHeight]);
  }
  hooks.markCanvasDirty?.();
}

export {
  firstExtendPromptY,
  layoutExtendPromptWidgets,
  visibleExtendPromptWidgets,
};
