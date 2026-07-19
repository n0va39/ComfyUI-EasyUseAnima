// @ts-check

import {
  optionalWildcardSeed,
} from "./wildcard_seed_contract.js";

const PREVIOUS_WILDCARD_EXECUTION_PROPERTY =
  "easyuse_anima_previous_wildcard_execution";

/** @param {any} value */
function normalizePreviousWildcardMode(value) {
  const normalized = String(value || "").trim().toLowerCase();
  return normalized === "sequential" || normalized === "순차"
    ? "sequential"
    : "populate";
}

/** @param {any} value */
function wildcardModeWidgetValue(value) {
  return normalizePreviousWildcardMode(value) === "sequential" ? "순차" : "일반";
}

/** @param {any} value */
function normalizePreviousWildcardExecution(value) {
  let parsed = value;
  if (typeof parsed === "string") {
    try {
      parsed = JSON.parse(parsed);
    } catch {
      return null;
    }
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    return null;
  }
  const seed = optionalWildcardSeed(parsed.seed);
  if (seed == null) {
    return null;
  }
  return {
    version: 1,
    seed,
    mode: normalizePreviousWildcardMode(parsed.mode),
  };
}

/** @param {any} node */
function readPreviousWildcardExecution(node) {
  return normalizePreviousWildcardExecution(
    node?.properties?.[PREVIOUS_WILDCARD_EXECUTION_PROPERTY],
  );
}

/** @param {any} node @param {any} execution */
function writePreviousWildcardExecution(node, execution) {
  const normalized = normalizePreviousWildcardExecution(execution);
  if (!node || !normalized) {
    return null;
  }
  node.properties ||= {};
  node.properties[PREVIOUS_WILDCARD_EXECUTION_PROPERTY] = JSON.stringify(normalized);
  return normalized;
}

/**
 * Save a workflow as a reproducible snapshot of the most recently accepted
 * wildcard execution while leaving the live node on its next-run seed.
 *
 * @param {any} node
 * @param {any} serialized
 * @param {{modeWidgetIndex: number, seedWidgetIndex: number, controlWidgetIndex: number}} contract
 */
function serializePreviousWildcardExecution(node, serialized, contract) {
  const execution = readPreviousWildcardExecution(node);
  if (!execution || !serialized || !Array.isArray(serialized.widgets_values)) {
    return false;
  }
  serialized.properties ||= {};
  serialized.properties[PREVIOUS_WILDCARD_EXECUTION_PROPERTY] = JSON.stringify(execution);
  const values = [
    [contract.modeWidgetIndex, wildcardModeWidgetValue(execution.mode)],
    [contract.seedWidgetIndex, execution.seed],
    [contract.controlWidgetIndex, "fixed"],
  ];
  for (const [index, value] of values) {
    while (serialized.widgets_values.length <= index) {
      serialized.widgets_values.push(null);
    }
    serialized.widgets_values[index] = value;
  }
  return true;
}

export {
  PREVIOUS_WILDCARD_EXECUTION_PROPERTY,
  normalizePreviousWildcardExecution,
  normalizePreviousWildcardMode,
  readPreviousWildcardExecution,
  serializePreviousWildcardExecution,
  wildcardModeWidgetValue,
  writePreviousWildcardExecution,
};
