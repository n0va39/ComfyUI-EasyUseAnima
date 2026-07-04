// @ts-check

import {
  LEGEND_COLUMNS,
  LEGEND_ITEMS,
  LEGEND_ROW_HEIGHT,
  LEGEND_TOP_GAP,
  SECTION_STYLES,
} from "./constants.js";
import {
  psText,
  sectionLabel,
} from "./text.js";
import {
  findWidget,
} from "./widgets.js";

function desiredLegendHeight() {
  return LEGEND_TOP_GAP + 16 + Math.ceil(LEGEND_ITEMS.length / LEGEND_COLUMNS) * LEGEND_ROW_HEIGHT;
}

function drawLegend(ctx, node, widget, width, y, refreshNodeSize = () => {}) {
  const nextHeight = desiredLegendHeight();
  if (Math.abs(nextHeight - widget.__height) > 2) {
    widget.__height = nextHeight;
    refreshNodeSize(node);
  }
  ctx.save();

  ctx.font = "9px sans-serif";
  ctx.fillStyle = "#94a3b8";
  ctx.fillText(psText("legend.color"), 14, y + LEGEND_TOP_GAP + 12);

  const left = 14;
  const availableWidth = Math.max(160, width - 28);
  ctx.font = "9px sans-serif";
  const maxItemWidth = Math.max(
    ...LEGEND_ITEMS.map((key) => 14 + ctx.measureText(sectionLabel(key)).width),
  );
  const columnWidth = Math.min(
    availableWidth / LEGEND_COLUMNS,
    Math.ceil(maxItemWidth + 24),
  );
  const rows = Math.ceil(LEGEND_ITEMS.length / LEGEND_COLUMNS);
  for (const [index, key] of LEGEND_ITEMS.entries()) {
    const style = SECTION_STYLES[key];
    const label = sectionLabel(key);
    const column = Math.floor(index / rows);
    const row = index % rows;
    const x = left + column * columnWidth;
    const rowY = y + LEGEND_TOP_GAP + 29 + row * LEGEND_ROW_HEIGHT;
    ctx.fillStyle = style.background;
    ctx.fillRect(x, rowY - 8, 10, 10);
    ctx.fillStyle = style.color;
    ctx.fillText(label, x + 14, rowY);
  }
  ctx.restore();
}

function ensureLegendWidget(node, refreshNodeSize = () => {}) {
  const name = "easyuse_anima_color_legend";
  let widget = findWidget(node, name);
  if (widget) {
    return widget;
  }
  widget = {
    name,
    type: "easyuse_anima_color_legend",
    serialize: false,
    __height: desiredLegendHeight(),
    computeSize(width) {
      return [width, this.__height];
    },
    draw(ctx, node, width, y) {
      drawLegend(ctx, node, this, width, y, refreshNodeSize);
    },
  };
  node.widgets ||= [];
  node.widgets.push(widget);
  return widget;
}

export {
  desiredLegendHeight,
  ensureLegendWidget,
};
