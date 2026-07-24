// @ts-check

import {
  findInputEl,
  findWidget,
} from "./widgets.js";

function connectedStudioControl(candidate) {
  if (
    !(candidate instanceof HTMLTextAreaElement)
    && !(candidate instanceof HTMLInputElement)
  ) {
    return null;
  }
  return candidate.isConnected === false ? null : candidate;
}

function nodeElementForCanvas(node, canvasElement) {
  const root = canvasElement?.parentElement;
  const nodeId = String(node?.id ?? "");
  if (!root || !nodeId) {
    return null;
  }
  return Array.from(root.querySelectorAll?.(".lg-node[data-node-id]") || [])
    .find((element) => String(element?.dataset?.nodeId || "") === nodeId)
    || null;
}

/**
 * Resolve the current Prompt Studio field input without installing a global
 * listener or registry. Legacy/custom DOM widgets keep their canonical
 * inputEl/element seam. Vue Node 2.0 fields are matched only inside the owning
 * node: named controls use aria-label, while anonymous multiline controls use
 * the current visible Prompt Studio field order.
 */
function resolveStudioInput(node, widget, fieldNames, canvasElement) {
  const current = findInputEl(widget);
  if (current) {
    return current;
  }

  const nodeElement = nodeElementForCanvas(node, canvasElement);
  if (!nodeElement || !widget?.name) {
    return null;
  }
  const controls = Array.from(
    nodeElement.querySelectorAll?.('[data-testid="node-widget"] textarea, [data-testid="node-widget"] input')
    || [],
  );
  const named = controls.find(
    (control) => control?.getAttribute?.("aria-label") === widget.name,
  );
  const namedInput = connectedStudioControl(named);
  if (namedInput) {
    widget.__easyuseAnimaStudioInput = namedInput;
    return namedInput;
  }

  const visibleFieldNames = fieldNames.filter((name) => {
    const fieldWidget = findWidget(node, name);
    return fieldWidget
      && fieldWidget.hidden !== true
      && fieldWidget.options?.hidden !== true
      && fieldWidget.__easyuseAnimaExtendHidden !== true;
  });
  const namedFieldNames = new Set(
    controls
      .map((control) => control?.getAttribute?.("aria-label"))
      .filter((name) => visibleFieldNames.includes(name)),
  );
  const anonymousFieldNames = visibleFieldNames.filter(
    (name) => !namedFieldNames.has(name),
  );
  const fieldIndex = anonymousFieldNames.indexOf(widget.name);
  if (fieldIndex < 0) {
    return null;
  }
  const anonymousControls = controls.filter(
    (control) => !control?.getAttribute?.("aria-label"),
  );
  const input = connectedStudioControl(anonymousControls[fieldIndex]);
  if (!input) {
    return null;
  }
  widget.__easyuseAnimaStudioInput = input;
  return input;
}

export {
  resolveStudioInput,
};
