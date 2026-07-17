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
    this.priorities = new Map();
  }

  setProperty(name, value, priority = "") {
    const key = String(name);
    const text = String(value);
    this.values.set(key, text);
    this.priorities.set(key, String(priority || ""));
    this[key] = text;
  }

  getPropertyValue(name) {
    return this.values.get(String(name)) ?? this[name] ?? "";
  }

  getPropertyPriority(name) {
    return this.priorities.get(String(name)) ?? "";
  }

  removeProperty(name) {
    const key = String(name);
    const previous = this.getPropertyValue(key);
    this.values.delete(key);
    this.priorities.delete(key);
    delete this[key];
    return previous;
  }
}

function listenerCapture(options = false) {
  return typeof options === "boolean" ? options : !!options?.capture;
}

function matchesSelector(element, selector) {
  return String(selector).split(",").some((candidate) => {
    const expected = candidate.trim();
    if (!expected) {
      return false;
    }
    const attributes = [];
    const withoutAttributes = expected.replace(
      /\[([A-Za-z0-9_:-]+)(?:(\$?=)"([^"]*)")?\]/g,
      (_match, name, operator, value) => {
        attributes.push({ name, operator: operator || "", value: value ?? "" });
        return "";
      },
    );
    if (withoutAttributes.includes("[") || withoutAttributes.includes("]")) {
      return false;
    }
    const tagMatch = withoutAttributes.match(/^[A-Za-z][A-Za-z0-9-]*/);
    const tagName = tagMatch?.[0] || "";
    if (tagName && element.tagName !== tagName.toUpperCase()) {
      return false;
    }
    const classNames = [...withoutAttributes.matchAll(/\.([A-Za-z0-9_-]+)/g)]
      .map((match) => match[1]);
    if (classNames.some((name) => !element.classList.contains(name))) {
      return false;
    }
    const remainder = withoutAttributes
      .slice(tagName.length)
      .replace(/\.[A-Za-z0-9_-]+/g, "")
      .trim();
    if (remainder) {
      return false;
    }
    return attributes.every(({ name, operator, value }) => {
      const actual = element.getAttribute(name);
      if (actual == null) {
        return false;
      }
      if (!operator) {
        return true;
      }
      return operator === "$=" ? actual.endsWith(value) : actual === value;
    });
  });
}

class FakeElement {
  constructor(tagName, ownerDocument = null) {
    this.tagName = String(tagName).toUpperCase();
    this.ownerDocument = ownerDocument;
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
    this.scrollTop = 0;
    this.scrollLeft = 0;
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
      child.detachActiveElement();
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

  addEventListener(type, handler, options = false) {
    const entries = this.listeners.get(type) || [];
    const capture = listenerCapture(options);
    if (!entries.some((entry) => entry.handler === handler && entry.capture === capture)) {
      entries.push({ handler, capture });
    }
    this.listeners.set(type, entries);
  }

  removeEventListener(type, handler, options = false) {
    const entries = this.listeners.get(type) || [];
    const capture = listenerCapture(options);
    this.listeners.set(
      type,
      entries.filter((entry) => entry.handler !== handler || entry.capture !== capture),
    );
  }

  listenerCount(type, options) {
    const entries = this.listeners.get(type) || [];
    if (arguments.length < 2) {
      return entries.length;
    }
    const capture = listenerCapture(options);
    return entries.filter((entry) => entry.capture === capture).length;
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
    for (const entry of this.listeners.get(type) || []) {
      entry.handler(nextEvent);
    }
    return nextEvent;
  }

  querySelector(selector) {
    return descendants(this).find((element) => matchesSelector(element, selector)) ?? null;
  }

  querySelectorAll(selector) {
    return descendants(this).filter((element) => matchesSelector(element, selector));
  }

  matches(selector) {
    return matchesSelector(this, selector);
  }

  contains(element) {
    return element === this || descendants(this).includes(element);
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
    const activeElement = this.ownerDocument?.activeElement;
    if (activeElement && activeElement !== this) {
      activeElement.focused = false;
    }
    if (this.ownerDocument) {
      this.ownerDocument.activeElement = this;
    }
    this.focused = true;
  }

  blur() {
    this.focused = false;
    if (this.ownerDocument?.activeElement === this) {
      this.ownerDocument.activeElement = this.ownerDocument.body;
    }
    this.emit("blur");
  }

  detachActiveElement() {
    const document = this.ownerDocument;
    const activeElement = document?.activeElement;
    if (activeElement && this.contains(activeElement)) {
      activeElement.focused = false;
      document.activeElement = document.body;
    }
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
    this.detachActiveElement();
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
    this.body = new FakeElement("body", this);
    this.activeElement = this.body;
    this.createdElements = [];
    this.listeners = new Map();
  }

  createElement(tagName) {
    const element = new FakeElement(tagName, this);
    this.createdElements.push(element);
    return element;
  }

  createTextNode(value) {
    const element = new FakeElement("#text", this);
    element.textContent = String(value);
    this.createdElements.push(element);
    return element;
  }

  querySelectorAll(selector) {
    return this.body.querySelectorAll(selector);
  }

  addEventListener(type, handler, options = false) {
    const entries = this.listeners.get(type) || [];
    const capture = listenerCapture(options);
    if (!entries.some((entry) => entry.handler === handler && entry.capture === capture)) {
      entries.push({ handler, capture });
    }
    this.listeners.set(type, entries);
  }

  removeEventListener(type, handler, options = false) {
    const entries = this.listeners.get(type) || [];
    const capture = listenerCapture(options);
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

  listenerCount(type, options) {
    const entries = this.listeners.get(type) || [];
    if (arguments.length < 2) {
      return entries.length;
    }
    const capture = listenerCapture(options);
    return entries.filter((entry) => entry.capture === capture).length;
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
