// @ts-check

const LORA_PRESET_MENU_LIFECYCLE_OWNER = Symbol.for(
  "easyuse-anima.lora-preset.menu-lifecycle-owner",
);

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
  const ownerHost = /** @type {any} */ (document);
  let activeLoraMenuNode = null;
  let installed = false;
  let installRevision = 0;
  let observer = /** @type {MutationObserver | null} */ (null);
  let styleElement = /** @type {HTMLElement | null} */ (null);

  function ownsRevision(revision) {
    return installed
      && revision === installRevision
      && ownerHost[LORA_PRESET_MENU_LIFECYCLE_OWNER] === dispose;
  }

  function ownsMenu(menu, revision) {
    return ownsRevision(revision)
      && menu?.__easyuseAnimaLoraMenuOwner === dispose
      && menu?.__easyuseAnimaLoraMenuRevision === revision;
  }

  function ownsRemovedMenu(menu) {
    if (!menu?.classList?.contains("easyuse-anima-lora-menu")) {
      return false;
    }
    const menuOwner = menu.__easyuseAnimaLoraMenuOwner;
    return !menuOwner || (
      menuOwner === dispose
      && menu.__easyuseAnimaLoraMenuRevision === installRevision
    );
  }

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

  function ensureLoraMenuSearch(menu, node, revision) {
    if (!menu || menu.__easyuseAnimaSearchReady) {
      return;
    }
    menu.__easyuseAnimaSearchReady = true;
    const isLive = () => ownsMenu(menu, revision);
    const existingInput = menu.querySelector(".comfy-context-menu-filter, input[type='search'], input");
    if (existingInput) {
      const applyExistingSearch = () => {
        if (!isLive()) {
          return;
        }
        applyLoraMenuSearch(menu, existingInput.value);
        positionMenu(menu, node?.__easyuseAnimaLoraMenuPoint);
      };
      existingInput.addEventListener("input", applyExistingSearch);
      window.requestAnimationFrame(() => {
        if (!isLive()) {
          return;
        }
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
    const stop = (event) => {
      if (isLive()) {
        event.stopPropagation();
      }
    };
    for (const eventName of ["pointerdown", "mousedown", "mouseup", "click", "dblclick", "keydown"]) {
      input.addEventListener(eventName, stop);
    }
    input.addEventListener("keydown", (event) => {
      if (isLive() && event.key === "Escape") {
        input.value = "";
        applyLoraMenuSearch(menu, "");
        event.preventDefault();
        event.stopPropagation();
      }
    });
    input.addEventListener("input", () => {
      if (!isLive()) {
        return;
      }
      applyLoraMenuSearch(menu, input.value);
      positionMenu(menu, node?.__easyuseAnimaLoraMenuPoint);
    });
    const firstDirectEntry = Array.from(menu.children).find((child) => child.classList?.contains("litemenu-entry"));
    menu.insertBefore(input, firstDirectEntry || menu.firstChild);
    window.requestAnimationFrame(() => {
      if (!isLive()) {
        return;
      }
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

  function addLoraMenuEntryHandlers(item, value, menu, revision) {
    if (
      item.__easyuseAnimaPreviewValue === value
      && item.__easyuseAnimaPreviewOwner === dispose
      && item.__easyuseAnimaPreviewRevision === revision
    ) {
      return;
    }
    item.__easyuseAnimaPreviewValue = value;
    item.__easyuseAnimaPreviewOwner = dispose;
    item.__easyuseAnimaPreviewRevision = revision;
    const showPreview = (event) => {
      if (ownsMenu(menu, revision)) {
        previewLifecycle.showPreview(value, event);
      }
    };
    const hidePreview = () => {
      if (ownsMenu(menu, revision)) {
        previewLifecycle.hidePreview();
      }
    };
    item.addEventListener("mouseover", showPreview, { passive: true });
    item.addEventListener("mousemove", showPreview, { passive: true });
    item.addEventListener("mouseout", hidePreview, { passive: true });
  }

  function normalizeLoraMenuEntries(menu, node, revision, options = {}) {
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
      addLoraMenuEntryHandlers(item, value, menu, revision);
      entries.push({ item, value, parts });
    });

    return entries;
  }

  function updateLoraMenuList(menu, node, revision) {
    if (!menu || menu.__easyuseAnimaListReady) {
      return;
    }
    menu.__easyuseAnimaListReady = true;
    normalizeLoraMenuEntries(menu, node, revision, { splitDisplay: false });
    ensureLoraMenuSearch(menu, node, revision);
    positionMenu(menu, node?.__easyuseAnimaLoraMenuPoint);
  }

  function updateLoraMenuTree(menu, node, revision) {
    if (!menu || menu.__easyuseAnimaTreeReady) {
      return;
    }
    menu.__easyuseAnimaTreeReady = true;
    const entries = normalizeLoraMenuEntries(menu, node, revision, { splitDisplay: true });
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
          style: { paddingLeft: `${depth * 10 + 5}px` },
        });
        folderEl.append(
          createElement("span", {
            className: "easyuse-anima-combo-folder-arrow",
            textContent: "▶",
          }),
          createElement("span", {
            className: "easyuse-anima-combo-folder-label",
            textContent: folder,
          }),
        );
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
          if (!ownsMenu(menu, revision)) {
            return;
          }
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
    ensureLoraMenuSearch(menu, node, revision);
    positionMenu(menu, node?.__easyuseAnimaLoraMenuPoint);
  }

  function updateLoraMenu(menu, node, revision) {
    if (getMenuMode() === "list") {
      updateLoraMenuList(menu, node, revision);
      return;
    }
    updateLoraMenuTree(menu, node, revision);
  }

  function dispose() {
    if (!installed) {
      if (ownerHost[LORA_PRESET_MENU_LIFECYCLE_OWNER] === dispose) {
        delete ownerHost[LORA_PRESET_MENU_LIFECYCLE_OWNER];
      }
      return false;
    }

    installed = false;
    installRevision += 1;
    const currentObserver = observer;
    const currentStyleElement = styleElement;
    observer = null;
    styleElement = null;
    if (activeLoraMenuNode) {
      activeLoraMenuNode.__easyuseAnimaOpeningLoraMenu = false;
    }
    activeLoraMenuNode = null;

    let cleanupFailed = false;
    let firstCleanupError;
    const runCleanup = (callback) => {
      try {
        callback();
      } catch (error) {
        if (!cleanupFailed) {
          cleanupFailed = true;
          firstCleanupError = error;
        }
      }
    };
    if (ownerHost[LORA_PRESET_MENU_LIFECYCLE_OWNER] === dispose) {
      runCleanup(() => {
        delete ownerHost[LORA_PRESET_MENU_LIFECYCLE_OWNER];
      });
    }
    runCleanup(() => currentObserver?.disconnect());
    runCleanup(() => currentStyleElement?.remove());
    runCleanup(() => previewLifecycle.hidePreview());
    if (cleanupFailed) {
      throw firstCleanupError;
    }
    return true;
  }

  function install() {
    if (installed && ownerHost[LORA_PRESET_MENU_LIFECYCLE_OWNER] === dispose) {
      return dispose;
    }

    if (installed) {
      dispose();
    }

    const previousOwner = ownerHost[LORA_PRESET_MENU_LIFECYCLE_OWNER];
    const revision = ++installRevision;
    const nextStyleElement = createElement("style", {
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
        .easyuse-anima-lora-menu .easyuse-anima-combo-folder-label {
          margin-left: 0.25em;
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
    });

    /** @param {MutationRecord[]} mutations */
    const handleMutations = (mutations) => {
      if (!ownsRevision(revision)) {
        return;
      }
      for (const mutation of mutations) {
        for (const removed of mutation.removedNodes) {
          const removedElement = /** @type {Element} */ (removed);
          if (ownsRemovedMenu(removedElement)) {
            previewLifecycle.hidePreview();
          }
        }
      }

      const node = activeLoraMenuNode || getCurrentNode();
      if (!node || node.comfyClass !== nodeType) {
        return;
      }
      for (const mutation of mutations) {
        for (const added of mutation.addedNodes) {
          const addedElement = /** @type {any} */ (added);
          if (
            !addedElement.classList?.contains("litecontextmenu")
            || !addedElement.classList?.contains("easyuse-anima-lora-menu")
            || !node.__easyuseAnimaOpeningLoraMenu
          ) {
            continue;
          }
          addedElement.__easyuseAnimaLoraMenuOwner = dispose;
          addedElement.__easyuseAnimaLoraMenuRevision = revision;
          window.requestAnimationFrame(() => {
            if (!ownsMenu(addedElement, revision)) {
              return;
            }
            updateLoraMenu(addedElement, node, revision);
            node.__easyuseAnimaOpeningLoraMenu = false;
            activeLoraMenuNode = null;
          });
        }
      }
    };

    let nextObserver = /** @type {MutationObserver | null} */ (null);
    const cleanupPreparedResources = () => {
      try {
        nextObserver?.disconnect();
      } catch {
        // Preserve the error that caused installation to fail.
      }
      try {
        nextStyleElement.remove();
      } catch {
        // Preserve the error that caused installation to fail.
      }
    };
    try {
      nextObserver = new MutationObserver(handleMutations);
      document.head.appendChild(nextStyleElement);
      nextObserver.observe(document.body, { childList: true, subtree: false });
    } catch (error) {
      installRevision += 1;
      cleanupPreparedResources();
      throw error;
    }

    let previousOwnerThrew = false;
    let previousOwnerError;
    if (typeof previousOwner === "function" && previousOwner !== dispose) {
      try {
        previousOwner();
      } catch (error) {
        previousOwnerThrew = true;
        previousOwnerError = error;
      }
      if (typeof ownerHost[LORA_PRESET_MENU_LIFECYCLE_OWNER] === "function") {
        installRevision += 1;
        cleanupPreparedResources();
        if (previousOwnerThrew) {
          throw previousOwnerError;
        }
        throw new Error("The previous LoRA preset menu lifecycle did not release ownership.");
      }
    }

    styleElement = nextStyleElement;
    observer = nextObserver;
    installed = true;
    ownerHost[LORA_PRESET_MENU_LIFECYCLE_OWNER] = dispose;
    if (previousOwnerThrew) {
      throw previousOwnerError;
    }
    return dispose;
  }

  return {
    activateMenu,
    createMenuItems,
    dispose,
    install,
  };
}
