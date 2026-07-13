// @ts-check

import {
  clampRegionalValue as clamp,
  findMaskAt,
  findMaskHandleAt,
  geometryToCanvasRect,
  maskHandlePoints,
  moveGeometry,
  normalizeGeometry,
  resizeGeometry,
} from "./mask_geometry.js";
import {
  ratioLabel,
} from "./resolution.js";
import {
  normalizeRegionalMaskIds,
  toRegionalInteger,
} from "./schema.js";
import {
  clearRegionalNodeCleanup,
  setRegionalNodeCleanup,
} from "./lifecycle.js";

/** @param {any} mask */
function maskOptionLabel(mask) {
  return `${mask.mask_id}: ${mask.name || mask.label || `Mask ${mask.mask_id}`}`;
}

/** @param {any} config @param {any} selectedIds */
function maskSelectionLabel(config, selectedIds) {
  const ids = normalizeRegionalMaskIds(selectedIds);
  if (!ids.length) {
    return "None";
  }
  const masks = Array.isArray(config.masks) ? config.masks : [];
  const labels = ids.map((id) => {
    const mask = masks.find((item) => item.mask_id === id);
    return mask ? maskOptionLabel(mask) : `${id}: missing mask`;
  });
  if (labels.length <= 2) {
    return labels.join(", ");
  }
  return `${labels.length} masks`;
}

/** @param {any} canvas @param {any} config @param {number} [activeMaskId] */
function drawMaskCanvas(canvas, config, activeMaskId = 0) {
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    return;
  }
  const masks = Array.isArray(config.masks) ? config.masks : [];
  const ratio = (config.canvas?.width || 1024) / Math.max(1, config.canvas?.height || 1024);
  const width = 720;
  const height = Math.max(240, Math.round(width / ratio));
  canvas.width = width;
  canvas.height = height;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#05070a";
  ctx.fillRect(0, 0, width, height);
  ctx.strokeStyle = "#334155";
  ctx.lineWidth = 1;
  ctx.strokeRect(0.5, 0.5, width - 1, height - 1);
  for (const mask of masks) {
    if (mask.enabled === false) {
      continue;
    }
    const geometry = normalizeGeometry(mask.geometry);
    const rect = geometryToCanvasRect(geometry, width, height);
    ctx.fillStyle = `${mask.color || "#3b82f6"}66`;
    ctx.strokeStyle = mask.mask_id === activeMaskId ? "#f8fafc" : (mask.color || "#3b82f6");
    ctx.lineWidth = mask.mask_id === activeMaskId ? 3 : 2;
    drawMaskShape(ctx, geometry, rect, true);
    ctx.save();
    ctx.fillStyle = "#f8fafc";
    ctx.font = "13px system-ui";
    ctx.fillText(String(mask.mask_id), rect.x + 6, rect.y + 18);
    ctx.restore();
    if (mask.mask_id === activeMaskId) {
      drawMaskHandles(ctx, geometry, width, height);
    }
  }
}

/** @param {any} ctx @param {any} geometry @param {any} rect @param {boolean} [fill] */
function drawMaskShape(ctx, geometry, rect, fill = true) {
  ctx.beginPath();
  if (geometry.type === "ellipse") {
    ctx.ellipse(
      rect.x + rect.width / 2,
      rect.y + rect.height / 2,
      Math.max(1, rect.width / 2),
      Math.max(1, rect.height / 2),
      0,
      0,
      Math.PI * 2,
    );
  } else {
    ctx.rect(rect.x, rect.y, rect.width, rect.height);
  }
  if (fill) {
    ctx.fill();
  }
  ctx.stroke();
}

/** @param {any} ctx @param {any} geometry @param {number} width @param {number} height */
function drawMaskHandles(ctx, geometry, width, height) {
  const points = maskHandlePoints(geometry);
  ctx.save();
  ctx.fillStyle = "#f8fafc";
  ctx.strokeStyle = "#0f172a";
  ctx.lineWidth = 1;
  for (const point of Object.values(points)) {
    const x = point.x * width;
    const y = point.y * height;
    ctx.beginPath();
    ctx.rect(x - 4, y - 4, 8, 8);
    ctx.fill();
    ctx.stroke();
  }
  ctx.restore();
}

/** @param {any} canvas @param {any} event */
function canvasPoint(canvas, event) {
  const rect = canvas.getBoundingClientRect();
  return {
    x: clamp((event.clientX - rect.left) / rect.width, 0, 1),
    y: clamp((event.clientY - rect.top) / rect.height, 0, 1),
  };
}

/**
 * @param {any} app
 * @param {any} runtime
 * @param {any} layout
 * @param {{
 *   createButton: (label: string, title: string, onClick: (event?: any) => void) => any,
 *   collectRegionalEditorFields: (node: any) => any[],
 *   renderRegionalEditor: (node: any) => void,
 * }} hooks
 */
function createRegionalMaskEditor(app, runtime, layout, hooks) {
  /** @type {{ node: any, element: any } | null} */
  let activeMaskPopover = null;

  /** @param {any} [node] */
  function closeMaskPopover(node = null) {
    if (!activeMaskPopover || (node && activeMaskPopover.node !== node)) {
      return false;
    }
    return clearRegionalNodeCleanup(activeMaskPopover.node, "mask-popover");
  }

  /** @param {any} button @param {any} popover */
  function positionMaskPopover(button, popover) {
    const rect = button.getBoundingClientRect();
    const margin = 8;
    const width = Math.max(rect.width, 180);
    popover.style.minWidth = `${width}px`;
    const popoverWidth = Number(popover.offsetWidth) || width;
    const left = Math.max(
      margin,
      Math.min(rect.left, window.innerWidth - popoverWidth - margin),
    );
    const top = Math.min(rect.bottom + 4, window.innerHeight - margin);
    popover.style.left = `${left}px`;
    popover.style.top = `${top}px`;
  }

  /** @param {any} element @param {any} target */
  function eventTargetInside(element, target) {
    return target instanceof Node && !!element?.contains?.(target);
  }

  /** @param {any} button @param {any} config @param {any} ids */
  function updateMaskButton(button, config, ids) {
    const normalized = normalizeRegionalMaskIds(ids);
    button.dataset.maskIds = normalized.join(",");
    button.textContent = maskSelectionLabel(config, normalized);
    button.classList.toggle("has-mask", normalized.length > 0);
    button.title = normalized.length ? button.textContent : "No mask selected";
  }

  /**
   * @param {any} node
   * @param {any} button
   * @param {any} config
   * @param {any} selectedIds
   * @param {(ids: number[]) => void} onChange
   */
  function openMaskPopover(node, button, config, selectedIds, onChange) {
    closeMaskPopover();
    const workingIds = new Set(normalizeRegionalMaskIds(selectedIds));
    const popover = document.createElement("div");
    popover.className = "easyuse-anima-regional-mask-popover";
    const applyIds = () => {
      const ids = [...workingIds].sort((a, b) => a - b);
      updateMaskButton(button, config, ids);
      onChange?.(ids);
    };
    const addOption = (label, id = null) => {
      const row = document.createElement("label");
      row.className = "easyuse-anima-regional-mask-option";
      const input = document.createElement("input");
      input.type = id == null ? "radio" : "checkbox";
      input.checked = id == null ? workingIds.size === 0 : workingIds.has(id);
      const text = document.createElement("span");
      text.textContent = label;
      row.append(input, text);
      row.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        if (id == null) {
          workingIds.clear();
          applyIds();
          closeMaskPopover();
          return;
        }
        if (workingIds.has(id)) {
          workingIds.delete(id);
        } else {
          workingIds.add(id);
        }
        applyIds();
        renderOptions();
      });
      return row;
    };
    const renderOptions = () => {
      popover.innerHTML = "";
      popover.append(addOption("None", null));
      const masks = Array.isArray(config.masks) ? config.masks : [];
      for (const mask of masks) {
        popover.append(addOption(maskOptionLabel(mask), mask.mask_id));
      }
      for (const id of workingIds) {
        if (masks.some((mask) => mask.mask_id === id)) {
          continue;
        }
        popover.append(addOption(`${id}: missing mask`, id));
      }
    };
    renderOptions();
    document.body.appendChild(popover);
    positionMaskPopover(button, popover);

    const onOutsidePointer = (event) => {
      if (
        eventTargetInside(popover, event.target)
        || eventTargetInside(button, event.target)
      ) {
        return;
      }
      closeMaskPopover();
    };
    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        closeMaskPopover();
      }
    };
    const onWindowResize = () => positionMaskPopover(button, popover);
    const onWindowBlur = () => closeMaskPopover();
    const canvas = app.canvas?.canvas;
    document.addEventListener("pointerdown", onOutsidePointer, true);
    document.addEventListener("mousedown", onOutsidePointer, true);
    document.addEventListener("keydown", onKeyDown, true);
    window.addEventListener("resize", onWindowResize);
    window.addEventListener("blur", onWindowBlur);
    canvas?.addEventListener?.("pointerdown", onOutsidePointer, true);
    canvas?.addEventListener?.("mousedown", onOutsidePointer, true);

    activeMaskPopover = { node, element: popover };
    setRegionalNodeCleanup(node, "mask-popover", () => {
      document.removeEventListener("pointerdown", onOutsidePointer, true);
      document.removeEventListener("mousedown", onOutsidePointer, true);
      document.removeEventListener("keydown", onKeyDown, true);
      window.removeEventListener("resize", onWindowResize);
      window.removeEventListener("blur", onWindowBlur);
      canvas?.removeEventListener?.("pointerdown", onOutsidePointer, true);
      canvas?.removeEventListener?.("mousedown", onOutsidePointer, true);
      popover.remove();
      if (activeMaskPopover?.element === popover) {
        activeMaskPopover = null;
      }
    });
  }

  /** @param {any} node @param {any} config @param {any} selectedIds */
  function createMaskSelectorButton(node, config, selectedIds) {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.role = "mask_ids";
    button.className = "easyuse-anima-regional-mask-button";
    updateMaskButton(button, config, selectedIds);
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      openMaskPopover(
        node,
        button,
        config,
        normalizeRegionalMaskIds(button.dataset.maskIds),
        () => {
          runtime.writeRegionalFields(node, hooks.collectRegionalEditorFields(node));
          layout.scheduleRegionalFieldHighlights(node, false);
        },
      );
    });
    return button;
  }

  /** @param {any} node */
  function openMaskEditor(node) {
    clearRegionalNodeCleanup(node, "mask-editor");
    const working = runtime.normalizeConfigValue(
      node,
      node.__easyuseAnimaRegionalConfig || runtime.regionalConfigWidget(node)?.value,
    );
    let activeMaskId = working.masks[0]?.mask_id || 0;
    let drag = null;

    const backdrop = document.createElement("div");
    backdrop.className = "easyuse-anima-regional-modal-backdrop";
    const modal = document.createElement("div");
    modal.className = "easyuse-anima-regional-modal";
    const head = document.createElement("div");
    head.className = "easyuse-anima-regional-modal-head";
    const title = document.createElement("div");
    title.className = "easyuse-anima-regional-modal-title";
    title.textContent = "Mask editor";
    const resolution = runtime.readResolution(node);
    const size = document.createElement("div");
    size.textContent = `${resolution.width} x ${resolution.height}`;
    size.style.color = "#94a3b8";
    size.style.marginLeft = "auto";
    head.append(title, size);

    const body = document.createElement("div");
    body.className = "easyuse-anima-regional-modal-body";
    const canvasWrap = document.createElement("div");
    canvasWrap.className = "easyuse-anima-regional-canvas-wrap";
    const canvas = document.createElement("canvas");
    canvas.className = "easyuse-anima-regional-canvas";
    canvasWrap.appendChild(canvas);
    const sidebar = document.createElement("div");
    sidebar.className = "easyuse-anima-regional-mask-sidebar";
    const list = document.createElement("div");
    list.className = "easyuse-anima-regional-mask-list";
    const inspector = document.createElement("div");
    inspector.className = "easyuse-anima-regional-mask-inspector";
    sidebar.append(list, inspector);
    body.append(canvasWrap, sidebar);

    const foot = document.createElement("div");
    foot.className = "easyuse-anima-regional-modal-foot";
    const closeModal = () => clearRegionalNodeCleanup(node, "mask-editor");
    const add = hooks.createButton("Add mask", "Create a new numbered mask", () => {
      const id = Math.max(1, toRegionalInteger(working.next_mask_id, 1));
      working.next_mask_id = id + 1;
      working.masks.push({
        mask_id: id,
        label: `Mask ${id}`,
        name: "",
        color: ["#3b82f6", "#22c55e", "#f97316", "#e879f9", "#f43f5e"][(id - 1) % 5],
        enabled: true,
        geometry: {
          type: "rect",
          x: clamp(0.08 + ((id - 1) % 4) * 0.08, 0, 0.7),
          y: clamp(0.08 + ((id - 1) % 3) * 0.08, 0, 0.7),
          width: 0.32,
          height: 0.32,
        },
      });
      activeMaskId = id;
      renderModal();
    });
    const cancel = hooks.createButton("Cancel", "Close without applying changes", closeModal);
    const apply = hooks.createButton("Apply", "Apply mask changes to this node", () => {
      runtime.writeRegionalConfig(node, working);
      hooks.renderRegionalEditor(node);
      closeModal();
    });
    foot.append(add, cancel, apply);
    modal.append(head, body, foot);
    backdrop.appendChild(modal);
    document.body.appendChild(backdrop);

    function renderMaskList() {
      list.innerHTML = "";
      for (const mask of working.masks) {
        const row = document.createElement("div");
        row.className = `easyuse-anima-regional-mask-row${mask.mask_id === activeMaskId ? " active" : ""}`;
        row.addEventListener("click", () => {
          activeMaskId = mask.mask_id;
          renderModal();
        });
        const enabled = document.createElement("input");
        enabled.type = "checkbox";
        enabled.checked = mask.enabled !== false;
        enabled.addEventListener("click", (event) => event.stopPropagation());
        enabled.addEventListener("change", (event) => {
          event.stopPropagation();
          mask.enabled = enabled.checked;
          drawMaskCanvas(canvas, working, activeMaskId);
        });
        const name = document.createElement("input");
        name.type = "text";
        name.value = mask.name || mask.label || `Mask ${mask.mask_id}`;
        name.addEventListener("click", (event) => event.stopPropagation());
        name.addEventListener("input", () => {
          mask.name = name.value;
          mask.label = name.value || `Mask ${mask.mask_id}`;
        });
        const color = document.createElement("input");
        color.type = "color";
        color.value = mask.color || "#3b82f6";
        color.addEventListener("click", (event) => event.stopPropagation());
        color.addEventListener("input", () => {
          mask.color = color.value;
          drawMaskCanvas(canvas, working, activeMaskId);
        });
        const remove = hooks.createButton(
          "X",
          "Delete this mask without renumbering other masks",
          (event) => {
            event?.stopPropagation?.();
            working.masks = working.masks.filter(
              (item) => item.mask_id !== mask.mask_id,
            );
            activeMaskId = working.masks[0]?.mask_id || 0;
            renderModal();
          },
        );
        row.append(enabled, name, color, remove);
        list.appendChild(row);
      }
    }

    function renderInspector() {
      inspector.innerHTML = "";
      const mask = working.masks.find((item) => item.mask_id === activeMaskId);
      if (!mask) {
        const empty = document.createElement("div");
        empty.className = "easyuse-anima-regional-mask-inspector-empty";
        empty.textContent = "Select a mask";
        inspector.appendChild(empty);
        return;
      }
      const geometry = normalizeGeometry(mask.geometry);
      const titleRow = document.createElement("div");
      titleRow.className = "easyuse-anima-regional-mask-inspector-title";
      titleRow.textContent = `Mask ${mask.mask_id}`;

      const shapeRow = document.createElement("label");
      shapeRow.className = "easyuse-anima-regional-mask-control";
      const shapeLabel = document.createElement("span");
      shapeLabel.textContent = "Shape";
      const shape = document.createElement("select");
      for (const value of ["rect", "ellipse"]) {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value === "rect" ? "Rectangle" : "Ellipse";
        shape.appendChild(option);
      }
      shape.value = geometry.type;
      shape.addEventListener("click", (event) => event.stopPropagation());
      shape.addEventListener("change", () => {
        mask.geometry = normalizeGeometry({
          ...normalizeGeometry(mask.geometry),
          type: shape.value,
        });
        drawMaskCanvas(canvas, working, activeMaskId);
      });
      shapeRow.append(shapeLabel, shape);
      inspector.append(titleRow, shapeRow);

      const addNumber = (label, key, min, max) => {
        const row = document.createElement("label");
        row.className = "easyuse-anima-regional-mask-control";
        const text = document.createElement("span");
        text.textContent = label;
        const input = document.createElement("input");
        input.type = "number";
        input.min = String(min);
        input.max = String(max);
        input.step = "1";
        input.value = String(Math.round((geometry[key] || 0) * 100));
        input.addEventListener("click", (event) => event.stopPropagation());
        input.addEventListener("input", () => {
          const current = normalizeGeometry(mask.geometry);
          current[key] = clamp(
            (Number(input.value) || 0) / 100,
            min / 100,
            max / 100,
          );
          mask.geometry = normalizeGeometry(current);
          input.value = String(Math.round((mask.geometry[key] || 0) * 100));
          drawMaskCanvas(canvas, working, activeMaskId);
        });
        row.append(text, input);
        inspector.appendChild(row);
      };

      addNumber("X %", "x", 0, 99);
      addNumber("Y %", "y", 0, 99);
      addNumber("Width %", "width", 1, 100);
      addNumber("Height %", "height", 1, 100);
    }

    function renderModal() {
      working.canvas = {
        width: resolution.width,
        height: resolution.height,
        aspect_ratio: ratioLabel(resolution.width, resolution.height),
        source: "resolution_fields",
      };
      renderMaskList();
      renderInspector();
      drawMaskCanvas(canvas, working, activeMaskId);
    }

    canvas.addEventListener("mousedown", (event) => {
      event.preventDefault();
      const point = canvasPoint(canvas, event);
      const handleHit = findMaskHandleAt(working, point, activeMaskId);
      if (handleHit) {
        drag = {
          mode: "resize",
          handle: handleHit.handle,
          mask: handleHit.mask,
          start: point,
          geometry: handleHit.geometry,
        };
        drawMaskCanvas(canvas, working, activeMaskId);
        return;
      }
      const selected = findMaskAt(working, point);
      if (selected) {
        activeMaskId = selected.mask_id;
        const geometry = normalizeGeometry(selected.geometry);
        drag = {
          mode: "move",
          mask: selected,
          start: point,
          geometry,
        };
        renderModal();
      }
    });

    function onMouseMove(event) {
      if (!drag) {
        return;
      }
      const point = canvasPoint(canvas, event);
      const dx = point.x - drag.start.x;
      const dy = point.y - drag.start.y;
      if (drag.mode === "resize") {
        drag.mask.geometry = resizeGeometry(
          drag.geometry,
          drag.handle || "se",
          dx,
          dy,
        );
      } else {
        drag.mask.geometry = moveGeometry(drag.geometry, dx, dy);
      }
      drawMaskCanvas(canvas, working, activeMaskId);
    }

    function onMouseUp() {
      if (drag) {
        renderModal();
      }
      drag = null;
    }

    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        closeModal();
      }
    };
    const onBackdropPointer = (event) => {
      if (event.target === backdrop) {
        closeModal();
      }
    };
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    document.addEventListener("keydown", onKeyDown, true);
    backdrop.addEventListener("pointerdown", onBackdropPointer);
    setRegionalNodeCleanup(node, "mask-editor", () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
      document.removeEventListener("keydown", onKeyDown, true);
      backdrop.removeEventListener("pointerdown", onBackdropPointer);
      backdrop.remove();
      drag = null;
    });

    renderModal();
  }

  return {
    closeMaskPopover,
    createMaskSelectorButton,
    openMaskEditor,
  };
}

export {
  canvasPoint,
  createRegionalMaskEditor,
  drawMaskCanvas,
  drawMaskHandles,
  drawMaskShape,
  maskOptionLabel,
  maskSelectionLabel,
};
