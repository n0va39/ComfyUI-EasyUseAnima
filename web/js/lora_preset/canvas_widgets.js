// @ts-check

const MIN_NODE_WIDTH = 520;
const PROFILE_CONTROLS_HEIGHT = 30;
const PROFILE_ROW_HEIGHT = 22;
const PROFILE_LIST_PADDING = 4;
const PROFILE_VISIBLE_ROWS = 6;
const LORA_HEADER_HEIGHT = 24;
const LORA_ROW_HEIGHT = 20;
const LORA_ADD_HEIGHT = 36;

/**
 * @typedef {object} LoraPresetCanvasWidgetDependencies
 * @property {() => any} getCanvas
 * @property {() => any} getLiteGraph
 * @property {() => {strengthButtonStep: number, strengthDragStep: number, strengthDragPixels: number}} getSettings
 * @property {(key: string) => string} text
 * @property {(key: string, values?: Record<string, unknown>) => string} formatText
 * @property {(value: unknown) => any} normalizeLoraEntry
 * @property {(node: any) => any[]} lorasWidgetValue
 * @property {(node: any, mutator: (loras: any[]) => void, options?: Record<string, unknown>) => void} mutateLoras
 * @property {(node: any, index: number, patch: Record<string, unknown>, options?: Record<string, unknown>) => void} updateLoraEntry
 * @property {(node: any, lora: any) => any} loraResolveState
 * @property {(state: any) => boolean} hasLoraPathProblem
 * @property {(node: any) => boolean} isAnyLoraFixPending
 * @property {(node: any, index: number) => boolean} isLoraFixPending
 * @property {(name: unknown) => string} loraDisplayName
 * @property {{showPreview: (name: string, event?: any) => void, hidePreview: () => void}} previewLifecycle
 * @property {(node: any, event: any, pos: number[], onChoose: (entry: any) => void) => void} openLoraMenu
 * @property {(node: any, event: any, index: number) => void} openLoraEntryMenu
 * @property {(node: any, entry: any) => void} addLoraEntry
 * @property {(node: any, index: number) => void} fixSingleLoraEntry
 * @property {(node: any) => number} profileCount
 * @property {(node: any) => number} activeProfileIndex
 * @property {(node: any, index: number) => {state?: string, savedName?: string, labelKey?: string}} profileSaveStatus
 * @property {(node: any) => void} addProfile
 * @property {(node: any, index: number) => void} deleteProfile
 * @property {(node: any) => void} saveProfileSet
 * @property {(node: any, event: any, pos: number[]) => void} openProfileLoadMenu
 * @property {(node: any) => void} fixProfileLoras
 * @property {(node: any, index: number) => void} switchProfile
 * @property {(node: any, pos: number[]) => number[] | null} nodePosToClient
 * @property {() => any} getActiveProfileWheelTarget
 * @property {(target: any) => void} setActiveProfileWheelTarget
 * @property {(node: any) => void} enforceNodeLayout
 */

/**
 * Own the LoRA Preset canvas drawing, hit testing, strength drag session, and
 * custom widget creation while the entry module keeps profile/runtime state.
 *
 * @param {LoraPresetCanvasWidgetDependencies} dependencies
 */
export function createLoraPresetCanvasWidgets(dependencies) {
  const {
    getCanvas,
    getLiteGraph,
    getSettings,
    text,
    formatText,
    normalizeLoraEntry,
    lorasWidgetValue,
    mutateLoras,
    updateLoraEntry,
    loraResolveState,
    hasLoraPathProblem,
    isAnyLoraFixPending,
    isLoraFixPending,
    loraDisplayName,
    previewLifecycle,
    openLoraMenu,
    openLoraEntryMenu,
    addLoraEntry,
    fixSingleLoraEntry,
    profileCount,
    activeProfileIndex,
    profileSaveStatus,
    addProfile,
    deleteProfile,
    saveProfileSet,
    openProfileLoadMenu,
    fixProfileLoras,
    switchProfile,
    nodePosToClient,
    getActiveProfileWheelTarget,
    setActiveProfileWheelTarget,
    enforceNodeLayout,
  } = dependencies;

  function roundStrength(value) {
    return Math.round(Number(value || 0) * 1000) / 1000;
  }

  function clearLoraStrengthDrag(node) {
    if (node?.__easyuseAnimaStrengthDrag) {
      node.__easyuseAnimaStrengthDrag = null;
    }
  }

  function beginLoraStrengthDrag(node, index, pos, lora) {
    node.__easyuseAnimaStrengthDrag = {
      index,
      startX: Number(pos?.[0]) || 0,
      startStrength: Number(lora?.strength ?? 1) || 0,
      lastSteps: 0,
      moved: false,
      promptOnClick: true,
    };
  }

  function handleLoraStrengthDrag(node, event, pos) {
    const drag = node?.__easyuseAnimaStrengthDrag;
    if (!drag) {
      return false;
    }
    if (event.type === "pointerleave" || event.type === "pointerout") {
      return true;
    }
    if (event.type === "pointercancel") {
      clearLoraStrengthDrag(node);
      return true;
    }
    if (event.type === "pointermove") {
      const currentX = Number(pos?.[0]);
      const distance = Number.isFinite(currentX) ? currentX - drag.startX : Number(event.deltaX || 0);
      const settings = getSettings();
      const pixels = Math.max(1, settings.strengthDragPixels);
      const steps = Math.trunc(distance / pixels);
      if (steps !== drag.lastSteps) {
        drag.lastSteps = steps;
        drag.moved = true;
        updateLoraEntry(
          node,
          drag.index,
          { strength: roundStrength(drag.startStrength + steps * settings.strengthDragStep) },
          { render: false },
        );
      }
      return true;
    }
    if (event.type === "pointerup") {
      const shouldPrompt = drag.promptOnClick && !drag.moved;
      const lora = normalizeLoraEntry(lorasWidgetValue(node)[drag.index]);
      clearLoraStrengthDrag(node);
      if (shouldPrompt && lora.name) {
        getCanvas().prompt(text("lora.strengthPrompt"), lora.strength ?? 1, (value) => {
          const next = Number(value);
          if (Number.isFinite(next)) {
            updateLoraEntry(node, drag.index, { strength: roundStrength(next) });
          }
        }, event);
      }
      return true;
    }
    return false;
  }

  function fitCanvasText(ctx, value, maxWidth) {
    const textValue = String(value || "");
    if (ctx.measureText(textValue).width <= maxWidth) {
      return textValue;
    }
    const ellipsis = "...";
    let result = textValue;
    while (result.length > 1 && ctx.measureText(`${result}${ellipsis}`).width > maxWidth) {
      result = result.slice(0, -1);
    }
    return `${result}${ellipsis}`;
  }

  function roundedRect(ctx, x, y, width, height, radius) {
    if (typeof ctx.roundRect === "function") {
      ctx.roundRect(x, y, width, height, radius);
      return;
    }
    const r = Math.min(radius, width / 2, height / 2);
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + width - r, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + r);
    ctx.lineTo(x + width, y + height - r);
    ctx.quadraticCurveTo(x + width, y + height, x + width - r, y + height);
    ctx.lineTo(x + r, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
  }

  function pointInArea(pos, area) {
    return !!area
      && pos[0] >= area[0]
      && pos[0] <= area[0] + area[2]
      && pos[1] >= area[1]
      && pos[1] <= area[1] + area[3];
  }

  function drawToggle(ctx, x, y, height, value) {
    const width = height * 1.5;
    ctx.save();
    ctx.globalAlpha = getCanvas().editor_alpha * 0.25;
    ctx.fillStyle = "rgba(255,255,255,0.45)";
    ctx.beginPath();
    roundedRect(ctx, x + 4, y + 4, width - 8, height - 8, height / 2);
    ctx.fill();
    ctx.globalAlpha = getCanvas().editor_alpha;
    ctx.fillStyle = value ? "#89B" : "#888";
    ctx.beginPath();
    ctx.arc(value ? x + height : x + height * 0.5, y + height * 0.5, height * 0.36, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
    return [x, y, width, height];
  }

  function drawNumberPart(ctx, x, y, height, value) {
    const arrowWidth = 9;
    const arrowHeight = 10;
    const inner = 3;
    const numberWidth = 32;
    const total = arrowWidth + inner + numberWidth + inner + arrowWidth;
    const startX = x - total;
    const midY = y + height / 2;
    ctx.save();
    ctx.fill(new Path2D(`M ${startX} ${midY} l ${arrowWidth} ${arrowHeight / 2} l 0 -${arrowHeight} L ${startX} ${midY} z`));
    const textX = startX + arrowWidth + inner;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(Number(value ?? 1).toFixed(2), textX + numberWidth / 2, midY);
    const rightX = textX + numberWidth + inner;
    ctx.fill(new Path2D(`M ${rightX} ${midY - arrowHeight / 2} l ${arrowWidth} ${arrowHeight / 2} l -${arrowWidth} ${arrowHeight / 2} v -${arrowHeight} z`));
    ctx.restore();
    return {
      dec: [startX, y, arrowWidth, height],
      value: [textX, y, numberWidth, height],
      inc: [rightX, y, arrowWidth, height],
      any: [startX, y, total, height],
    };
  }

  function nodeWidgetWidth(node, fallbackWidth) {
    return Math.max(1, Number(node?.size?.[0]) || Number(fallbackWidth) || MIN_NODE_WIDTH);
  }

  class ProfileBarWidget {
    constructor() {
      this.name = "easyuse_anima_profile_bar";
      this.type = "custom";
      this.options = { serialize: false };
      this.serialize = false;
      this.__easyuseAnimaControlWidget = true;
      this.hitAreas = [];
      this.scrollOffset = 0;
      this.listArea = null;
      this.listClientArea = null;
      this.scrollTrackArea = null;
      this.scrollThumbArea = null;
      this.scrollDragging = false;
      this.scrollDragDelta = 0;
    }

    computeSize(_width, node) {
      const widgetNode = /** @type {any} */ (this).node;
      const count = node || widgetNode ? profileCount(node || widgetNode) : 1;
      const visibleRows = Math.max(1, Math.min(PROFILE_VISIBLE_ROWS, count));
      return [
        MIN_NODE_WIDTH,
        PROFILE_CONTROLS_HEIGHT + PROFILE_LIST_PADDING * 2 + visibleRows * PROFILE_ROW_HEIGHT,
      ];
    }

    draw(ctx, node, width, y, _height) {
      const drawWidth = nodeWidgetWidth(node, width);
      const canvas = getCanvas();
      const liteGraph = getLiteGraph();
      this.hitAreas = [];
      this.listArea = null;
      this.listClientArea = null;
      this.scrollTrackArea = null;
      this.scrollThumbArea = null;
      const active = activeProfileIndex(node);
      const count = profileCount(node);
      const maxOffset = Math.max(0, count - PROFILE_VISIBLE_ROWS);
      this.scrollOffset = Math.max(0, Math.min(maxOffset, this.scrollOffset || 0));

      const buttonY = y + 4;
      const buttonH = 22;
      const gap = 4;

      ctx.save();
      ctx.font = "13px sans-serif";
      ctx.textBaseline = "middle";
      ctx.fillStyle = liteGraph.WIDGET_TEXT_COLOR;
      ctx.globalAlpha = canvas.editor_alpha * 0.75;
      ctx.textAlign = "left";
      ctx.fillText(formatText("profile.header", { active, count }), 10, buttonY + buttonH / 2);
      ctx.globalAlpha = 1;

      let x = Math.max(120, drawWidth - 8);

      const drawButton = (id, label, buttonW, selected = false, disabled = false) => {
        x -= buttonW;
        if (x < 8) {
          return;
        }
        this.hitAreas.push([x, buttonY, buttonW, buttonH, id, disabled]);
        ctx.globalAlpha = disabled ? 0.45 : 1;
        ctx.fillStyle = selected ? "#3f79d8" : liteGraph.WIDGET_BGCOLOR;
        ctx.strokeStyle = selected ? "#6fa2ff" : liteGraph.WIDGET_OUTLINE_COLOR;
        ctx.beginPath();
        roundedRect(ctx, x, buttonY, buttonW, buttonH, 4);
        ctx.fill();
        ctx.stroke();
        ctx.fillStyle = liteGraph.WIDGET_TEXT_COLOR;
        ctx.textAlign = "center";
        let fontSize = 13;
        ctx.font = `${fontSize}px sans-serif`;
        while (fontSize > 10 && ctx.measureText(label).width > buttonW - 8) {
          fontSize -= 1;
          ctx.font = `${fontSize}px sans-serif`;
        }
        ctx.fillText(fitCanvasText(ctx, label, buttonW - 8), x + buttonW / 2, buttonY + buttonH / 2);
        ctx.font = "13px sans-serif";
        x -= gap;
        ctx.globalAlpha = 1;
      };

      drawButton("load", text("profile.load"), 66);
      drawButton("save", text("profile.save"), 46);
      drawButton("fix", text("profile.fix"), 40, false, isAnyLoraFixPending(node));
      drawButton("delete", "X", 28, false, count <= 1);
      drawButton("add", "+", 28);

      const listX = 8;
      const listY = y + PROFILE_CONTROLS_HEIGHT + PROFILE_LIST_PADDING;
      const listW = Math.max(0, drawWidth - 16);
      const visibleRows = Math.max(1, Math.min(PROFILE_VISIBLE_ROWS, count));
      const listH = visibleRows * PROFILE_ROW_HEIGHT;
      const hasScrollbar = count > visibleRows;
      const scrollbarW = hasScrollbar ? 10 : 0;
      const rowW = Math.max(0, listW - scrollbarW - (hasScrollbar ? 4 : 0));
      this.listArea = [listX, listY, listW, listH];
      const listClientStart = nodePosToClient(node, [listX, listY]);
      const listClientEnd = nodePosToClient(node, [listX + listW, listY + listH]);
      if (listClientStart && listClientEnd) {
        this.listClientArea = [
          Math.min(listClientStart[0], listClientEnd[0]),
          Math.min(listClientStart[1], listClientEnd[1]),
          Math.abs(listClientEnd[0] - listClientStart[0]),
          Math.abs(listClientEnd[1] - listClientStart[1]),
        ];
      }

      ctx.save();
      ctx.beginPath();
      ctx.rect(listX, listY, listW, listH);
      ctx.clip();
      for (let row = 0; row < visibleRows; row += 1) {
        const index = this.scrollOffset + row + 1;
        if (index > count) {
          break;
        }
        const rowY = listY + row * PROFILE_ROW_HEIGHT;
        const selected = index === active;
        const status = profileSaveStatus(node, index);
        const rowArea = [listX, rowY + 1, rowW, PROFILE_ROW_HEIGHT - 2];
        this.hitAreas.push([...rowArea, `profile:${index}`, false]);
        ctx.fillStyle = selected ? "#3f79d8" : "rgba(255,255,255,0.045)";
        ctx.strokeStyle = selected ? "#6fa2ff" : "rgba(255,255,255,0.12)";
        ctx.beginPath();
        roundedRect(ctx, ...rowArea, 4);
        ctx.fill();
        ctx.stroke();

        const stateColor = {
          saved: "#8ecf8e",
          changed: "#e3ba66",
          unsaved: "#b8b8b8",
        }[status.state] || "#b8b8b8";
        const leftText = `${index}. ${status.savedName || text("profile.unsaved")}`;
        const rightText = text(status.labelKey || `profile.${status.state}`);
        ctx.font = "12px sans-serif";
        const rightWidth = Math.min(82, Math.max(58, ctx.measureText(rightText).width + 16));
        ctx.textAlign = "left";
        ctx.fillStyle = liteGraph.WIDGET_TEXT_COLOR;
        ctx.fillText(fitCanvasText(ctx, leftText, Math.max(20, rowW - rightWidth - 18)), listX + 8, rowY + PROFILE_ROW_HEIGHT / 2);
        ctx.textAlign = "right";
        ctx.fillStyle = stateColor;
        ctx.fillText(rightText, listX + rowW - 8, rowY + PROFILE_ROW_HEIGHT / 2);
      }
      ctx.restore();

      if (hasScrollbar) {
        const trackW = 8;
        const trackX = listX + listW - trackW - 1;
        this.scrollTrackArea = [trackX - 2, listY, trackW + 4, listH];
        ctx.fillStyle = "rgba(255,255,255,0.08)";
        ctx.beginPath();
        roundedRect(ctx, trackX, listY, trackW, listH, 4);
        ctx.fill();

        const barH = Math.max(14, listH * (visibleRows / count));
        const barY = listY + (listH - barH) * (this.scrollOffset / Math.max(1, maxOffset));
        this.scrollThumbArea = [trackX - 2, barY, trackW + 4, barH];
        ctx.fillStyle = "rgba(255,255,255,0.42)";
        ctx.beginPath();
        roundedRect(ctx, trackX, barY, trackW, barH, 4);
        ctx.fill();
      }
      ctx.restore();
    }

    scrollToPointer(pos, node) {
      const count = profileCount(node);
      const maxOffset = Math.max(0, count - PROFILE_VISIBLE_ROWS);
      if (maxOffset <= 0 || !this.scrollTrackArea || !this.scrollThumbArea) {
        return false;
      }
      const trackY = this.scrollTrackArea[1];
      const trackH = this.scrollTrackArea[3];
      const thumbH = this.scrollThumbArea[3];
      const range = Math.max(1, trackH - thumbH);
      const y = Math.max(0, Math.min(range, pos[1] - trackY - this.scrollDragDelta));
      const nextOffset = Math.round((y / range) * maxOffset);
      if (nextOffset !== this.scrollOffset) {
        this.scrollOffset = nextOffset;
        node.setDirtyCanvas?.(true, true);
      }
      return true;
    }

    scrollByWheel(deltaY, node) {
      const count = profileCount(node);
      const maxOffset = Math.max(0, count - PROFILE_VISIBLE_ROWS);
      if (maxOffset <= 0) {
        return false;
      }
      const direction = Number(deltaY || 0) > 0 ? 1 : -1;
      const nextOffset = Math.max(0, Math.min(maxOffset, (this.scrollOffset || 0) + direction));
      if (nextOffset !== this.scrollOffset) {
        this.scrollOffset = nextOffset;
        node.setDirtyCanvas?.(true, true);
      }
      return true;
    }

    updateWheelTarget(pos, node) {
      if (pointInArea(pos, this.listArea)) {
        setActiveProfileWheelTarget({
          node,
          widget: this,
          time: performance.now(),
        });
      } else if (getActiveProfileWheelTarget()?.widget === this) {
        setActiveProfileWheelTarget(null);
      }
    }

    mouse(event, pos, node) {
      if (node?.__easyuseAnimaStrengthDrag) {
        return handleLoraStrengthDrag(node, event, pos);
      }
      if (event.type === "wheel" && pointInArea(pos, this.listArea)) {
        return this.scrollByWheel(event.deltaY, node);
      }
      if (event.type === "pointermove" && this.scrollDragging) {
        return this.scrollToPointer(pos, node);
      }
      if ((event.type === "pointerup" || event.type === "pointercancel" || event.type === "pointerleave") && this.scrollDragging) {
        this.scrollDragging = false;
        this.scrollDragDelta = 0;
        return true;
      }
      if (event.type === "pointermove") {
        this.updateWheelTarget(pos, node);
        return false;
      }
      if (event.type === "pointerout" || event.type === "pointerleave" || event.type === "pointercancel") {
        if (getActiveProfileWheelTarget()?.widget === this) {
          setActiveProfileWheelTarget(null);
        }
        return false;
      }
      if (event.type !== "pointerdown" || event.button !== 0) {
        return false;
      }
      this.updateWheelTarget(pos, node);
      if (pointInArea(pos, this.scrollThumbArea)) {
        this.scrollDragging = true;
        this.scrollDragDelta = pos[1] - this.scrollThumbArea[1];
        return true;
      }
      if (pointInArea(pos, this.scrollTrackArea)) {
        this.scrollDragging = true;
        this.scrollDragDelta = this.scrollThumbArea ? this.scrollThumbArea[3] / 2 : 0;
        return this.scrollToPointer(pos, node);
      }
      for (const [x, y, width, height, id, disabled] of this.hitAreas) {
        if (disabled || !pointInArea(pos, [x, y, width, height])) {
          continue;
        }
        if (id === "add") {
          addProfile(node);
        } else if (id === "delete") {
          deleteProfile(node, activeProfileIndex(node));
        } else if (id === "save") {
          saveProfileSet(node);
        } else if (id === "load") {
          openProfileLoadMenu(node, event, pos);
        } else if (id === "fix") {
          fixProfileLoras(node);
        } else if (String(id).startsWith("profile:")) {
          switchProfile(node, Number.parseInt(String(id).slice(8), 10));
        }
        return true;
      }
      return false;
    }
  }

  class LoraHeaderWidget {
    constructor() {
      this.name = "easyuse_anima_lora_header";
      this.type = "custom";
      this.options = { serialize: false };
      this.serialize = false;
      this.__easyuseAnimaLoraWidget = true;
      this.toggleArea = null;
    }

    computeSize() {
      return [MIN_NODE_WIDTH, LORA_HEADER_HEIGHT];
    }

    draw(ctx, node, width, y, height) {
      const drawWidth = nodeWidgetWidth(node, width);
      const canvas = getCanvas();
      const liteGraph = getLiteGraph();
      const loras = lorasWidgetValue(node);
      if (!loras.length) {
        return;
      }
      const allOn = loras.every((lora) => normalizeLoraEntry(lora).on !== false);
      const margin = 10;
      const midY = y + height / 2 + 1;
      ctx.save();
      this.toggleArea = drawToggle(ctx, margin, y + 2, height, allOn);
      ctx.globalAlpha = canvas.editor_alpha * 0.55;
      ctx.fillStyle = liteGraph.WIDGET_TEXT_COLOR;
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillText(drawWidth < 320 ? text("lora.allShort") : text("lora.toggleAll"), margin + this.toggleArea[2] + 4, midY);
      ctx.textAlign = "center";
      ctx.fillText(drawWidth < 320 ? text("lora.strengthShort") : text("lora.strength"), Math.max(margin + 90, drawWidth - margin - 28), midY);
      ctx.restore();
    }

    mouse(event, pos, node) {
      if (node?.__easyuseAnimaStrengthDrag) {
        return handleLoraStrengthDrag(node, event, pos);
      }
      if (event.type !== "pointerdown" || event.button !== 0 || !pointInArea(pos, this.toggleArea)) {
        return false;
      }
      const nextOn = !lorasWidgetValue(node).every((lora) => normalizeLoraEntry(lora).on !== false);
      mutateLoras(node, (loras) => {
        for (const lora of loras) {
          lora.on = nextOn;
        }
      });
      return true;
    }
  }

  class LoraRowWidget {
    constructor(index) {
      this.name = `easyuse_anima_lora_${index}`;
      this.type = "custom";
      this.options = { serialize: false };
      this.serialize = false;
      this.__easyuseAnimaLoraWidget = true;
      this.index = index;
      this.hitAreas = {};
    }

    computeSize() {
      return [MIN_NODE_WIDTH, LORA_ROW_HEIGHT];
    }

    draw(ctx, node, width, y, height) {
      const drawWidth = nodeWidgetWidth(node, width);
      const liteGraph = getLiteGraph();
      this.hitAreas = {};
      const lora = normalizeLoraEntry(lorasWidgetValue(node)[this.index]);
      if (!lora.name) {
        return;
      }
      const margin = drawWidth < 340 ? 6 : 10;
      const inner = drawWidth < 340 ? 2 : 4;
      const rowX = margin;
      const rowW = Math.max(0, drawWidth - margin * 2);
      const rowH = Math.max(16, height - 2);
      const rowY = y + 1;
      const midY = y + height / 2;
      const right = rowX + rowW;
      const resolveState = loraResolveState(node, lora);
      const pathProblem = hasLoraPathProblem(resolveState);
      const fixPending = isLoraFixPending(node, this.index);

      ctx.save();
      ctx.fillStyle = pathProblem ? "rgba(95, 34, 34, 0.72)" : liteGraph.WIDGET_BGCOLOR;
      ctx.strokeStyle = pathProblem ? "#ff5f5f" : liteGraph.WIDGET_OUTLINE_COLOR;
      ctx.beginPath();
      roundedRect(ctx, rowX, rowY, rowW, rowH, rowH / 2);
      ctx.fill();
      ctx.stroke();

      this.hitAreas.toggle = drawToggle(ctx, rowX, rowY, rowH, lora.on !== false);
      let posX = rowX + this.hitAreas.toggle[2] + inner;

      if (lora.on === false) {
        ctx.globalAlpha = getCanvas().editor_alpha * 0.4;
      }
      ctx.fillStyle = liteGraph.WIDGET_TEXT_COLOR;

      const showStrength = drawWidth >= 230;
      const showInfo = drawWidth >= 310;
      const showMenu = drawWidth >= 280;
      let nameRight = right - inner;
      if (showStrength) {
        const number = drawNumberPart(ctx, right - inner, rowY, rowH, lora.strength);
        this.hitAreas.dec = number.dec;
        this.hitAreas.value = number.value;
        this.hitAreas.inc = number.inc;
        this.hitAreas.strengthAny = number.any;
        nameRight = number.dec[0] - inner;

        if (showInfo) {
          const infoSize = 16;
          const infoX = number.dec[0] - infoSize - inner * 2;
          this.hitAreas.info = [infoX, rowY + 2, infoSize, Math.max(12, rowH - 4)];
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText("i", infoX + infoSize / 2, midY);
          nameRight = infoX - inner;
        } else {
          this.hitAreas.info = null;
        }
      } else {
        this.hitAreas.dec = null;
        this.hitAreas.value = null;
        this.hitAreas.inc = null;
        this.hitAreas.strengthAny = null;
        this.hitAreas.info = null;
      }

      const showFix = pathProblem && drawWidth >= 330;
      if (showFix) {
        const fixW = 28;
        const fixX = nameRight - fixW - inner;
        this.hitAreas.fix = [fixX, rowY + 2, fixW, Math.max(12, rowH - 4)];
        ctx.fillStyle = fixPending ? "rgba(110, 80, 80, 0.7)" : "rgba(190, 58, 58, 0.8)";
        ctx.strokeStyle = "#ff8989";
        ctx.beginPath();
        roundedRect(ctx, ...this.hitAreas.fix, 4);
        ctx.fill();
        ctx.stroke();
        ctx.font = "10px sans-serif";
        ctx.fillStyle = "#fff2f2";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(text("lora.fix"), fixX + fixW / 2, midY);
        ctx.font = "13px sans-serif";
        nameRight = fixX - inner;
      } else {
        this.hitAreas.fix = null;
      }

      if (showMenu) {
        const menuSize = 14;
        const menuX = nameRight - menuSize - inner;
        this.hitAreas.menu = [menuX, rowY + 2, menuSize, Math.max(12, rowH - 4)];
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillStyle = pathProblem ? "#ff9a9a" : liteGraph.WIDGET_TEXT_COLOR;
        ctx.fillText("⋮", menuX + menuSize / 2, midY);
        nameRight = menuX - inner;
      } else {
        this.hitAreas.menu = null;
      }

      const nameW = Math.max(0, nameRight - posX - inner);
      this.hitAreas.lora = [posX, y, nameW, height];
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillStyle = pathProblem ? "#ffd8d8" : liteGraph.WIDGET_TEXT_COLOR;
      if (nameW > 4) {
        ctx.fillText(fitCanvasText(ctx, loraDisplayName(lora.name), nameW), posX, midY);
      }
      ctx.restore();
    }

    mouse(event, pos, node) {
      if (node?.__easyuseAnimaStrengthDrag) {
        return handleLoraStrengthDrag(node, event, pos);
      }
      const lora = normalizeLoraEntry(lorasWidgetValue(node)[this.index]);
      if (!lora.name) {
        return false;
      }
      if (event.type === "pointerout" || event.type === "pointerleave") {
        previewLifecycle.hidePreview();
        return false;
      }
      if (event.type === "pointercancel") {
        previewLifecycle.hidePreview();
        clearLoraStrengthDrag(node);
        return false;
      }
      if (event.type === "pointermove") {
        if (pointInArea(pos, this.hitAreas.info)) {
          previewLifecycle.showPreview(lora.name, event);
        } else {
          previewLifecycle.hidePreview();
        }
      }
      if (event.type !== "pointerdown") {
        return false;
      }
      if (event.button === 2 && pointInArea(pos, [0, this.hitAreas.lora?.[1] ?? 0, node.size[0], LORA_ROW_HEIGHT])) {
        openLoraEntryMenu(node, event, this.index);
        return true;
      }
      if (event.button !== 0) {
        return false;
      }
      if (pointInArea(pos, this.hitAreas.toggle)) {
        updateLoraEntry(node, this.index, { on: lora.on === false });
        return true;
      }
      const fixPending = isLoraFixPending(node, this.index);
      if (!fixPending && pointInArea(pos, this.hitAreas.fix)) {
        fixSingleLoraEntry(node, this.index);
        return true;
      }
      if (pointInArea(pos, this.hitAreas.lora)) {
        openLoraMenu(node, event, pos, (entry) => updateLoraEntry(node, this.index, entry));
        return true;
      }
      if (pointInArea(pos, this.hitAreas.menu)) {
        openLoraEntryMenu(node, event, this.index);
        return true;
      }
      if (pointInArea(pos, this.hitAreas.info)) {
        previewLifecycle.showPreview(lora.name, event);
        return true;
      }
      if (pointInArea(pos, this.hitAreas.dec)) {
        updateLoraEntry(node, this.index, { strength: roundStrength((lora.strength ?? 1) - getSettings().strengthButtonStep) });
        return true;
      }
      if (pointInArea(pos, this.hitAreas.inc)) {
        updateLoraEntry(node, this.index, { strength: roundStrength((lora.strength ?? 1) + getSettings().strengthButtonStep) });
        return true;
      }
      if (pointInArea(pos, this.hitAreas.strengthAny)) {
        beginLoraStrengthDrag(node, this.index, pos, lora);
        return true;
      }
      return false;
    }

    promptStrength(event, node, lora) {
      getCanvas().prompt(text("lora.strengthPrompt"), lora.strength ?? 1, (value) => {
        const next = Number(value);
        if (Number.isFinite(next)) {
          updateLoraEntry(node, this.index, { strength: roundStrength(next) });
        }
      }, event);
    }
  }

  class AddLoraWidget {
    constructor() {
      this.name = "easyuse_anima_add_lora";
      this.type = "custom";
      this.options = { serialize: false };
      this.serialize = false;
      this.__easyuseAnimaLoraWidget = true;
      this.hitArea = null;
    }

    computeSize() {
      return [MIN_NODE_WIDTH, LORA_ADD_HEIGHT];
    }

    draw(ctx, node, width, y, height) {
      const drawWidth = nodeWidgetWidth(node, width);
      const liteGraph = getLiteGraph();
      const margin = 15;
      const buttonY = y + 5;
      const buttonH = height - 10;
      this.hitArea = [margin, buttonY, Math.max(0, drawWidth - margin * 2), buttonH];
      ctx.save();
      ctx.fillStyle = liteGraph.WIDGET_BGCOLOR;
      ctx.strokeStyle = liteGraph.WIDGET_OUTLINE_COLOR;
      ctx.beginPath();
      roundedRect(ctx, ...this.hitArea, 5);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = liteGraph.WIDGET_TEXT_COLOR;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(text("lora.add"), drawWidth / 2, buttonY + buttonH / 2);
      ctx.restore();
    }

    mouse(event, pos, node) {
      if (node?.__easyuseAnimaStrengthDrag) {
        return handleLoraStrengthDrag(node, event, pos);
      }
      if (event.type !== "pointerdown" || event.button !== 0 || !pointInArea(pos, this.hitArea)) {
        return false;
      }
      openLoraMenu(node, event, pos, (entry) => addLoraEntry(node, entry));
      return true;
    }
  }

  function renderProfileBar(node) {
    if (node.__easyuseAnimaProfileBar) {
      node.__easyuseAnimaProfileBar.node = node;
    }
    enforceNodeLayout(node);
  }

  function renderLoraWidgets(node) {
    if (!node.widgets) {
      return;
    }
    node.widgets = node.widgets.filter((widget) => !widget.__easyuseAnimaLoraWidget);
    const loras = lorasWidgetValue(node);
    if (loras.length) {
      node.widgets.push(new LoraHeaderWidget());
    }
    for (let index = 0; index < loras.length; index += 1) {
      node.widgets.push(new LoraRowWidget(index));
    }
    node.widgets.push(new AddLoraWidget());
    enforceNodeLayout(node);
  }

  function ensureProfileBar(node) {
    if (node.__easyuseAnimaProfileBar || !node.widgets) {
      return;
    }
    const profileBar = new ProfileBarWidget();
    /** @type {any} */ (profileBar).node = node;
    node.__easyuseAnimaProfileBar = profileBar;
    node.widgets = node.widgets.filter((widget) => !widget.__easyuseAnimaControlWidget);
    const insertBeforeIndex = node.widgets.findIndex((widget) => widget.name === "lora_name" || widget.name === "loras");
    if (insertBeforeIndex >= 0) {
      node.widgets.splice(insertBeforeIndex, 0, profileBar);
    } else {
      node.widgets.push(profileBar);
    }
    renderProfileBar(node);
    renderLoraWidgets(node);
  }

  return {
    AddLoraWidget,
    LoraHeaderWidget,
    LoraRowWidget,
    ProfileBarWidget,
    clearLoraStrengthDrag,
    ensureProfileBar,
    minNodeWidth: MIN_NODE_WIDTH,
    pointInArea,
    profileVisibleRows: PROFILE_VISIBLE_ROWS,
    renderLoraWidgets,
    renderProfileBar,
  };
}
