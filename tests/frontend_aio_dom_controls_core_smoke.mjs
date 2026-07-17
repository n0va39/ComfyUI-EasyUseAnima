import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function assertJsonEqual(actual, expected, message) {
  assert(JSON.stringify(actual) === JSON.stringify(expected), message);
}

class FakeElement {
  constructor(tagName) {
    this.tagName = String(tagName).toUpperCase();
    this.type = "";
    this.step = "";
    this.checked = false;
    this.disabled = false;
    this.selected = false;
    this.title = "";
    this.textContent = "";
    this.children = [];
    this._value = "";
  }

  get value() {
    return this._value;
  }

  set value(value) {
    this._value = String(value);
  }

  append(...children) {
    this.children.push(...children);
  }
}

const previousDocument = globalThis.document;
const hadDocument = Object.prototype.hasOwnProperty.call(globalThis, "document");
delete globalThis.document;

const controlsModule = await import(dataModule("../web/js/aio/dom_controls.js"));
const expectedExports = [
  "aioCreateCheckboxInput",
  "aioCreateNumberInput",
  "aioCreateSelectInput",
  "aioCreateTextInput",
  "aioCreateTextareaInput",
  "aioNodeInputControlForSpec",
  "aioNodeInputDefault",
  "aioValueFromNodeInputControl",
];
assertJsonEqual(
  Object.keys(controlsModule).sort(),
  expectedExports,
  "AiO DOM controls core must expose only its public helper contract",
);

globalThis.document = {
  createElement(tagName) {
    return new FakeElement(tagName);
  },
};

try {
  const {
    aioCreateCheckboxInput,
    aioCreateNumberInput,
    aioCreateSelectInput,
    aioCreateTextInput,
    aioCreateTextareaInput,
    aioNodeInputControlForSpec,
    aioNodeInputDefault,
    aioValueFromNodeInputControl,
  } = controlsModule;

  const number = aioCreateNumberInput(12);
  assert(
    number.tagName === "INPUT"
      && number.type === "number"
      && number.step === "1"
      && number.value === "12",
    "Number controls must keep the native input type, default step, and value",
  );
  const preciseNumber = aioCreateNumberInput("1.25", "0.05");
  assert(
    preciseNumber.step === "0.05" && preciseNumber.value === "1.25",
    "Number controls must preserve an explicit step and value",
  );

  const text = aioCreateTextInput(null);
  const textarea = aioCreateTextareaInput(undefined);
  assert(
    text.tagName === "INPUT" && text.type === "text" && text.value === "",
    "Text controls must normalize nullish values to an empty native input",
  );
  assert(
    textarea.tagName === "TEXTAREA" && textarea.value === "",
    "Textarea controls must normalize nullish values to an empty textarea",
  );

  const unchecked = aioCreateCheckboxInput(0);
  const checked = aioCreateCheckboxInput("enabled");
  assert(
    unchecked.tagName === "INPUT"
      && unchecked.type === "checkbox"
      && unchecked.checked === false
      && checked.checked === true,
    "Checkbox controls must preserve their native type and boolean coercion",
  );

  const select = aioCreateSelectInput([
    "alpha",
    {
      value: "beta",
      label: "Beta label",
      disabled: true,
      title: "Beta title",
    },
    { value: 3 },
  ], "beta");
  assert(select.tagName === "SELECT", "Choice controls must create a native select");
  assertJsonEqual(
    select.children.map((option) => option.value),
    ["alpha", "beta", "3"],
    "Choice controls must retain option order and normalize values to strings",
  );
  assertJsonEqual(
    select.children.map((option) => option.textContent),
    ["alpha", "Beta label", "3"],
    "Choice controls must use structured labels and value fallbacks",
  );
  assert(
    select.children[1].selected === true
      && select.children[1].disabled === true
      && select.children[1].title === "Beta title",
    "Structured choice metadata and the matching selected option must be preserved",
  );
  assert(
    select.children[0].selected === false
      && select.children[0].disabled === false
      && select.children[0].title === "",
    "Plain choice options must retain their native defaults",
  );
  const strictSelect = aioCreateSelectInput([1], 1);
  assert(
    strictSelect.children[0].value === "1" && strictSelect.children[0].selected === false,
    "Choice selection must retain the existing strict string comparison contract",
  );
  const stringSelect = aioCreateSelectInput([1], "1");
  assert(
    stringSelect.children[0].selected === true,
    "A string choice value must select the matching normalized option",
  );

  assert(
    aioNodeInputDefault(["INT", { default: 0 }], 99) === 0,
    "Node input defaults must preserve an own default property, including zero",
  );
  const inheritedOptions = Object.create({ default: "inherited" });
  assert(
    aioNodeInputDefault(["STRING", inheritedOptions], "fallback") === "fallback",
    "Node input defaults must ignore inherited default properties",
  );
  assert(
    aioNodeInputDefault(null, "fallback") === "fallback",
    "Invalid node specs must use the supplied fallback",
  );

  const choiceControl = aioNodeInputControlForSpec([
    ["first", "second"],
    { default: "second" },
  ], null);
  assert(
    choiceControl.tagName === "SELECT"
      && choiceControl.children[1].selected === true,
    "Choice node specs must build a select using their default value",
  );
  const booleanControl = aioNodeInputControlForSpec(["BOOLEAN", { default: true }]);
  assert(
    booleanControl.type === "checkbox" && booleanControl.checked === true,
    "BOOLEAN node specs must build checkbox controls",
  );
  const intControl = aioNodeInputControlForSpec(["int", { default: 7 }], 0);
  assert(
    intControl.type === "number" && intControl.step === "1" && intControl.value === "0",
    "INT node specs must build integer controls and preserve an explicit zero",
  );
  const floatControl = aioNodeInputControlForSpec(["FLOAT", { default: 1.5 }]);
  assert(
    floatControl.type === "number"
      && floatControl.step === "0.01"
      && floatControl.value === "1.5",
    "FLOAT node specs must build decimal controls",
  );
  const stringControl = aioNodeInputControlForSpec(["STRING", { default: "fallback" }], "");
  assert(
    stringControl.type === "text" && stringControl.value === "",
    "STRING node specs must build text controls and preserve an explicit empty string",
  );
  assert(
    aioNodeInputControlForSpec(["IMAGE"], "value") === null
      && aioNodeInputControlForSpec(null, "value") === null,
    "Unsupported and invalid node specs must not create controls",
  );

  assert(
    aioValueFromNodeInputControl(null) === null,
    "Missing controls must extract as null",
  );
  checked.checked = true;
  assert(
    aioValueFromNodeInputControl(checked) === true,
    "Checkbox controls must extract boolean values",
  );
  preciseNumber.value = "12.5";
  assert(
    aioValueFromNodeInputControl(preciseNumber) === 12.5,
    "Number controls must extract numeric values",
  );
  preciseNumber.value = "";
  assert(
    aioValueFromNodeInputControl(preciseNumber) === 0,
    "Empty number controls must retain the existing zero fallback",
  );
  text.value = "plain text";
  assert(
    aioValueFromNodeInputControl(text) === "plain text",
    "Text controls must extract their string value",
  );
} finally {
  if (hadDocument) {
    globalThis.document = previousDocument;
  } else {
    delete globalThis.document;
  }
}

console.log("AiO DOM controls core smoke passed.");
