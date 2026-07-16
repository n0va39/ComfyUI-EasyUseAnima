// @ts-check

const WILDCARD_SEED_MAX = Number.MAX_SAFE_INTEGER;
const WILDCARD_SEED_MAX_BIGINT = BigInt(WILDCARD_SEED_MAX);

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
  const syncSeed = () => {
    const seed = normalizeWildcardSeedInput(input.value);
    if (seed == null) {
      input.value = String(getCurrentSeed() ?? "0");
      return false;
    }
    input.value = String(seed);
    publishSeed(seed);
    afterPublish?.(seed);
    return true;
  };
  input.addEventListener("change", syncSeed);
  input.addEventListener("blur", syncSeed);
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
};
