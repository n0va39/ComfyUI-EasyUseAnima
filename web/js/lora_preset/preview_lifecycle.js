// @ts-check

/**
 * @typedef {object} LoraPresetPreviewDependencies
 * @property {Document} document
 * @property {(value: string) => string} encodeURIComponent
 * @property {number} previewSize
 */

/**
 * Keep preview geometry independent from the DOM lifecycle so viewport-edge
 * behavior can be verified without creating a preview element.
 *
 * @param {{clientX?: number, clientY?: number} | null | undefined} event
 * @param {{width: number, height: number}} bodyBounds
 * @param {number} previewSize
 * @returns {[number, number]}
 */
export function loraPreviewPosition(event, bodyBounds, previewSize) {
  let left = Number(event?.clientX || bodyBounds.width / 2) + 18;
  let top = Number(event?.clientY || bodyBounds.height / 2) + 18;
  if (left + previewSize > bodyBounds.width) {
    left = Math.max(
      0,
      Number(event?.clientX || bodyBounds.width / 2) - previewSize - 18,
    );
  }
  if (top + previewSize > bodyBounds.height) {
    top = Math.max(0, bodyBounds.height - previewSize - 12);
  }
  return [left, top];
}

/**
 * Own the singleton LoRA preview element, failed-name cache, and visibility
 * state without taking ownership of menu observers or extension listeners.
 *
 * @param {LoraPresetPreviewDependencies} dependencies
 */
export function createLoraPresetPreviewLifecycle(dependencies) {
  const {
    document,
    encodeURIComponent,
    previewSize,
  } = dependencies;
  const missingPreviewNames = new Set();

  function findPreview() {
    return /** @type {HTMLImageElement | null} */ (
      document.querySelector(".easyuse-anima-lora-preview")
    );
  }

  /**
   * @param {HTMLImageElement} element
   * @param {{clientX?: number, clientY?: number} | null | undefined} event
   */
  function positionPreview(element, event) {
    const bodyBounds = document.body.getBoundingClientRect();
    const [left, top] = loraPreviewPosition(event, bodyBounds, previewSize);
    element.style.left = `${left}px`;
    element.style.top = `${top}px`;
  }

  function hidePreview() {
    const preview = findPreview();
    if (preview) {
      preview.removeAttribute("data-visible");
      preview.style.display = "none";
    }
  }

  /** @param {string} name */
  function forgetMissingPreview(name) {
    missingPreviewNames.delete(name);
  }

  /**
   * @param {string} name
   * @param {{clientX?: number, clientY?: number} | null | undefined} event
   */
  function showPreview(name, event) {
    if (!name || name === "None") {
      hidePreview();
      return;
    }
    if (missingPreviewNames.has(name)) {
      hidePreview();
      return;
    }
    let preview = findPreview();
    if (!preview) {
      const created = document.createElement("img");
      created.className = "easyuse-anima-lora-preview";
      created.addEventListener("error", () => {
        const failedName = created.getAttribute("data-name");
        if (failedName) {
          missingPreviewNames.add(failedName);
        }
        created.style.display = "none";
        created.removeAttribute("data-name");
        created.removeAttribute("data-loaded");
        created.removeAttribute("data-visible");
      });
      created.addEventListener("load", () => {
        created.setAttribute("data-loaded", "1");
        if (
          created.getAttribute("data-name")
          && created.getAttribute("data-visible") === "1"
        ) {
          created.style.display = "block";
        }
      });
      document.body.appendChild(created);
      preview = created;
    }
    preview.setAttribute("data-visible", "1");
    positionPreview(preview, event);
    const src = `/easyuse_anima/lora_preview?name=${encodeURIComponent(name)}`;
    if (preview.getAttribute("data-name") !== name) {
      preview.setAttribute("data-name", name);
      preview.removeAttribute("data-loaded");
      preview.style.display = "none";
      preview.src = src;
      return;
    }
    if (preview.getAttribute("data-loaded") === "1" && preview.naturalWidth > 0) {
      preview.style.display = "block";
    }
  }

  return {
    showPreview,
    hidePreview,
    forgetMissingPreview,
  };
}
