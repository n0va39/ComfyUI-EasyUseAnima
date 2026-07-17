// @ts-check

/**
 * @param {any} value
 * @param {string} [step]
 * @returns {HTMLInputElement}
 */
export function aioCreateNumberInput(value, step = "1") {
  const input = document.createElement("input");
  input.type = "number";
  input.step = step;
  input.value = value;
  return input;
}

/**
 * @param {any} value
 * @returns {HTMLInputElement}
 */
export function aioCreateTextInput(value) {
  const input = document.createElement("input");
  input.type = "text";
  input.value = value ?? "";
  return input;
}

/**
 * @param {any} value
 * @returns {HTMLTextAreaElement}
 */
export function aioCreateTextareaInput(value) {
  const textarea = document.createElement("textarea");
  textarea.value = value ?? "";
  return textarea;
}

/**
 * @param {any} value
 * @returns {HTMLInputElement}
 */
export function aioCreateCheckboxInput(value) {
  const input = document.createElement("input");
  input.type = "checkbox";
  input.checked = !!value;
  return input;
}

/**
 * @param {any[]} options
 * @param {any} value
 * @returns {HTMLSelectElement}
 */
export function aioCreateSelectInput(options, value) {
  const select = document.createElement("select");
  for (const optionSpec of options) {
    const optionValue = typeof optionSpec === "object" && optionSpec
      ? String(optionSpec.value ?? "")
      : String(optionSpec ?? "");
    const option = document.createElement("option");
    option.value = optionValue;
    option.textContent = typeof optionSpec === "object" && optionSpec
      ? String(optionSpec.label ?? optionValue)
      : optionValue;
    option.disabled = !!(typeof optionSpec === "object" && optionSpec?.disabled);
    if (typeof optionSpec === "object" && optionSpec?.title) {
      option.title = String(optionSpec.title);
    }
    if (optionValue === value) {
      option.selected = true;
    }
    select.append(option);
  }
  return select;
}

/**
 * @param {any} spec
 * @param {any} [fallback]
 * @returns {any}
 */
export function aioNodeInputDefault(spec, fallback = "") {
  const options = Array.isArray(spec) && spec[1] && typeof spec[1] === "object" ? spec[1] : null;
  if (options && Object.prototype.hasOwnProperty.call(options, "default")) {
    return options.default;
  }
  return fallback;
}

/**
 * @param {any} spec
 * @param {any} [value]
 * @returns {HTMLInputElement | HTMLSelectElement | null}
 */
export function aioNodeInputControlForSpec(spec, value) {
  if (!Array.isArray(spec)) {
    return null;
  }
  const type = spec[0];
  if (Array.isArray(type)) {
    return aioCreateSelectInput(type, value ?? aioNodeInputDefault(spec, type[0] ?? ""));
  }
  const normalizedType = String(type || "").toUpperCase();
  if (normalizedType === "BOOLEAN") {
    return aioCreateCheckboxInput(value ?? aioNodeInputDefault(spec, false));
  }
  if (normalizedType === "INT") {
    const input = aioCreateNumberInput(value ?? aioNodeInputDefault(spec, 0), "1");
    input.step = "1";
    return input;
  }
  if (normalizedType === "FLOAT") {
    return aioCreateNumberInput(value ?? aioNodeInputDefault(spec, 0), "0.01");
  }
  if (normalizedType === "STRING") {
    return aioCreateTextInput(value ?? aioNodeInputDefault(spec, ""));
  }
  return null;
}

/**
 * @param {any} control
 * @returns {any}
 */
export function aioValueFromNodeInputControl(control) {
  if (!control) {
    return null;
  }
  if (control.type === "checkbox") {
    return !!control.checked;
  }
  if (control.type === "number") {
    return Number(control.value || 0);
  }
  return control.value;
}
