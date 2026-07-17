// @ts-check

const AIO_PANEL_SELECTOR = ".easyuse-anima-aio-node-panel";
const AIO_SETTINGS_SCROLL_SELECTOR = ".easyuse-anima-aio-node-settings-scroll";
const AIO_PREVIEW_SELECTOR = ".easyuse-anima-aio-node-preview";
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

function aioPreviewSurfaceFromWheelEvent(event, panel) {
  const preview = wheelPathElement(event, AIO_PREVIEW_SELECTOR);
  return preview && panel?.contains?.(preview) ? preview : null;
}

function aioSettingsScrollFromWheelEvent(event, panel) {
  const settingsScroll = wheelPathElement(event, AIO_SETTINGS_SCROLL_SELECTOR);
  return settingsScroll && panel?.contains?.(settingsScroll) ? settingsScroll : null;
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

function consumeAioWheelEvent(event) {
  event.preventDefault?.();
  event.stopPropagation?.();
  event.stopImmediatePropagation?.();
  return true;
}

function consumeAioScrollAreaWheel(event, element, axis) {
  const maximum = aioScrollMaximum(element, axis);
  if (maximum <= 1) {
    return false;
  }

  // A visible scrollbar owns the wheel even at either boundary. Do not let a
  // no-op boundary wheel fall through to ComfyUI canvas zoom.
  consumeAioWheelEvent(event);
  const property = axis === "x" ? "scrollLeft" : "scrollTop";
  const current = Number(element[property]) || 0;
  element[property] = Math.max(
    0,
    Math.min(maximum, current + aioWheelDeltaPixels(event, element, axis)),
  );
  return true;
}

/**
 * The preview surface always owns wheel input so it cannot scroll settings or
 * zoom the canvas. An overflowing preview feed maps that input to horizontal
 * scrolling. Settings owns vertical input only under its own surface, leaving
 * unrelated panel space available for the existing canvas forwarding path.
 */
function consumeAioPanelWheel(event, panel) {
  const previewFeed = aioPreviewFeedFromWheelEvent(event, panel);
  if (previewFeed && consumeAioScrollAreaWheel(event, previewFeed, "x")) {
    return true;
  }
  if (aioPreviewSurfaceFromWheelEvent(event, panel)) {
    return consumeAioWheelEvent(event);
  }
  const settingsScroll = aioSettingsScrollFromWheelEvent(event, panel);
  return consumeAioScrollAreaWheel(event, settingsScroll, "y");
}

export {
  AIO_PANEL_SELECTOR,
  AIO_PREVIEW_SELECTOR,
  AIO_PREVIEW_FEED_SELECTOR,
  AIO_SETTINGS_SCROLL_SELECTOR,
  aioPanelFromWheelEvent,
  aioPreviewFeedFromWheelEvent,
  aioPreviewSurfaceFromWheelEvent,
  aioScrollMaximum,
  aioSettingsScrollFromWheelEvent,
  aioWheelDeltaPixels,
  consumeAioPanelWheel,
  consumeAioScrollAreaWheel,
  consumeAioWheelEvent,
};
