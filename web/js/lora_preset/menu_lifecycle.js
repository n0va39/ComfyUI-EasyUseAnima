// @ts-check

/**
 * @typedef {object} LoraPresetMenuDependencies
 * @property {Document} document
 * @property {Window} window
 * @property {typeof MutationObserver} MutationObserver
 * @property {(tagName: string, options?: Record<string, any>) => any} createElement
 * @property {(value: unknown) => string} validComboEntryText
 * @property {{showPreview: (name: string, event?: any) => void, hidePreview: () => void}} previewLifecycle
 * @property {(menu: any, clientPoint: any) => void} positionMenu
 * @property {(key: string) => string} text
 * @property {() => string} getMenuMode
 * @property {() => any} getCurrentNode
 * @property {string} nodeType
 * @property {number} previewSize
 */

/**
 * Own the LoRA context-menu DOM lifecycle while the entry module keeps menu
 * creation and selection callbacks. This preserves the existing order:
 * prepare node state, create the LiteGraph menu, normalize its DOM on the
 * observer frame, then release the active node.
 *
 * @param {LoraPresetMenuDependencies} dependencies
 */
export function createLoraPresetMenuLifecycle(dependencies) {
  const {
    document,
    window,
    MutationObserver,
    createElement,
    validComboEntryText,
    previewLifecycle,
    positionMenu,
    text,
    getMenuMode,
    getCurrentNode,
    nodeType,
    previewSize,
  } = dependencies;
  let activeLoraMenuNode = null;

  function normalizeSearchText(value) {
    return String(value || "")
      .replace(/[\\/_-]+/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  function escapeHtml(value) {
    return String(value || "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "\"": "&quot;",
      "'": "&#39;",
    })[char]);
  }

  function createMenuItems(values) {
    return (values || [])
      .map((value) => validComboEntryText(value))
      .filter(Boolean)
      .map((name) => ({
        content: escapeHtml(name),
        value: name,
      }));
  }

  function activateMenu(node, clientPoint, menuItems) {
    node.__easyuseAnimaOpeningLoraMenu = true;
    node.__easyuseAnimaLoraMenuPoint = clientPoint;
    node.__easyuseAnimaLoraMenuValues = menuItems.map((item) => item.value);
    activeLoraMenuNode = node;
  }

  function ensureLoraMenuSearch(menu, node) {
    if (!menu || menu.__easyuseAnimaSearchReady) {
      return;
    }
    menu.__easyuseAnimaSearchReady = true;
    const existingInput = menu.querySelector(".comfy-context-menu-filter, input[type='search'], input");
    if (existingInput) {
      const applyExistingSearch = () => {
        applyLoraMenuSearch(menu, existingInput.value);
        positionMenu(menu, node?.__easyuseAnimaLoraMenuPoint);
      };
      existingInput.addEventListener("input", applyExistingSearch);
      window.requestAnimationFrame(() => {
        existingInput.focus();
        applyExistingSearch();
      });
      return;
    }
    const input = createElement("input", {
      className: "easyuse-anima-lora-search",
    });
    input.type = "search";
    input.placeholder = text("lora.search");
    input.autocomplete = "off";
    input.spellcheck = false;
    const stop = (event) => event.stopPropagation();
    for (const eventName of ["pointerdown", "mousedown", "mouseup", "click", "dblclick", "keydown"]) {
      input.addEventListener(eventName, stop);
    }
    input.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        input.value = "";
        applyLoraMenuSearch(menu, "");
        event.preventDefault();
        event.stopPropagation();
      }
    });
    input.addEventListener("input", () => {
      applyLoraMenuSearch(menu, input.value);
      positionMenu(menu, node?.__easyuseAnimaLoraMenuPoint);
    });
    const firstDirectEntry = Array.from(menu.children).find((child) => child.classList?.contains("litemenu-entry"));
    menu.insertBefore(input, firstDirectEntry || menu.firstChild);
    window.requestAnimationFrame(() => {
      input.focus();
      positionMenu(menu, node?.__easyuseAnimaLoraMenuPoint);
    });
  }

  function applyLoraMenuSearch(menu, rawQuery) {
    const query = normalizeSearchText(rawQuery);
    const hasQuery = !!query;
    const entries = Array.from(menu.querySelectorAll(".litemenu-entry:not(.easyuse-anima-combo-folder)"));
    for (const entry of entries) {
      const textValue = entry.getAttribute("data-search") || normalizeSearchText(entry.getAttribute("data-value") || entry.textContent);
      entry.style.display = !hasQuery || textValue.includes(query) ? "" : "none";
    }
    for (const folder of menu.querySelectorAll(".easyuse-anima-combo-folder")) {
      folder.style.display = hasQuery ? "none" : "";
    }
    for (const container of menu.querySelectorAll(".easyuse-anima-combo-folder-contents")) {
      container.style.display = hasQuery ? "block" : (container.__easyuseAnimaOpen ? "block" : "none");
    }
  }

  function loraMenuElementValue(item, fallbackValue) {
    const candidates = [
      item?.getAttribute?.("data-value"),
      item?.dataset?.value,
      item?.value,
      item?.__value,
      fallbackValue,
      item?.textContent,
    ];
    for (const candidate of candidates) {
      const textValue = validComboEntryText(candidate);
      if (textValue) {
        return textValue;
      }
    }
    return "";
  }

  function addLoraMenuEntryHandlers(item, value) {
    if (item.__easyuseAnimaPreviewValue === value) {
      return;
    }
    item.__easyuseAnimaPreviewValue = value;
    item.addEventListener("mouseover", (event) => previewLifecycle.showPreview(value, event), { passive: true });
    item.addEventListener("mousemove", (event) => previewLifecycle.showPreview(value, event), { passive: true });
    item.addEventListener("mouseout", previewLifecycle.hidePreview, { passive: true });
  }

  function normalizeLoraMenuEntries(menu, node, options = {}) {
    const items = Array.from(menu.querySelectorAll(".litemenu-entry"));
    const fallbackValues = node?.__easyuseAnimaLoraMenuValues || [];
    const splitBy = /\/|\\/;
    const entries = [];

    items.forEach((item, index) => {
      const value = loraMenuElementValue(item, fallbackValues[index]);
      if (!value) {
        item.textContent = "";
        item.style.display = "none";
        return;
      }
      item.setAttribute("data-value", value);
      item.setAttribute("title", value);
      const parts = value.split(splitBy).filter(Boolean);
      item.setAttribute("data-search", normalizeSearchText([value, parts.join(" ")].join(" ")));
      item.textContent = options.splitDisplay ? (parts[parts.length - 1] || value) : value;
      if (options.splitDisplay && parts.length > 1) {
        item.prepend(createElement("span", {
          className: "easyuse-anima-combo-prefix",
          textContent: `${parts.slice(0, -1).join("/")}/`,
        }));
      }
      addLoraMenuEntryHandlers(item, value);
      entries.push({ item, value, parts });
    });

    return entries;
  }

  function updateLoraMenuList(menu, node) {
    if (!menu || menu.__easyuseAnimaListReady) {
      return;
    }
    menu.__easyuseAnimaListReady = true;
    normalizeLoraMenuEntries(menu, node, { splitDisplay: false });
    ensureLoraMenuSearch(menu, node);
    positionMenu(menu, node?.__easyuseAnimaLoraMenuPoint);
  }

  function updateLoraMenuTree(menu, node) {
    if (!menu || menu.__easyuseAnimaTreeReady) {
      return;
    }
    menu.__easyuseAnimaTreeReady = true;
    const entries = normalizeLoraMenuEntries(menu, node, { splitDisplay: true });
    if (!entries.length) {
      return;
    }
    const folderMap = new Map();
    const itemsSymbol = Symbol("items");

    for (const { item, parts } of entries) {
      if (parts.length <= 1) {
        continue;
      }
      item.remove();
      let level = folderMap;
      for (const folder of parts.slice(0, -1)) {
        if (!level.has(folder)) {
          level.set(folder, new Map());
        }
        level = level.get(folder);
      }
      if (!level.has(itemsSymbol)) {
        level.set(itemsSymbol, []);
      }
      level.get(itemsSymbol).push(item);
    }

    const parent = entries[0]?.item?.parentElement || menu;
    const insertFolders = (target, map, depth = 0) => {
      for (const [folder, content] of map.entries()) {
        if (folder === itemsSymbol) {
          continue;
        }
        const folderEl = createElement("div", {
          className: "litemenu-entry easyuse-anima-combo-folder",
          innerHTML: `<span class="easyuse-anima-combo-folder-arrow">▶</span> ${folder}`,
          style: { paddingLeft: `${depth * 10 + 5}px` },
        });
        const childContainer = createElement("div", {
          className: "easyuse-anima-combo-folder-contents",
          style: { display: "none" },
        });
        for (const child of content.get(itemsSymbol) || []) {
          child.style.paddingLeft = `${(depth + 1) * 10 + 14}px`;
          childContainer.appendChild(child);
        }
        insertFolders(childContainer, content, depth + 1);
        folderEl.addEventListener("click", (event) => {
          event.stopPropagation();
          const open = childContainer.style.display === "none";
          childContainer.__easyuseAnimaOpen = open;
          childContainer.style.display = open ? "block" : "none";
          folderEl.querySelector(".easyuse-anima-combo-folder-arrow").textContent = open ? "▼" : "▶";
        });
        target.appendChild(folderEl);
        target.appendChild(childContainer);
      }
    };

    insertFolders(parent, folderMap);
    ensureLoraMenuSearch(menu, node);
    positionMenu(menu, node?.__easyuseAnimaLoraMenuPoint);
  }

  function updateLoraMenu(menu, node) {
    if (getMenuMode() === "list") {
      updateLoraMenuList(menu, node);
      return;
    }
    updateLoraMenuTree(menu, node);
  }

  function install() {
    document.head.appendChild(createElement("style", {
      textContent: `
        .easyuse-anima-lora-preview {
          position: fixed;
          width: ${previewSize}px;
          height: ${previewSize}px;
          object-fit: contain;
          background: rgba(20, 20, 22, 0.96);
          border: 1px solid rgba(180, 180, 185, 0.45);
          z-index: 10000;
          pointer-events: none;
          display: none;
        }
        .easyuse-anima-lora-menu .easyuse-anima-lora-search {
          box-sizing: border-box;
          width: calc(100% - 10px);
          margin: 4px 5px 6px;
          padding: 4px 6px;
          color: var(--input-text, #ddd);
          background: var(--comfy-input-bg, #222);
          border: 1px solid rgba(180, 180, 185, 0.45);
          border-radius: 3px;
          outline: none;
        }
        .easyuse-anima-lora-menu .easyuse-anima-combo-folder {
          opacity: 0.72;
        }
        .easyuse-anima-lora-menu .easyuse-anima-combo-folder-arrow {
          display: inline-block;
          width: 15px;
        }
        .easyuse-anima-lora-menu .easyuse-anima-combo-folder:hover {
          background-color: rgba(255, 255, 255, 0.1);
        }
        .easyuse-anima-lora-menu .easyuse-anima-combo-prefix {
          display: none;
        }
        .easyuse-anima-lora-menu:has(input:not(:placeholder-shown)) .easyuse-anima-combo-folder-contents {
          display: block !important;
        }
        .easyuse-anima-lora-menu:has(input:not(:placeholder-shown)) .easyuse-anima-combo-folder {
          display: none;
        }
        .easyuse-anima-lora-menu:has(input:not(:placeholder-shown)) .easyuse-anima-combo-prefix {
          display: inline;
        }
        .easyuse-anima-lora-menu:has(input:not(:placeholder-shown)) .litemenu-entry {
          padding-left: 2px !important;
        }
      `,
    }));

    const observer = new MutationObserver((mutations) => {
      const node = activeLoraMenuNode || getCurrentNode();
      if (!node || node.comfyClass !== nodeType) {
        return;
      }
      for (const mutation of mutations) {
        for (const removed of mutation.removedNodes) {
          const removedElement = /** @type {Element} */ (removed);
          if (removedElement.classList?.contains("litecontextmenu")) {
            previewLifecycle.hidePreview();
          }
        }
        for (const added of mutation.addedNodes) {
          const addedElement = /** @type {Element} */ (added);
          if (!addedElement.classList?.contains("litecontextmenu") || !node.__easyuseAnimaOpeningLoraMenu) {
            continue;
          }
          window.requestAnimationFrame(() => {
            updateLoraMenu(addedElement, node);
            node.__easyuseAnimaOpeningLoraMenu = false;
            activeLoraMenuNode = null;
          });
        }
      }
    });
    observer.observe(document.body, { childList: true, subtree: false });
  }

  return {
    activateMenu,
    createMenuItems,
    install,
  };
}
