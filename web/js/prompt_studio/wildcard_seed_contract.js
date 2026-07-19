// @ts-check

const WILDCARD_SEED_MAX = Number.MAX_SAFE_INTEGER;
const WILDCARD_SEED_MAX_BIGINT = BigInt(WILDCARD_SEED_MAX);
const WILDCARD_MODE_CONTROL_OVERRIDES = new Map([
  ["sequential", "increment"],
  ["순차", "increment"],
]);

/**
 * Return the seed control implied by Prompt Studio's two modes.
 *
 * @param {any} mode
 */
function wildcardSeedControlForMode(mode) {
  return WILDCARD_MODE_CONTROL_OVERRIDES.get(
    String(mode || "").trim().toLowerCase(),
  )
    || "fixed";
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
  let baselineValue = String(input.value ?? "");
  let dirty = false;
  const restoreCurrentSeed = () => {
    input.value = String(getCurrentSeed() ?? "0");
    baselineValue = input.value;
    dirty = false;
  };
  const syncSeed = () => {
    if (!dirty && input.value === baselineValue) {
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
    baselineValue = input.value;
    dirty = false;
    return true;
  };
  input.addEventListener("input", () => {
    dirty = true;
  });
  input.addEventListener("change", syncSeed);
  input.addEventListener("blur", syncSeed);
  const requestFrame = globalThis.requestAnimationFrame;
  if (typeof requestFrame === "function") {
    requestFrame(function syncVisibleSeed() {
      if (input.isConnected !== true) {
        return;
      }
      if (!dirty && String(input.value ?? "") !== String(getCurrentSeed() ?? "0")) {
        restoreCurrentSeed();
      }
      requestFrame(syncVisibleSeed);
    });
  }
  return syncSeed;
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
  normalizeWildcardSeedInput,
  optionalWildcardSeed,
  randomWildcardSeed,
  wildcardSeedControlForMode,
};
