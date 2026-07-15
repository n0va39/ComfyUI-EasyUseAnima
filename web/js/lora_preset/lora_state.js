// @ts-check

export function loraFixPendingSet(node) {
  node.__easyuseAnimaLoraFixPending ||= new Set();
  return node.__easyuseAnimaLoraFixPending;
}

export function isLoraFixPending(node, index) {
  return !!node?.__easyuseAnimaProfileFixPending || loraFixPendingSet(node).has(index);
}

export function isAnyLoraFixPending(node) {
  return !!node?.__easyuseAnimaProfileFixPending || loraFixPendingSet(node).size > 0;
}

export function comboEntryText(value, depth = 0) {
  if (value == null || depth > 2) {
    return "";
  }
  if (typeof value === "string" || typeof value === "number") {
    return String(value).trim();
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      const text = comboEntryText(item, depth + 1);
      if (text) {
        return text;
      }
    }
    return "";
  }
  if (typeof value === "object") {
    for (const key of ["value", "content", "name", "title", "text", "label", "path", "filename"]) {
      const text = comboEntryText(value[key], depth + 1);
      if (text && text !== "[object Object]") {
        return text;
      }
    }
  }
  return "";
}

export function validComboEntryText(value, options = {}) {
  const text = comboEntryText(value);
  if (!text || text === "[object Object]" || (!options.allowNone && text === "None")) {
    return "";
  }
  return text;
}

export function normalizeLoraNameList(values) {
  const seen = new Set();
  const names = [];
  for (const value of values || []) {
    const text = validComboEntryText(value);
    if (!text) {
      continue;
    }
    const key = text.replace(/\\/g, "/").toLowerCase();
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    names.push(text);
  }
  return names;
}

export function normalizeLoraKey(value) {
  let text = String(value || "").trim().replace(/\\/g, "/");
  const marker = "/models/loras/";
  const markerIndex = text.toLowerCase().lastIndexOf(marker);
  if (markerIndex >= 0) {
    text = text.slice(markerIndex + marker.length);
  }
  return text.replace(/^\/+|\/+$/g, "").toLowerCase();
}

export function loraFileKey(value) {
  return (String(value || "").trim().replace(/\\/g, "/").split("/").pop() || "").toLowerCase();
}

function putUniqueLoraMatch(map, key, value) {
  if (!key) {
    return;
  }
  if (!map.has(key)) {
    map.set(key, value);
    return;
  }
  if (map.get(key) !== value) {
    map.set(key, null);
  }
}

export function buildLoraLookup(values) {
  const lookup = {
    byName: new Map(),
    byFile: new Map(),
  };
  for (const name of values || []) {
    putUniqueLoraMatch(lookup.byName, normalizeLoraKey(name), name);
    putUniqueLoraMatch(lookup.byFile, loraFileKey(name), name);
  }
  return lookup;
}

export function localLoraMatch(lora, lookup) {
  if (!lookup) {
    return { state: "unknown", match: "", reason: "" };
  }
  const rawName = String(lora?.name || lora?.lora || "").trim();
  if (!rawName) {
    return { state: "unknown", match: "", reason: "" };
  }
  const slashName = rawName.replace(/\\/g, "/");
  const exact = lookup.byName.get(normalizeLoraKey(rawName));
  if (exact) {
    const exactSlash = String(exact).replace(/\\/g, "/");
    return {
      state: exactSlash === slashName ? "ok" : "fixable",
      match: exact,
      reason: "name",
    };
  }
  const byFile = lookup.byFile.get(loraFileKey(rawName));
  if (byFile) {
    return { state: "fixable", match: byFile, reason: "file" };
  }
  return {
    state: "missing",
    match: "",
    reason: "",
  };
}

export function hasLoraPathProblem(state) {
  return state?.state === "fixable" || state?.state === "missing";
}
