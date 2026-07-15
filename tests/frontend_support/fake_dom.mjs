class FakeClassList {
  constructor(element) {
    this.element = element;
  }

  values() {
    return new Set(String(this.element.className || "").split(/\s+/).filter(Boolean));
  }

  write(values) {
    this.element.className = [...values].join(" ");
  }

  add(...names) {
    const values = this.values();
    for (const name of names) {
      values.add(String(name));
    }
    this.write(values);
  }

  remove(...names) {
    const values = this.values();
    for (const name of names) {
      values.delete(String(name));
    }
    this.write(values);
  }

  toggle(name, force) {
    const values = this.values();
    const text = String(name);
    const enabled = force == null ? !values.has(text) : !!force;
    if (enabled) {
      values.add(text);
    } else {
      values.delete(text);
    }
    this.write(values);
    return enabled;
  }

  contains(name) {
    return this.values().has(String(name));
  }
}

class FakeStyle {
  constructor() {
    this.cssText = "";
    this.background = "";
    this.borderColor = "";
    this.values = new Map();
  }

  setProperty(name, value) {
    const text = String(value);
    this.values.set(String(name), text);
    this[name] = text;
  }

  getPropertyValue(name) {
    return this.values.get(String(name)) ?? this[name] ?? "";
  }

  removeProperty(name) {
    const key = String(name);
    const previous = this.getPropertyValue(key);
    this.values.delete(key);
    delete this[key];
    return previous;
  }
}

function matchesSelector(element, selector) {
  return String(selector).split(",").some((candidate) => {
    const expected = candidate.trim();
    if (!expected) {
      return false;
    }
    if (expected.startsWith(".")) {
      return element.classList.contains(expected.slice(1));
    }
    const attribute = expected.match(/^\[([^=\]]+)(?:="([^"]*)")?\]$/);
    if (attribute) {
      const actual = element.getAttribute(attribute[1]);
      return actual != null && (attribute[2] == null || actual === attribute[2]);
    }
    return element.tagName === expected.toUpperCase();
  });
}

class FakeElement {
  constructor(tagName) {
    this.tagName = String(tagName).toUpperCase();
    this.children = [];
    this.parentElement = null;
    this.style = new FakeStyle();
    this.listeners = new Map();
    this.attributes = new Map();
    this.className = "";
    this.classList = new FakeClassList(this);
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
    this.checked = false;
    this.hidden = false;
    this.focused = false;
    this.removed = false;
    this.onclick = null;
    this.scrollIntoViewCalls = [];
    this.boundingClientRect = { left: 0, top: 0, width: 100, height: 20 };
    this.pointerCaptures = new Set();
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
    return descendants(this).find((element) => matchesSelector(element, selector)) ?? null;
  }

  querySelectorAll(selector) {
    return descendants(this).filter((element) => matchesSelector(element, selector));
  }

  closest(selector) {
    let current = this;
    while (current) {
      if (matchesSelector(current, selector)) {
        return current;
      }
      current = current.parentElement;
    }
    return null;
  }

  focus() {
    this.focused = true;
  }

  blur() {
    this.focused = false;
    this.emit("blur");
  }

  getBoundingClientRect() {
    return { ...this.boundingClientRect };
  }

  scrollIntoView(options) {
    this.scrollIntoViewCalls.push(options);
  }

  setPointerCapture(pointerId) {
    this.pointerCaptures.add(pointerId);
  }

  releasePointerCapture(pointerId) {
    this.pointerCaptures.delete(pointerId);
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

  createTextNode(value) {
    const element = new FakeElement("#text");
    element.textContent = String(value);
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
