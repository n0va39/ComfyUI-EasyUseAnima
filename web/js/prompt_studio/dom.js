// @ts-check

import {
  ADVANCED_NATIVE_CONTROL_EVENTS,
} from "./constants.js";
import {
  getAdvancedEditorElement,
} from "./state.js";

function stopAdvancedControlEvent(event) {
  event.stopPropagation();
}

function protectAdvancedNativeControl(element) {
  if (!(element instanceof HTMLElement)) {
    return element;
  }
  for (const eventName of ADVANCED_NATIVE_CONTROL_EVENTS) {
    element.addEventListener(eventName, stopAdvancedControlEvent);
  }
  return element;
}

function updateAdvancedSummary(node, groupId, text) {
  getAdvancedEditorElement(node)
    ?.querySelector?.(`[data-easyuse-anima-control-summary="${groupId}"]`)
    ?.replaceChildren(document.createTextNode(text));
}

function closeAdvancedHelpPopovers() {
  document.querySelectorAll(".easyuse-anima-advanced-help-popover").forEach((element) => element.remove());
}

function openAdvancedHelpPopover(button, text) {
  closeAdvancedHelpPopovers();
  const popover = document.createElement("div");
  popover.className = "easyuse-anima-advanced-help-popover";
  popover.textContent = text;
  document.body.append(popover);
  const rect = button.getBoundingClientRect();
  const margin = 8;
  const width = Number(popover.offsetWidth) || 260;
  const height = Number(popover.offsetHeight) || 80;
  const left = Math.min(
    Math.max(margin, rect.right + margin),
    Math.max(margin, (Number(globalThis.innerWidth) || 0) - width - margin),
  );
  const preferredTop = rect.top + rect.height / 2 - height / 2;
  const top = Math.min(
    Math.max(margin, preferredTop),
    Math.max(margin, (Number(globalThis.innerHeight) || 0) - height - margin),
  );
  popover.style.left = `${Math.round(left)}px`;
  popover.style.top = `${Math.round(top)}px`;
  const close = (event) => {
    if (event?.target === button || popover.contains(event?.target)) {
      return;
    }
    popover.remove();
    document.removeEventListener("pointerdown", close, true);
  };
  setTimeout(() => document.addEventListener("pointerdown", close, true), 0);
}

export {
  closeAdvancedHelpPopovers,
  openAdvancedHelpPopover,
  protectAdvancedNativeControl,
  stopAdvancedControlEvent,
  updateAdvancedSummary,
};
