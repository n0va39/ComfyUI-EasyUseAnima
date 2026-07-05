// @ts-check

function advancedPaneFields(fields, pane) {
  return (fields || []).filter((field) => field.pane === pane);
}

function hasAdvancedNaia(fields, pane) {
  return (fields || []).some((field) => field.pane === pane && field.type === "naia");
}

function hasPositiveNaia(fields) {
  return (fields || []).some((field) => field.pane === "positive" && field.type === "naia");
}

function hasPositiveTrigger(fields) {
  return (fields || []).some((field) => field.pane === "positive" && field.type === "trigger");
}

function moveAdvancedFieldInPane(fields, field, direction) {
  if (!Array.isArray(fields) || !field) {
    return false;
  }
  const paneFields = fields
    .map((item, index) => ({ item, index }))
    .filter(({ item }) => item.pane === field.pane);
  const current = paneFields.findIndex(({ item }) => item.id === field.id);
  const target = current + direction;
  if (current < 0 || target < 0 || target >= paneFields.length) {
    return false;
  }
  const from = paneFields[current].index;
  const to = paneFields[target].index;
  const [removed] = fields.splice(from, 1);
  fields.splice(to, 0, removed);
  return true;
}

export {
  advancedPaneFields,
  hasAdvancedNaia,
  hasPositiveNaia,
  hasPositiveTrigger,
  moveAdvancedFieldInPane,
};
