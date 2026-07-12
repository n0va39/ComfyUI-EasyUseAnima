// @ts-check

const AIO_PANEL_SELECTOR = ".easyuse-anima-aio-node-panel";
const AIO_SETTINGS_SCROLL_SELECTOR = ".easyuse-anima-aio-node-settings-scroll";
const AIO_PREVIEW_FEED_SELECTOR = ".easyuse-anima-aio-node-preview-feed";

function wheelPathElement(event, selector) {
  for (const candidate of event?.composedPath?.() || []) {
    if (candidate instanceof Element && candidate.matches?.(selector)) {
      return candidate;
    }
  }
  const target = event?.target;
  return target instanceof Element ? target.closest(selector) : null;
}

function aioPanelFromWheelEvent(event) {
  return wheelPathElement(event, AIO_PANEL_SELECTOR);
}

function aioPreviewFeedFromWheelEvent(event, panel) {
  const feed = wheelPathElement(event, AIO_PREVIEW_FEED_SELECTOR);
  return feed && panel?.contains?.(feed) ? feed : null;
}

function aioScrollMaximum(element, axis) {
  if (!(element instanceof HTMLElement)) {
    return 0;
  }
  return axis === "x"
    ? Math.max(0, element.scrollWidth - element.clientWidth)
    : Math.max(0, element.scrollHeight - element.clientHeight);
}

function aioWheelDeltaPixels(event, element, axis) {
  const delta = axis === "x"
    ? (Number(event?.deltaX) || Number(event?.deltaY) || 0)
    : (Number(event?.deltaY) || 0);
  const deltaMode = Number(event?.deltaMode) || 0;
  if (deltaMode === 1) {
    return delta * 16;
  }
  if (deltaMode === 2) {
    const viewport = axis === "x" ? element?.clientWidth : element?.clientHeight;
    return delta * Math.max(1, Number(viewport) || 0);
  }
  return delta;
}

function consumeAioScrollAreaWheel(event, element, axis) {
  const maximum = aioScrollMaximum(element, axis);
  if (maximum <= 1) {
    return false;
  }

  // A visible scrollbar owns the wheel even at either boundary. Do not let a
  // no-op boundary wheel fall through to ComfyUI canvas zoom.
  event.preventDefault?.();
  event.stopPropagation?.();
  event.stopImmediatePropagation?.();
  const property = axis === "x" ? "scrollLeft" : "scrollTop";
  const current = Number(element[property]) || 0;
  element[property] = Math.max(
    0,
    Math.min(maximum, current + aioWheelDeltaPixels(event, element, axis)),
  );
  return true;
}

/**
 * AiO uses one vertical scroll owner: the left settings column. Its scrollbar
 * owns wheel input from anywhere in the panel. The preview feed remains a more
 * local horizontal owner only while the pointer is over that overflowing feed.
 * Canvas zoom is allowed only when neither intended scrollbar exists.
 */
function consumeAioPanelWheel(event, panel) {
  const previewFeed = aioPreviewFeedFromWheelEvent(event, panel);
  if (previewFeed && consumeAioScrollAreaWheel(event, previewFeed, "x")) {
    return true;
  }
  const settingsScroll = panel?.querySelector?.(AIO_SETTINGS_SCROLL_SELECTOR);
  return consumeAioScrollAreaWheel(event, settingsScroll, "y");
}

export {
  AIO_PANEL_SELECTOR,
  AIO_PREVIEW_FEED_SELECTOR,
  AIO_SETTINGS_SCROLL_SELECTOR,
  aioPanelFromWheelEvent,
  aioPreviewFeedFromWheelEvent,
  aioScrollMaximum,
  aioWheelDeltaPixels,
  consumeAioPanelWheel,
  consumeAioScrollAreaWheel,
};
