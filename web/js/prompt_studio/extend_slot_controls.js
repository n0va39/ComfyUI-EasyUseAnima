// @ts-check

import {
  EXTEND_FIELD_NAMES,
  EXTEND_SLOT_GROUPS,
} from "./constants.js";
import {
  applyExtendSlotVisibility,
  extendSlotShouldShow,
  extendVisibleSlots,
  writeExtendVisibleSlots,
} from "./extend_slots.js";
import {
  ensureExtendSlotStyle,
} from "./style.js";
import {
  psFormat,
  psText,
} from "./text.js";
import {
  findWidget,
  isWidgetInputLinked,
} from "./widgets.js";

function measureExtendSlotControlsHeight(node) {
  const container = node.__easyuseAnimaExtendSlotControlsEl;
  if (!container) {
    return 30;
  }
  return Math.max(
    30,
    Math.ceil(
      Number(container.scrollHeight)
      || Number(container.getBoundingClientRect?.().height)
      || 0,
    ) + 4,
  );
}

function refreshExtendSlotControlsSize(node) {
  const widget = findWidget(node, "easyuse_anima_extend_slot_controls");
  if (widget) {
    widget.__height = measureExtendSlotControlsHeight(node);
  }
}

function refreshExtendLayoutAfterSlotChange(node, hooks) {
  refreshExtendSlotControlsSize(node);
  for (const widget of hooks.visibleStudioWidgets(node)) {
    hooks.expandStudioInputToContent(node, widget);
  }
  hooks.layoutExtendPromptWidgets(node);
  hooks.refreshNodeSize(node, { immediate: true });
  requestAnimationFrame(() => {
    refreshExtendSlotControlsSize(node);
    for (const widget of hooks.visibleStudioWidgets(node)) {
      hooks.expandStudioInputToContent(node, widget);
    }
    hooks.layoutExtendPromptWidgets(node);
    hooks.refreshNodeSize(node, { immediate: true });
  });
}

function addNextExtendSlot(node, group, hooks) {
  const visible = extendVisibleSlots(node);
  const next = group.fields.find((fieldName) => !extendSlotShouldShow(node, fieldName));
  if (!next) {
    return;
  }
  visible.add(next);
  writeExtendVisibleSlots(node, visible);
  applyExtendSlotVisibility(node);
  renderExtendSlotControls(node, hooks);
  refreshExtendLayoutAfterSlotChange(node, hooks);
}

function hideExtendSlot(node, fieldName, hooks) {
  if (!EXTEND_FIELD_NAMES.includes(fieldName) || isWidgetInputLinked(node, fieldName)) {
    return;
  }
  const visible = extendVisibleSlots(node);
  visible.delete(fieldName);
  writeExtendVisibleSlots(node, visible);
  applyExtendSlotVisibility(node);
  renderExtendSlotControls(node, hooks);
  refreshExtendLayoutAfterSlotChange(node, hooks);
}

function extendSlotShortLabel(fieldName) {
  if (fieldName === "naia_prompt_3") {
    return "NAIA3";
  }
  const match = /_(\d+)$/.exec(fieldName);
  const index = match?.[1] || "";
  if (fieldName.startsWith("quality_")) {
    return `Q${index}`;
  }
  if (fieldName.startsWith("general_")) {
    return `G${index}`;
  }
  if (fieldName.startsWith("trailing_")) {
    return `T${index}`;
  }
  if (fieldName.startsWith("negative_")) {
    return `N${index}`;
  }
  return fieldName;
}

function extendSlotGroupLabel(group) {
  return group?.labelKey ? psText(group.labelKey) : String(group?.label || "");
}

function renderExtendSlotControls(node, hooks) {
  const container = node.__easyuseAnimaExtendSlotControlsEl;
  if (!container) {
    return;
  }
  container.innerHTML = "";
  const row = document.createElement("div");
  row.className = "easyuse-anima-extend-slot-row";
  for (const group of EXTEND_SLOT_GROUPS) {
    const shown = group.fields.filter((fieldName) => extendSlotShouldShow(node, fieldName)).length;
    const next = group.fields.find((fieldName) => !extendSlotShouldShow(node, fieldName));
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = `+ ${extendSlotGroupLabel(group)} ${shown}/${group.fields.length}`;
    button.disabled = !next;
    button.title = next ? psFormat("extend.showSlotTitle", { name: next }) : psText("extend.noHiddenSlots");
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      addNextExtendSlot(node, group, hooks);
    });
    row.append(button);
  }
  container.append(row);

  const visibleFields = EXTEND_SLOT_GROUPS
    .flatMap((group) => group.fields)
    .filter((fieldName) => extendSlotShouldShow(node, fieldName) && !isWidgetInputLinked(node, fieldName));
  if (visibleFields.length) {
    const hideRow = document.createElement("div");
    hideRow.className = "easyuse-anima-extend-slot-row easyuse-anima-extend-slot-hide-row";
    for (const fieldName of visibleFields) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = psFormat("extend.hideSlot", { slot: extendSlotShortLabel(fieldName) });
      button.title = psFormat("extend.hideSlotTitle", { name: fieldName });
      button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        hideExtendSlot(node, fieldName, hooks);
      });
      hideRow.append(button);
    }
    container.append(hideRow);
  }
  refreshExtendSlotControlsSize(node);
}

function ensureExtendSlotControls(node, hooks) {
  if (!hooks.isExtendNode(node)) {
    return;
  }
  ensureExtendSlotStyle();
  if (!node.__easyuseAnimaExtendSlotControlsEl) {
    const container = document.createElement("div");
    container.className = "easyuse-anima-extend-slots";
    node.__easyuseAnimaExtendSlotControlsEl = container;
    node.addDOMWidget?.("easyuse_anima_extend_slot_controls", "EasyUseAnimaExtendSlotControls", container, {
      serialize: false,
      hideOnZoom: false,
      getMinHeight: () => measureExtendSlotControlsHeight(node),
    });
  }
  renderExtendSlotControls(node, hooks);
}

export {
  ensureExtendSlotControls,
  extendSlotGroupLabel,
  extendSlotShortLabel,
  measureExtendSlotControlsHeight,
  refreshExtendSlotControlsSize,
  renderExtendSlotControls,
};
