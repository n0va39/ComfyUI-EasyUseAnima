// @ts-check

const PREVIEW_NODE_ID_KEYS = [
  "displayNodeId",
  "nodeId",
  "realNodeId",
  "parentNodeId",
  "display_node_id",
  "node_id",
  "real_node_id",
  "parent_node_id",
  "node",
];

function firstValue(value, fallback = "") {
  if (Array.isArray(value)) {
    return value.length > 0 ? value[0] : fallback;
  }
  return value ?? fallback;
}

function normalizeNodeId(value) {
  return value == null ? "" : String(value).trim();
}

function previewIdentity(image) {
  return [
    image?.stage || "",
    image?.type || "",
    image?.subfolder || "",
    image?.filename || image?.name || "",
  ].map((part) => String(part)).join("\u0001");
}

function previewFeedLimit(settings, fallback = 12) {
  const parsed = Number(settings?.preview?.feed_count);
  const fallbackValue = Number(fallback);
  const next = Number.isFinite(parsed)
    ? parsed
    : (Number.isFinite(fallbackValue) ? fallbackValue : 12);
  return Math.trunc(Math.max(1, Math.min(100, next)));
}

function lockLegacyCanvasPreview(node) {
  if (!node || node.__easyuseAnimaLegacyCanvasPreviewLocked) {
    return;
  }
  node.__easyuseAnimaLegacyCanvasPreviewLocked = true;
  try {
    Object.defineProperty(node, "imgs", {
      configurable: true,
      enumerable: false,
      get() {
        return [];
      },
      set() {
        // Comfy syncs ui.images into node.imgs for legacy canvas previews.
        // AiO keeps queue/history images but renders its own in-node preview.
      },
    });
  } catch {
    node.imgs = [];
  }
}

export function aioPreviewNodeIdsFromDetail(detail) {
  const ids = [];
  for (const key of PREVIEW_NODE_ID_KEYS) {
    const id = normalizeNodeId(detail?.[key]);
    if (id && !ids.includes(id)) {
      ids.push(id);
    }
  }
  return ids;
}

export function aioCreatePreviewProgressTracker() {
  const progressByNode = new Map();

  const remember = (detail) => {
    const ids = aioPreviewNodeIdsFromDetail(detail);
    if (!ids.length) {
      return;
    }
    const value = Number(detail?.value);
    const max = Number(detail?.max);
    const promptId = normalizeNodeId(detail?.prompt_id ?? detail?.jobId ?? detail?.job_id);
    const entry = {
      value: Number.isFinite(value) ? value : 0,
      max: Number.isFinite(max) ? max : 0,
      promptId,
      updatedAt: Date.now(),
    };
    for (const id of ids) {
      progressByNode.set(id, entry);
    }
  };

  const rememberState = (detail) => {
    const nodes = detail?.nodes;
    if (!nodes || typeof nodes !== "object") {
      return;
    }
    for (const state of Object.values(nodes)) {
      remember({
        ...state,
        prompt_id: state?.prompt_id || detail?.prompt_id,
      });
    }
  };

  const find = (detail) => {
    const promptId = normalizeNodeId(detail?.prompt_id ?? detail?.jobId ?? detail?.job_id);
    for (const id of aioPreviewNodeIdsFromDetail(detail)) {
      const progress = progressByNode.get(id);
      if (!progress) {
        continue;
      }
      if (promptId && progress.promptId && promptId !== progress.promptId) {
        continue;
      }
      return progress;
    }
    return null;
  };

  return {
    remember,
    rememberState,
    find,
    clear: () => progressByNode.clear(),
  };
}

export function aioPreviewImages(message) {
  const value = message?.easyuse_anima_preview;
  const raw = Array.isArray(value) ? value : [firstValue(value, null)];
  const images = [];
  for (const item of raw) {
    if (Array.isArray(item)) {
      images.push(...item);
    } else if (item) {
      images.push(item);
    }
  }
  return images.filter((item) => item && typeof item === "object" && !Array.isArray(item));
}

export function aioPreviewRunId(message) {
  return String(firstValue(message?.easyuse_anima_run_id ?? message?.run_id, "") || "");
}

export function aioTagPreviewRun(images, runId = "", startIndex = 0) {
  const normalizedRunId = runId || `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  return images.map((image, index) => ({
    ...image,
    __aio_run_id: image.__aio_run_id || normalizedRunId,
    __aio_run_index: Number.isInteger(image.__aio_run_index) ? image.__aio_run_index : startIndex + index,
  }));
}

export function aioMergePreviewImages(existingImages, nextImages, runId = "", limit = 0) {
  const existing = Array.isArray(existingImages)
    ? existingImages.filter((item) => item && typeof item === "object" && !Array.isArray(item))
    : [];
  const tagged = aioTagPreviewRun(nextImages, runId, existing.length);
  const merged = [];
  const indexByKey = new Map();
  for (const item of [...existing, ...tagged]) {
    const key = previewIdentity(item);
    if (!key.replace(/\u0001/g, "")) {
      merged.push(item);
      continue;
    }
    if (indexByKey.has(key)) {
      const index = indexByKey.get(key);
      merged[index] = { ...merged[index], ...item };
    } else {
      indexByKey.set(key, merged.length);
      merged.push(item);
    }
  }
  return limit > 0 ? merged.slice(Math.max(0, merged.length - limit)) : merged;
}

export function aioAppendPreviewFeed(existingImages, nextImages, settings, runId = "", fallbackLimit = 12) {
  return aioMergePreviewImages(
    existingImages,
    nextImages,
    runId,
    previewFeedLimit(settings, fallbackLimit),
  );
}

export function aioRemovePreviewRun(images, runId = "") {
  const normalizedRunId = String(runId || "");
  if (!normalizedRunId || !Array.isArray(images)) {
    return Array.isArray(images) ? images : [];
  }
  return images.filter((item) => String(item?.__aio_run_id || "") !== normalizedRunId);
}

export function aioResolveTerminalPreviewState(existingFeedImages, settings, runId = "") {
  const previewFeedImages = aioRemovePreviewRun(existingFeedImages, runId);
  const previewImages = settings?.preview?.image_feed ? previewFeedImages : [];
  return {
    currentRunImages: [],
    previewFeedImages,
    previewImages,
    selectedIndex: previewImages.length ? aioDefaultPreviewIndex(previewImages) : -1,
  };
}

export function aioPreviewEventDetail(event) {
  const detail = event?.detail || {};
  if (detail?.data && typeof detail.data === "object") {
    return detail.data;
  }
  return detail;
}

export function aioPreviewImageLabel(image) {
  return String(image?.label || image?.stage || "Preview");
}

export function aioPreviewImageName(image) {
  return String(image?.filename || image?.name || aioPreviewImageLabel(image) || "-");
}

export function aioPreviewResolution(image) {
  const width = Number(image?.width || 0);
  const height = Number(image?.height || 0);
  return width > 0 && height > 0 ? `${Math.trunc(width)} x ${Math.trunc(height)}` : "-";
}

export function aioPreviewFileSize(image) {
  const bytes = Number(image?.bytes || image?.size || 0);
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return "-";
  }
  const units = ["B", "KB", "MB", "GB"];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  const decimals = unit === 0 || value >= 10 ? 0 : 1;
  return `${value.toFixed(decimals)} ${units[unit]}`;
}

export function aioDefaultPreviewIndex(images) {
  if (!Array.isArray(images) || !images.length) {
    return -1;
  }
  for (let index = images.length - 1; index >= 0; index -= 1) {
    if (String(images[index]?.stage || "") === "final") {
      return index;
    }
  }
  return images.length - 1;
}

export function aioSelectedPreviewIndex(node, images) {
  const selected = Number(node?.__easyuseAnimaSelectedPreviewIndex);
  if (Number.isInteger(selected) && selected >= 0 && selected < images.length) {
    return selected;
  }
  return aioDefaultPreviewIndex(images);
}

export function aioMainPreviewImage(node, images) {
  const index = aioSelectedPreviewIndex(node, images);
  return index >= 0 ? images[index] : null;
}

export function aioDeletePreviewStoreEntry(container, locator) {
  if (!container || !locator) {
    return;
  }
  try {
    const target = container.value && typeof container.value === "object"
      ? container.value
      : container;
    if (target instanceof Map) {
      target.delete(locator);
    } else if (typeof target === "object") {
      delete target[locator];
    }
  } catch {
    // Store shapes differ across ComfyUI frontend builds.
  }
}

export function aioSuppressDefaultPreview(node, options = {}) {
  if (!node) {
    return false;
  }
  lockLegacyCanvasPreview(node);
  const shouldMarkDirty = options.markDirty !== false;
  let changed = false;
  if (node.hideOutputImages !== true) {
    node.hideOutputImages = true;
    changed = true;
  }
  for (const key of ["imgs", "images", "imageRects"]) {
    if (!Array.isArray(node[key]) || node[key].length) {
      node[key] = [];
      changed = true;
    }
  }
  for (const key of ["imageIndex", "overIndex"]) {
    if (node[key] !== null) {
      node[key] = null;
      changed = true;
    }
  }
  if (node.previewMediaType !== undefined) {
    node.previewMediaType = undefined;
    changed = true;
  }
  if (changed && shouldMarkDirty) {
    options.markNodeDirty?.(node);
  }
  return changed;
}
