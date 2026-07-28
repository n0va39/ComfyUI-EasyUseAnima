import { readFileSync } from "node:fs";

const coreSource = readFileSync(
  new URL("../web/js/prompt_studio/highlight_overlay_core.js", import.meta.url),
  "utf8",
);
const coreUrl = `data:text/javascript;base64,${Buffer.from(coreSource).toString("base64")}`;
const {
  HIGHLIGHT_TEXT_METRIC_PROPERTIES,
  copyInputTextMetrics,
  createHighlightOverlayRenderer,
  overlayBounds,
  overlayScrollbarPadding,
  syncOverlayBounds,
} = await import(coreUrl);

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

const style = Object.fromEntries(
  HIGHLIGHT_TEXT_METRIC_PROPERTIES.map((property) => [property, ""]),
);
Object.assign(style, {
  borderLeftWidth: "1px",
  borderRightWidth: "1px",
  borderTopWidth: "2px",
  borderBottomWidth: "2px",
  overflowY: "auto",
  paddingLeft: "4px",
  paddingRight: "4px",
  paddingBottom: "6px",
  font: "12px sans-serif",
  lineHeight: "18px",
});

const input = {
  offsetLeft: 8,
  offsetTop: 12,
  offsetWidth: 120,
  offsetHeight: 80,
  clientWidth: 100,
  clientHeight: 70,
  scrollHeight: 140,
  scrollTop: 17,
  scrollLeft: 5,
};
const overlay = {
  style: {},
  scrollTop: 0,
  scrollLeft: 0,
};

const padding = overlayScrollbarPadding(input, style);
assert(padding.right === "22px", "Vertical scrollbar padding changed");
assert(padding.bottom === "12px", "Horizontal scrollbar padding changed");

const noScrollbarStyle = { ...style, overflowY: "hidden" };
const noScrollbarInput = { ...input, scrollHeight: input.clientHeight };
const noScrollbarPadding = overlayScrollbarPadding(noScrollbarInput, noScrollbarStyle);
assert(
  noScrollbarPadding.right === "4px",
  "Hidden overflow must not reserve a vertical scrollbar gutter",
);
const textareaWrapWidth = input.offsetWidth
  - Number.parseFloat(style.borderLeftWidth)
  - Number.parseFloat(style.borderRightWidth)
  - Number.parseFloat(style.paddingLeft)
  - Number.parseFloat(style.paddingRight);
const overlayWrapWidth = input.offsetWidth
  - Number.parseFloat(style.borderLeftWidth)
  - Number.parseFloat(style.borderRightWidth)
  - Number.parseFloat(style.paddingLeft)
  - Number.parseFloat(noScrollbarPadding.right);
assert(
  overlayWrapWidth === textareaWrapWidth,
  "No-scrollbar overlay and textarea effective wrap widths diverged",
);
assert(
  overlayScrollbarPadding(noScrollbarInput, style).right === "4px",
  "Auto overflow without content overflow must not reserve a scrollbar gutter",
);
assert(
  JSON.stringify(overlayBounds(input)) === JSON.stringify({
    left: "8px",
    top: "12px",
    width: "120px",
    height: "80px",
  }),
  "Overlay bounds changed",
);

copyInputTextMetrics(input, overlay, style);
assert(overlay.style.font === "12px sans-serif", "Font metrics were not copied");
assert(overlay.style.lineHeight === "18px", "Line height was not copied");
assert(overlay.style.boxSizing === "border-box", "Overlay box sizing changed");
assert(overlay.style.whiteSpace === "pre-wrap", "Overlay whitespace mode changed");
assert(overlay.style.paddingRight === "22px", "Copied right padding changed");
assert(overlay.style.paddingBottom === "12px", "Copied bottom padding changed");

syncOverlayBounds(input, overlay, style);
assert(overlay.style.left === "8px", "Overlay left position changed");
assert(overlay.style.top === "12px", "Overlay top position changed");
assert(overlay.style.width === "120px", "Overlay width changed");
assert(overlay.style.height === "80px", "Overlay height changed");
assert(overlay.scrollTop === 17, "Vertical scroll synchronization changed");
assert(overlay.scrollLeft === 5, "Horizontal scroll synchronization changed");

const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;");
const renderHighlightedText = (text) => `<mark>${escapeHtml(text)}</mark>`;
const highlightOverlayHtml = createHighlightOverlayRenderer({
  escapeHtml,
  renderHighlightedText,
});

assert(
  highlightOverlayHtml("", [], "<prompt>") === '<span style="opacity: 0.45">&lt;prompt&gt;</span>',
  "Empty prompt placeholder rendering changed",
);
assert(
  highlightOverlayHtml("cat\n", []).endsWith("</mark> "),
  "Trailing newline alignment spacer changed",
);

const previewInput = {
  __easyuseAnimaAutocompletePreview: {
    sourceValue: "cat",
    value: "cathedral",
    candidateStart: 0,
    candidateEnd: 9,
    ghostStart: 3,
    ghostEnd: 9,
    color: "#cbd5e1",
  },
};
const previewHtml = highlightOverlayHtml("cat", [], "", previewInput);
assert(previewHtml.includes('opacity: 0.95">cat</span>'), "Autocomplete typed segment changed");
assert(previewHtml.includes('opacity: 0.52">hedral</span>'), "Autocomplete ghost segment changed");

previewInput.__easyuseAnimaAutocompletePreview.sourceValue = "dog";
assert(
  highlightOverlayHtml("cat", [], "", previewInput) === "<mark>cat</mark>",
  "Stale autocomplete preview fallback changed",
);

console.log("Highlight overlay core smoke passed.");
