// @ts-check

import {
  NAIA_ADVANCED_RESOLUTION_BUCKET,
} from "./constants.js";
import {
  getAdvancedEditorElement,
  getAdvancedFields,
} from "./state.js";
import {
  findWidget,
} from "./widgets.js";

const ADVANCED_NAIA_RESOLUTION_SURFACE = "prompt.execution.naia_resolution";

function advancedNaiaFieldSurface(fieldId) {
  const normalized = String(fieldId || "").trim();
  return normalized ? `prompt.execution.naia:${normalized}` : null;
}

function captureAdvancedNaiaFieldSnapshots(fields) {
  const snapshots = [];
  for (const field of fields || []) {
    if (field?.type !== "naia" || field?.enabled === false) {
      continue;
    }
    const surface = advancedNaiaFieldSurface(field?.id);
    if (surface == null) {
      continue;
    }
    snapshots.push(Object.freeze({
      fieldId: String(field.id),
      pane: String(field.pane || "positive"),
      type: "naia",
      enabled: true,
      text: String(field.text || ""),
      surface,
    }));
  }
  return snapshots;
}

function currentAdvancedNaiaField(node, snapshot) {
  if (!snapshot || typeof snapshot !== "object") {
    return null;
  }
  const field = (getAdvancedFields(node) || []).find(
    (candidate) => candidate?.id === snapshot.fieldId,
  );
  if (
    !field
    || String(field.pane || "positive") !== snapshot.pane
    || String(field.type || "general") !== snapshot.type
    || (field.enabled !== false) !== snapshot.enabled
    || String(field.text || "") !== snapshot.text
  ) {
    return null;
  }
  return field;
}

function commitAdvancedNaiaFieldCanonical(
  node,
  snapshot,
  value,
  { persistFields = null, commitView = null } = {},
) {
  const field = currentAdvancedNaiaField(node, snapshot);
  if (!field) {
    return false;
  }
  const text = String(value ?? "");
  field.text = text;
  const fields = getAdvancedFields(node) || [];
  persistFields?.(node, fields);
  const editor = getAdvancedEditorElement(node);
  const textarea = [...(editor?.querySelectorAll?.(
    "textarea[data-easyuse-anima-advanced-field-id]",
  ) || [])].find((candidate) => (
    String(candidate?.dataset?.easyuseAnimaAdvancedFieldId || "") === snapshot.fieldId
  ));
  commitView?.(node, field, textarea || null, text);
  return true;
}

function advancedNaiaResolutionSnapshot(node) {
  return {
    bucket: String(findWidget(node, "resolution_bucket")?.value ?? ""),
    size: String(findWidget(node, "resolution_size")?.value ?? ""),
    customWidth: String(findWidget(node, "resolution_custom_width")?.value ?? ""),
    customHeight: String(findWidget(node, "resolution_custom_height")?.value ?? ""),
  };
}

function captureAdvancedNaiaResolutionSnapshot(node) {
  const snapshot = advancedNaiaResolutionSnapshot(node);
  if (snapshot.bucket !== NAIA_ADVANCED_RESOLUTION_BUCKET) {
    return null;
  }
  return Object.freeze({
    ...snapshot,
    surface: ADVANCED_NAIA_RESOLUTION_SURFACE,
  });
}

function currentAdvancedNaiaResolution(node, snapshot) {
  if (!snapshot || typeof snapshot !== "object") {
    return false;
  }
  const current = advancedNaiaResolutionSnapshot(node);
  return current.bucket === NAIA_ADVANCED_RESOLUTION_BUCKET
    && current.bucket === snapshot.bucket
    && current.size === snapshot.size
    && current.customWidth === snapshot.customWidth
    && current.customHeight === snapshot.customHeight;
}

function commitAdvancedNaiaResolution(
  node,
  snapshot,
  value,
  { commitView = null } = {},
) {
  const width = Number(value?.width);
  const height = Number(value?.height);
  if (
    !currentAdvancedNaiaResolution(node, snapshot)
    || !Number.isFinite(width)
    || !Number.isFinite(height)
    || width <= 0
    || height <= 0
    || typeof commitView !== "function"
  ) {
    return false;
  }
  return commitView(node, width, height) !== false;
}

export {
  ADVANCED_NAIA_RESOLUTION_SURFACE,
  advancedNaiaFieldSurface,
  captureAdvancedNaiaFieldSnapshots,
  captureAdvancedNaiaResolutionSnapshot,
  commitAdvancedNaiaFieldCanonical,
  commitAdvancedNaiaResolution,
  currentAdvancedNaiaField,
  currentAdvancedNaiaResolution,
};
