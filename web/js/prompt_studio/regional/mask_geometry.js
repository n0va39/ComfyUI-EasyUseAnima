// @ts-check

const MASK_MIN_SIZE = 0.01;
const MASK_HANDLE_RADIUS = 0.018;
const MASK_HANDLE_NAMES = ["nw", "n", "ne", "e", "se", "s", "sw", "w"];

export function clampRegionalValue(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

export function normalizeGeometry(geometry) {
  const raw = geometry && typeof geometry === "object" ? geometry : {};
  const shape = String(raw.type || "rect").toLowerCase() === "ellipse" ? "ellipse" : "rect";
  const x = clampRegionalValue(Number(raw.x ?? 0.1), 0, 1);
  const y = clampRegionalValue(Number(raw.y ?? 0.1), 0, 1);
  const width = clampRegionalValue(Number(raw.width ?? 0.35), MASK_MIN_SIZE, 1);
  const height = clampRegionalValue(Number(raw.height ?? 0.35), MASK_MIN_SIZE, 1);
  return {
    type: shape,
    x: Number(clampRegionalValue(x, 0, 0.99).toFixed(6)),
    y: Number(clampRegionalValue(y, 0, 0.99).toFixed(6)),
    width: Number(clampRegionalValue(width, MASK_MIN_SIZE, 1 - x).toFixed(6)),
    height: Number(clampRegionalValue(height, MASK_MIN_SIZE, 1 - y).toFixed(6)),
  };
}

export function geometryToCanvasRect(geometry, width, height) {
  return {
    x: geometry.x * width,
    y: geometry.y * height,
    width: geometry.width * width,
    height: geometry.height * height,
  };
}

export function maskHandlePoints(geometry) {
  const left = geometry.x;
  const top = geometry.y;
  const right = geometry.x + geometry.width;
  const bottom = geometry.y + geometry.height;
  const midX = geometry.x + geometry.width / 2;
  const midY = geometry.y + geometry.height / 2;
  return {
    nw: { x: left, y: top },
    n: { x: midX, y: top },
    ne: { x: right, y: top },
    e: { x: right, y: midY },
    se: { x: right, y: bottom },
    s: { x: midX, y: bottom },
    sw: { x: left, y: bottom },
    w: { x: left, y: midY },
  };
}

export function hitTestMaskHandle(geometry, point) {
  const points = maskHandlePoints(geometry);
  for (const name of MASK_HANDLE_NAMES) {
    const handle = points[name];
    if (
      Math.abs(point.x - handle.x) <= MASK_HANDLE_RADIUS
      && Math.abs(point.y - handle.y) <= MASK_HANDLE_RADIUS
    ) {
      return name;
    }
  }
  return "";
}

export function maskContainsPoint(geometry, point) {
  if (
    point.x < geometry.x
    || point.x > geometry.x + geometry.width
    || point.y < geometry.y
    || point.y > geometry.y + geometry.height
  ) {
    return false;
  }
  if (geometry.type !== "ellipse") {
    return true;
  }
  const rx = Math.max(MASK_MIN_SIZE / 2, geometry.width / 2);
  const ry = Math.max(MASK_MIN_SIZE / 2, geometry.height / 2);
  const cx = geometry.x + geometry.width / 2;
  const cy = geometry.y + geometry.height / 2;
  return (((point.x - cx) / rx) ** 2 + ((point.y - cy) / ry) ** 2) <= 1;
}

export function findMaskHandleAt(config, point, activeMaskId = 0) {
  const masks = Array.isArray(config.masks) ? config.masks : [];
  const active = masks.find((mask) => mask.mask_id === activeMaskId);
  if (!active) {
    return null;
  }
  const geometry = normalizeGeometry(active.geometry);
  const handle = hitTestMaskHandle(geometry, point);
  return handle ? { mask: active, geometry, handle } : null;
}

export function findMaskAt(config, point) {
  const masks = Array.isArray(config.masks) ? [...config.masks].reverse() : [];
  for (const mask of masks) {
    const geometry = normalizeGeometry(mask.geometry);
    if (maskContainsPoint(geometry, point)) {
      return mask;
    }
  }
  return null;
}

export function moveGeometry(geometry, dx, dy) {
  const width = clampRegionalValue(geometry.width, MASK_MIN_SIZE, 1);
  const height = clampRegionalValue(geometry.height, MASK_MIN_SIZE, 1);
  return normalizeGeometry({
    ...geometry,
    x: clampRegionalValue(geometry.x + dx, 0, Math.max(0, 1 - width)),
    y: clampRegionalValue(geometry.y + dy, 0, Math.max(0, 1 - height)),
    width,
    height,
  });
}

export function resizeGeometry(geometry, handle, dx, dy) {
  let left = geometry.x;
  let top = geometry.y;
  let right = geometry.x + geometry.width;
  let bottom = geometry.y + geometry.height;

  if (handle.includes("w")) {
    left += dx;
  }
  if (handle.includes("e")) {
    right += dx;
  }
  if (handle.includes("n")) {
    top += dy;
  }
  if (handle.includes("s")) {
    bottom += dy;
  }

  left = clampRegionalValue(left, 0, 1 - MASK_MIN_SIZE);
  top = clampRegionalValue(top, 0, 1 - MASK_MIN_SIZE);
  right = clampRegionalValue(right, MASK_MIN_SIZE, 1);
  bottom = clampRegionalValue(bottom, MASK_MIN_SIZE, 1);

  if (right - left < MASK_MIN_SIZE) {
    if (handle.includes("w")) {
      left = right - MASK_MIN_SIZE;
    } else {
      right = left + MASK_MIN_SIZE;
    }
  }
  if (bottom - top < MASK_MIN_SIZE) {
    if (handle.includes("n")) {
      top = bottom - MASK_MIN_SIZE;
    } else {
      bottom = top + MASK_MIN_SIZE;
    }
  }

  return normalizeGeometry({
    type: geometry.type,
    x: left,
    y: top,
    width: right - left,
    height: bottom - top,
  });
}
