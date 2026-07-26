// @ts-check

const WILDCARD_SEED_MAX = Number.MAX_SAFE_INTEGER;
const WILDCARD_SEED_MAX_BIGINT = BigInt(WILDCARD_SEED_MAX);
const WILDCARD_SEED_CONTROL_ALIASES = new Map([
  ["fixed", "fixed"],
  ["고정", "fixed"],
  ["random", "randomize"],
  ["randomize", "randomize"],
  ["매번 랜덤", "randomize"],
  ["increase", "increment"],
  ["increment", "increment"],
  ["증가", "increment"],
]);
const LEGACY_FIXED_WILDCARD_MODES = new Set([
  "fixed",
  "고정",
  "reproduce",
  "재현",
]);
const WILDCARD_SEED_INPUT_STATES = new WeakMap();

/**
 * Normalize Prompt Studio's independent next-seed policy. Legacy Fixed and
 * Reproduce modes keep their historical fixed-seed meaning while loading.
 *
 * @param {any} control
 * @param {any} [mode]
 */
function normalizeWildcardSeedControl(control, mode = null) {
  const normalizedMode = String(mode || "").trim().toLowerCase();
  if (LEGACY_FIXED_WILDCARD_MODES.has(normalizedMode)) {
    return "fixed";
  }
  return WILDCARD_SEED_CONTROL_ALIASES.get(
    String(control || "").trim().toLowerCase(),
  ) || "fixed";
}

/** @param {any} value */
function normalizeWildcardSeed(value) {
  const numberValue = Number(value);
  if (!Number.isFinite(numberValue)) {
    return 0;
  }
  return Math.max(0, Math.min(WILDCARD_SEED_MAX, Math.trunc(numberValue)));
}

/** @param {any} value */
function optionalWildcardSeed(value) {
  const numberValue = Number(value);
  return Number.isSafeInteger(numberValue)
    && numberValue >= 0
    && numberValue <= WILDCARD_SEED_MAX
    ? numberValue
    : null;
}

/**
 * Normalize an editable value without silently replacing a loaded legacy
 * uint64 seed. A null result tells the caller to restore the current widget
 * value instead of publishing a rounded JavaScript number.
 *
 * @param {any} value
 */
function normalizeWildcardSeedInput(value) {
  if (typeof value === "number") {
    return Number.isSafeInteger(value) && value >= 0 ? value : null;
  }
  if (typeof value !== "string") {
    return null;
  }
  const decimal = value.trim();
  if (!/^\d+$/.test(decimal)) {
    return null;
  }
  try {
    const parsed = BigInt(decimal);
    return parsed <= WILDCARD_SEED_MAX_BIGINT ? Number(parsed) : null;
  } catch {
    return null;
  }
}

/**
 * @param {any} input
 * @param {() => any} getCurrentSeed
 * @param {(seed: number) => void} publishSeed
 * @param {(seed: number) => void} [afterPublish]
 */
function bindWildcardSeedInput(input, getCurrentSeed, publishSeed, afterPublish) {
  input.min = "0";
  input.max = String(WILDCARD_SEED_MAX);
  input.step = "1";
  // An untouched open control must yield to queue/executed widget updates,
  // while any real input event keeps ownership of the user's pending edit.
  const state = {
    baselineValue: String(input.value ?? ""),
    dirty: false,
    getCurrentSeed,
  };
  WILDCARD_SEED_INPUT_STATES.set(input, state);
  const restoreCurrentSeed = () => {
    input.value = String(getCurrentSeed() ?? "0");
    state.baselineValue = input.value;
    state.dirty = false;
  };
  const syncSeed = () => {
    if (!state.dirty && input.value === state.baselineValue) {
      restoreCurrentSeed();
      return false;
    }
    const seed = normalizeWildcardSeedInput(input.value);
    if (seed == null) {
      restoreCurrentSeed();
      return false;
    }
    input.value = String(seed);
    publishSeed(seed);
    afterPublish?.(seed);
    state.baselineValue = input.value;
    state.dirty = false;
    return true;
  };
  input.addEventListener("input", () => {
    state.dirty = true;
  });
  input.addEventListener("change", syncSeed);
  input.addEventListener("blur", syncSeed);
  const requestFrame = globalThis.requestAnimationFrame;
  if (typeof requestFrame === "function") {
    requestFrame(function syncVisibleSeed() {
      if (input.isConnected !== true) {
        return;
      }
      syncBoundWildcardSeedInput(input);
      requestFrame(syncVisibleSeed);
    });
  }
  return syncSeed;
}

/**
 * Reflect a canonical seed into an already-open input only while that input
 * still represents its untouched baseline. Pending user text keeps ownership.
 *
 * @param {any} input
 */
function syncBoundWildcardSeedInput(input) {
  const state = WILDCARD_SEED_INPUT_STATES.get(input);
  if (
    !state
    || state.dirty
    || String(input.value ?? "") !== state.baselineValue
  ) {
    return false;
  }
  const currentValue = String(state.getCurrentSeed() ?? "0");
  if (String(input.value ?? "") === currentValue) {
    return false;
  }
  input.value = currentValue;
  state.baselineValue = currentValue;
  return true;
}

/**
 * @param {number} seed
 * @param {any} control
 * @param {() => any} randomSeed
 */
function nextWildcardSeed(seed, control, randomSeed = randomWildcardSeed) {
  const publicSeed = normalizeWildcardSeed(seed);
  const normalizedControl = String(control || "fixed").trim();
  if (normalizedControl === "randomize") {
    return normalizeWildcardSeed(randomSeed());
  }
  if (normalizedControl === "increment") {
    return publicSeed >= WILDCARD_SEED_MAX ? 0 : publicSeed + 1;
  }
  if (normalizedControl === "decrement") {
    return publicSeed <= 0 ? WILDCARD_SEED_MAX : publicSeed - 1;
  }
  return publicSeed;
}

/** @param {() => number} random */
function randomWildcardSeed(random = Math.random) {
  return normalizeWildcardSeed(
    Math.floor(Number(random()) * (WILDCARD_SEED_MAX + 1)),
  );
}

export {
  WILDCARD_SEED_MAX,
  bindWildcardSeedInput,
  nextWildcardSeed,
  normalizeWildcardSeed,
  normalizeWildcardSeedControl,
  normalizeWildcardSeedInput,
  optionalWildcardSeed,
  randomWildcardSeed,
  syncBoundWildcardSeedInput,
};
