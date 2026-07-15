class FakeElement {
  constructor(tagName) {
    this.tagName = String(tagName).toUpperCase();
    this.children = [];
    this.parentElement = null;
    this.style = { cssText: "", background: "", borderColor: "" };
    this.listeners = new Map();
    this.attributes = new Map();
    this.className = "";
    this.textContent = "";
    this.title = "";
    this.type = "";
    this.inputMode = "";
    this.value = "";
    this.placeholder = "";
    this.rows = 0;
    this.spellcheck = true;
    this.disabled = false;
    this.selected = false;
    this.focused = false;
    this.removed = false;
    this.onclick = null;
  }

  append(...children) {
    for (const child of children) {
      child.parentElement = this;
      this.children.push(child);
      if (this.tagName === "SELECT" && child.tagName === "OPTION" && child.selected) {
        this.value = child.value;
      }
    }
  }

  prepend(...children) {
    for (const child of [...children].reverse()) {
      child.parentElement = this;
      this.children.unshift(child);
    }
  }

  replaceChildren(...children) {
    for (const child of this.children) {
      child.parentElement = null;
    }
    this.children = [];
    this.append(...children);
  }

  get lastElementChild() {
    return this.children.at(-1) ?? null;
  }

  setAttribute(name, value) {
    this.attributes.set(name, String(value));
  }

  getAttribute(name) {
    return this.attributes.get(name) ?? null;
  }

  addEventListener(type, handler) {
    const handlers = this.listeners.get(type) || [];
    handlers.push(handler);
    this.listeners.set(type, handlers);
  }

  emit(type, event = {}) {
    const nextEvent = {
      target: this,
      defaultPrevented: false,
      propagationStopped: false,
      preventDefault() {
        this.defaultPrevented = true;
      },
      stopPropagation() {
        this.propagationStopped = true;
      },
      ...event,
    };
    for (const handler of this.listeners.get(type) || []) {
      handler(nextEvent);
    }
    return nextEvent;
  }

  querySelector(selector) {
    const expectedTag = String(selector).toUpperCase();
    return descendants(this).find((element) => element.tagName === expectedTag) ?? null;
  }

  focus() {
    this.focused = true;
  }

  blur() {
    this.focused = false;
    this.emit("blur");
  }

  remove() {
    if (this.parentElement) {
      const index = this.parentElement.children.indexOf(this);
      if (index >= 0) {
        this.parentElement.children.splice(index, 1);
      }
    }
    this.parentElement = null;
    this.removed = true;
  }
}

class FakeDocument {
  constructor() {
    this.body = new FakeElement("body");
    this.createdElements = [];
    this.listeners = new Map();
  }

  createElement(tagName) {
    const element = new FakeElement(tagName);
    this.createdElements.push(element);
    return element;
  }

  addEventListener(type, handler, capture = false) {
    const entries = this.listeners.get(type) || [];
    entries.push({ handler, capture });
    this.listeners.set(type, entries);
  }

  removeEventListener(type, handler, capture = false) {
    const entries = this.listeners.get(type) || [];
    this.listeners.set(
      type,
      entries.filter((entry) => entry.handler !== handler || entry.capture !== capture),
    );
  }

  dispatchKey(key) {
    for (const entry of [...(this.listeners.get("keydown") || [])]) {
      entry.handler({ key });
    }
  }

  listenerCount(type) {
    return (this.listeners.get(type) || []).length;
  }
}

export function createFakeDocument() {
  return new FakeDocument();
}

export function descendants(root) {
  const values = [];
  for (const child of root.children) {
    values.push(child, ...descendants(child));
  }
  return values;
}
