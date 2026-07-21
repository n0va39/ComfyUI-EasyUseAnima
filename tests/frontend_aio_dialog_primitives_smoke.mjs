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

class FakeClassList {
  constructor(owner) {
    this.owner = owner;
  }

  add(...tokens) {
    const classes = new Set(String(this.owner.className || "").split(/\s+/).filter(Boolean));
    for (const token of tokens) {
      classes.add(token);
    }
    this.owner.className = [...classes].join(" ");
  }

  contains(token) {
    return String(this.owner.className || "").split(/\s+/).includes(token);
  }
}

class FakeElement {
  constructor(tagName) {
    this.tagName = String(tagName).toUpperCase();
    this.type = "";
    this.className = "";
    this.textContent = "";
    this.title = "";
    this.children = [];
    this.listeners = new Map();
    this.removed = false;
    this.isConnected = true;
    this.classList = new FakeClassList(this);
  }

  append(...children) {
    this.children.push(...children);
  }

  addEventListener(type, listener) {
    const listeners = this.listeners.get(type) || [];
    listeners.push(listener);
    this.listeners.set(type, listeners);
  }

  dispatch(type, target = this) {
    for (const listener of this.listeners.get(type) || []) {
      listener({ target });
    }
  }

  remove() {
    this.removed = true;
    this.isConnected = false;
  }
}

const dialogModule = await import(dataModule("../web/js/aio/dialog_primitives.js"));
assertJsonEqual(
  Object.keys(dialogModule),
  ["aioCreateDialogPrimitives"],
  "AiO dialog primitives must expose only their factory contract",
);

const body = new FakeElement("body");
const fakeDocument = {
  body,
  createElement(tagName) {
    return new FakeElement(tagName);
  },
};
const tooltipCalls = [];
const tooltipTextCalls = [];
const presentationCalls = [];
let ensureStyleCalls = 0;
const primitives = dialogModule.aioCreateDialogPrimitives({
  document: fakeDocument,
  ensureStyle() {
    ensureStyleCalls += 1;
  },
  staticText(value) {
    return `static:${value}`;
  },
  text(key) {
    return `text:${key}`;
  },
  resolveFieldPresentation(label, tooltipKey) {
    presentationCalls.push([label, tooltipKey]);
    const displayLabel = `label:${label}`;
    const tooltipText = tooltipKey
      ? `text:${tooltipKey}`
      : label === "Mapped"
        ? "text:tip.mapped"
        : `format:tip.fieldGeneric:${displayLabel}`;
    return { displayLabel, tooltipText };
  },
  applyTooltip(element, key) {
    tooltipCalls.push([element, key]);
  },
  applyTooltipText(element, value) {
    tooltipTextCalls.push([element, value]);
  },
});

assertJsonEqual(
  Object.keys(primitives),
  ["createDialog", "createNodeField", "field"],
  "AiO dialog primitive factory must expose only the three UI builders",
);
assert(Object.isFrozen(primitives), "AiO dialog primitive contract must be immutable");
assert(ensureStyleCalls === 0, "Creating dialog primitives must not install styles eagerly");

const textControl = new FakeElement("input");
textControl.type = "text";
const nodeField = primitives.createNodeField("Node label", textControl, "wide", "tip.node");
assert(
  nodeField.className === "easyuse-anima-aio-node-field wide",
  "Node fields must retain their base and custom classes",
);
assert(
  nodeField.children[0].tagName === "LABEL"
    && nodeField.children[0].textContent === "Node label"
    && nodeField.children[1] === textControl,
  "Non-checkbox node fields must keep label/control order and text",
);
assertJsonEqual(
  tooltipCalls.map(([, key]) => key),
  ["tip.node", "tip.node", "tip.node"],
  "Node fields must apply the tooltip key to wrapper, label, and control",
);

const checkboxControl = new FakeElement("input");
checkboxControl.type = "checkbox";
const checkboxNodeField = primitives.createNodeField("Enabled", checkboxControl);
assert(
  checkboxNodeField.classList.contains("checkbox")
    && checkboxNodeField.children.length === 1,
  "Checkbox node fields must retain their checkbox layout class and wrapper shape",
);
assert(
  checkboxNodeField.children[0].children[0].textContent === "Enabled"
    && checkboxNodeField.children[0].children[1] === checkboxControl,
  "Checkbox node fields must keep text and native control inside the label",
);

const genericSection = new FakeElement("section");
const genericControl = new FakeElement("input");
const returnedGenericControl = primitives.field(genericSection, "Generic", genericControl);
assert(returnedGenericControl === genericControl, "Dialog fields must return their control");
assert(
  genericSection.children[0].children[0].textContent === "label:Generic"
    && genericSection.children[0].children[1] === genericControl,
  "Dialog fields must append translated label/control rows to their section",
);
assertJsonEqual(
  presentationCalls,
  [["Generic", ""]],
  "Dialog fields must delegate label and tooltip policy to the injected presentation resolver",
);
assertJsonEqual(
  tooltipTextCalls.slice(-3).map(([, value]) => value),
  [
    "format:tip.fieldGeneric:label:Generic",
    "format:tip.fieldGeneric:label:Generic",
    "format:tip.fieldGeneric:label:Generic",
  ],
  "Dialog fields must apply generic tooltip text to row, label, and control",
);

const mappedSection = new FakeElement("section");
const mappedControl = new FakeElement("input");
mappedControl.type = "checkbox";
primitives.field(mappedSection, "Mapped", mappedControl);
assert(
  mappedSection.children[0].classList.contains("checkbox")
    && mappedSection.children[0].children[0].children[0].textContent === "label:Mapped"
    && mappedSection.children[0].children[0].children[1] === mappedControl,
  "Mapped checkbox fields must retain the checkbox row structure",
);
assertJsonEqual(
  tooltipTextCalls.slice(-3).map(([, value]) => value),
  ["text:tip.mapped", "text:tip.mapped", "text:tip.mapped"],
  "Dialog fields must resolve mapped tooltip keys through the text adapter",
);

const explicitSection = new FakeElement("section");
primitives.field(explicitSection, "Mapped", new FakeElement("input"), "tip.explicit");
assertJsonEqual(
  tooltipTextCalls.slice(-3).map(([, value]) => value),
  ["text:tip.explicit", "text:tip.explicit", "text:tip.explicit"],
  "An explicit dialog tooltip key must take precedence over the field mapping",
);

const firstDialog = primitives.createDialog("Title", "Subtitle");
assert(ensureStyleCalls === 1, "Dialog creation must ensure the AiO stylesheet exactly once");
assert(
  firstDialog.backdrop.className === "easyuse-anima-aio-backdrop"
    && firstDialog.body.className === "easyuse-anima-aio-body"
    && firstDialog.actions.className === "easyuse-anima-aio-actions",
  "Dialog creation must retain its public backdrop/body/actions classes",
);
assert(body.children[0] === firstDialog.backdrop, "Dialogs must append their backdrop to document.body");
const firstDialogElement = firstDialog.backdrop.children[0];
const firstHeader = firstDialogElement.children[0];
const firstTitleBox = firstHeader.children[0];
const firstClose = firstHeader.children[1];
assert(
  firstTitleBox.children[0].textContent === "static:Title"
    && firstTitleBox.children[1].textContent === "static:Subtitle"
    && firstClose.textContent === "text:button.close",
  "Dialog title, subtitle, and close label must use their injected text adapters",
);
firstDialog.backdrop.dispatch("pointerdown", firstDialogElement);
assert(!firstDialog.backdrop.removed, "Pointerdown inside a dialog must keep the backdrop connected");
firstDialog.backdrop.dispatch("pointerdown");
assert(firstDialog.backdrop.removed, "Pointerdown on the backdrop must close the dialog");

let secondDialogCloseCount = 0;
const secondDialog = primitives.createDialog("Second", "Dialog", () => {
  secondDialogCloseCount += 1;
});
assert(ensureStyleCalls === 2, "Every dialog open must ensure the AiO stylesheet");
assert(
  secondDialog.dialog === secondDialog.backdrop.children[0]
    && typeof secondDialog.close === "function",
  "Dialog creation must expose the dialog element and an imperative close contract",
);
const secondClose = secondDialog.backdrop.children[0].children[0].children[1];
secondClose.dispatch("click");
assert(secondDialog.backdrop.removed, "The dialog close button must remove its backdrop");
secondDialog.close();
assert(
  secondDialogCloseCount === 1,
  "Dialog close callbacks and removals must be idempotent",
);

console.log("AiO dialog primitives smoke passed.");
