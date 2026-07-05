// @ts-check

function getHiddenWidgets(node) {
  return node?.__easyuseAnimaHiddenWidgets || null;
}

function ensureHiddenWidgets(node) {
  node.__easyuseAnimaHiddenWidgets ||= {};
  return node.__easyuseAnimaHiddenWidgets;
}

function findHiddenWidget(node, name) {
  return getHiddenWidgets(node)?.[name] || null;
}

function setHiddenWidget(node, name, widget) {
  ensureHiddenWidgets(node)[name] = widget;
}

function getAdvancedEditorElement(node) {
  return node?.__easyuseAnimaAdvancedEditorEl || null;
}

function setAdvancedEditorElement(node, element) {
  node.__easyuseAnimaAdvancedEditorEl = element;
  return element;
}

function getAdvancedFields(node) {
  return node?.__easyuseAnimaAdvancedFields || null;
}

function setAdvancedFields(node, fields) {
  node.__easyuseAnimaAdvancedFields = fields;
  return fields;
}

function getPendingAdvancedFieldsValue(node) {
  return node?.__easyuseAnimaPendingAdvancedFieldsValue || "";
}

function setPendingAdvancedFieldsValue(node, value) {
  node.__easyuseAnimaPendingAdvancedFieldsValue = value;
}

function clearPendingAdvancedFieldsValue(node) {
  delete node.__easyuseAnimaPendingAdvancedFieldsValue;
}

export {
  clearPendingAdvancedFieldsValue,
  findHiddenWidget,
  getAdvancedEditorElement,
  getAdvancedFields,
  getPendingAdvancedFieldsValue,
  setAdvancedEditorElement,
  setAdvancedFields,
  setHiddenWidget,
  setPendingAdvancedFieldsValue,
};
