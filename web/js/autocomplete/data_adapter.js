// @ts-check

/**
 * @typedef {object} AutocompleteDataAdapterDependencies
 * @property {(url: string, options?: {signal?: AbortSignal}) => Promise<any>} fetchJson
 * @property {(value: any) => string} normalizeWildcardSearchText
 * @property {() => number} getLimit
 * @property {() => number} [now]
 */

/**
 * @typedef {object} ResolvedResultCacheEntry
 * @property {any[]} results
 * @property {number} expiresAt
 */

/**
 * @typedef {object} ResultRequestOwner
 * @property {string} key
 * @property {number} epoch
 * @property {Promise<any[]>} promise
 * @property {AbortController} controller
 * @property {number} consumers
 * @property {boolean} settled
 */

/**
 * @typedef {object} WildcardSourceRequestOwner
 * @property {number} epoch
 * @property {Promise<string[]>} promise
 * @property {AbortController} controller
 * @property {boolean} settled
 */

/** @typedef {Promise<any[]> & {abort: () => void}} AbortableResultPromise */

// A 256-entry cap bounds arrays of up to 100 suggestions while retaining a
// useful editing-session working set; five minutes keeps warm-query latency low
// without preserving resolved backend data for an entire long-running session.
const RESOLVED_CACHE_MAX_ENTRIES = 256;
const RESOLVED_CACHE_TTL_MS = 5 * 60 * 1000;

function createAbortError() {
  const error = new Error("The autocomplete request was aborted.");
  error.name = "AbortError";
  return error;
}

/**
 * Own autocomplete result caching, wildcard source loading, and source-setting
 * identity without taking ownership of DOM, popup, or extension lifecycle.
 *
 * @param {AutocompleteDataAdapterDependencies} dependencies
 */
export function createAutocompleteDataAdapter(dependencies) {
  const {
    fetchJson,
    normalizeWildcardSearchText,
    getLimit,
    now = Date.now,
  } = dependencies;
  /** @type {Map<string, ResolvedResultCacheEntry>} */
  const cache = new Map();
  /** @type {Map<string, ResultRequestOwner>} */
  const pendingResults = new Map();
  let resultsEpoch = 0;
  let wildcardSourceEpoch = 0;
  /** @type {string[] | null} */
  let wildcardItemsCache = null;
  /** @type {WildcardSourceRequestOwner | null} */
  let wildcardLoadOwner = null;
  let autocompleteSourceSeen = false;
  let autocompleteSourceSignature = "";
  let wildcardExtraPathsSeen = false;
  let wildcardExtraPathsSignature = "";

  function dataSettingSignature(value) {
    try {
      return JSON.stringify([value]);
    } catch {
      return String(value);
    }
  }

  /**
   * Read one unexpired result and promote it to the most-recently-used slot.
   * TTL is measured from resolution rather than extended by cache hits.
   *
   * @param {string} key
   * @returns {any[] | null}
   */
  function getCachedResults(key) {
    const entry = cache.get(key);
    if (!entry) {
      return null;
    }
    if (entry.expiresAt <= now()) {
      cache.delete(key);
      return null;
    }
    cache.delete(key);
    cache.set(key, entry);
    return entry.results;
  }

  /**
   * @param {string} key
   * @param {any[]} results
   */
  function cacheResults(key, results) {
    cache.delete(key);
    cache.set(key, {
      results,
      expiresAt: now() + RESOLVED_CACHE_TTL_MS,
    });
    while (cache.size > RESOLVED_CACHE_MAX_ENTRIES) {
      const oldestKey = cache.keys().next().value;
      if (oldestKey === undefined) {
        break;
      }
      cache.delete(oldestKey);
    }
  }

  /**
   * @param {any[]} results
   * @returns {AbortableResultPromise}
   */
  function resolvedResults(results) {
    const promise = /** @type {AbortableResultPromise} */ (Promise.resolve(results));
    promise.abort = () => {};
    return promise;
  }

  /**
   * Give each caller independent cancellation while retaining one shared load.
   * The underlying request is aborted only after its final consumer releases it.
   *
   * @param {ResultRequestOwner} owner
   * @returns {AbortableResultPromise}
   */
  function consumeResults(owner) {
    /** @type {(value: any[]) => void} */
    let resolveConsumer = () => {};
    /** @type {(reason?: any) => void} */
    let rejectConsumer = () => {};
    let consumerSettled = false;
    let released = false;
    owner.consumers += 1;

    const release = (abortWhenUnused) => {
      if (released) {
        return;
      }
      released = true;
      owner.consumers = Math.max(0, owner.consumers - 1);
      if (abortWhenUnused && owner.consumers === 0 && !owner.settled) {
        owner.controller.abort();
        if (pendingResults.get(owner.key) === owner) {
          pendingResults.delete(owner.key);
        }
      }
    };

    const consumerPromise = /** @type {AbortableResultPromise} */ (new Promise(
      (resolve, reject) => {
        resolveConsumer = resolve;
        rejectConsumer = reject;
      },
    ));
    owner.promise.then(
      (results) => {
        if (consumerSettled) {
          return;
        }
        consumerSettled = true;
        release(false);
        resolveConsumer(results);
      },
      (error) => {
        if (consumerSettled) {
          return;
        }
        consumerSettled = true;
        release(false);
        rejectConsumer(error);
      },
    );
    consumerPromise.abort = () => {
      if (consumerSettled) {
        return;
      }
      consumerSettled = true;
      release(true);
      rejectConsumer(createAbortError());
    };
    return consumerPromise;
  }

  /**
   * @param {string} key
   * @param {(signal: AbortSignal) => Promise<any[]>} load
   * @returns {AbortableResultPromise}
   */
  function requestResults(key, load) {
    const cachedResults = getCachedResults(key);
    if (cachedResults !== null) {
      return resolvedResults(cachedResults);
    }

    const epoch = resultsEpoch;
    const existingOwner = pendingResults.get(key);
    if (
      existingOwner?.epoch === epoch
      && !existingOwner.controller.signal.aborted
    ) {
      return consumeResults(existingOwner);
    }

    /** @type {(value: any[]) => void} */
    let resolveRequest = () => {};
    /** @type {(reason?: any) => void} */
    let rejectRequest = () => {};
    /** @type {Promise<any[]>} */
    const promise = new Promise((resolve, reject) => {
      resolveRequest = resolve;
      rejectRequest = reject;
    });
    const controller = new AbortController();
    const owner = {
      key,
      epoch,
      promise,
      controller,
      consumers: 0,
      settled: false,
    };
    pendingResults.set(key, owner);

    /** @type {Promise<any[]>} */
    let loadPromise;
    try {
      loadPromise = load(controller.signal);
    } catch (error) {
      owner.settled = true;
      if (pendingResults.get(key) === owner) {
        pendingResults.delete(key);
      }
      rejectRequest(error);
      return consumeResults(owner);
    }

    Promise.resolve(loadPromise).then(
      (results) => {
        owner.settled = true;
        if (
          resultsEpoch === epoch
          && pendingResults.get(key) === owner
          && !controller.signal.aborted
        ) {
          cacheResults(key, results);
        }
        if (pendingResults.get(key) === owner) {
          pendingResults.delete(key);
        }
        resolveRequest(results);
      },
      (error) => {
        owner.settled = true;
        if (pendingResults.get(key) === owner) {
          pendingResults.delete(key);
        }
        rejectRequest(error);
      },
    );

    return consumeResults(owner);
  }

  function clearResults() {
    resultsEpoch += 1;
    cache.clear();
    for (const owner of pendingResults.values()) {
      if (!owner.settled) {
        owner.controller.abort();
      }
    }
    pendingResults.clear();
  }

  function clearWildcards() {
    wildcardSourceEpoch += 1;
    wildcardItemsCache = null;
    if (wildcardLoadOwner && !wildcardLoadOwner.settled) {
      wildcardLoadOwner.controller.abort();
    }
    wildcardLoadOwner = null;
    clearResults();
  }

  /**
   * Track the backend settings that select autocomplete and wildcard sources.
   * Settings events carry a full snapshot, so key presence alone cannot own
   * invalidation without turning unrelated setting updates into fresh fetches.
   *
   * @param {Record<string, any> | null | undefined} settings
   * @param {{initialize?: boolean}} [options]
   * @returns {boolean}
   */
  function syncSourceSettings(settings, options = {}) {
    const initialize = !!options.initialize;
    let resultsChanged = false;
    let wildcardSourceChanged = false;

    if (
      settings
      && Object.prototype.hasOwnProperty.call(settings, "autocomplete.source")
    ) {
      const nextSignature = dataSettingSignature(settings["autocomplete.source"]);
      const changed = !autocompleteSourceSeen
        || nextSignature !== autocompleteSourceSignature;
      if (changed && (!initialize || autocompleteSourceSeen)) {
        resultsChanged = true;
      }
      autocompleteSourceSeen = true;
      autocompleteSourceSignature = nextSignature;
    }

    if (
      settings
      && Object.prototype.hasOwnProperty.call(settings, "wildcard.extra_paths")
    ) {
      const nextSignature = dataSettingSignature(settings["wildcard.extra_paths"]);
      const changed = !wildcardExtraPathsSeen
        || nextSignature !== wildcardExtraPathsSignature;
      if (changed && (!initialize || wildcardExtraPathsSeen)) {
        wildcardSourceChanged = true;
      }
      wildcardExtraPathsSeen = true;
      wildcardExtraPathsSignature = nextSignature;
    }

    if (wildcardSourceChanged) {
      clearWildcards();
    } else if (resultsChanged) {
      clearResults();
    }
    return resultsChanged || wildcardSourceChanged;
  }

  function search(query, category = "") {
    const limit = getLimit();
    const normalizedCategory = category || "";
    const key = JSON.stringify([
      "autocomplete",
      normalizedCategory,
      limit,
      query.toLocaleLowerCase(),
    ]);
    const categoryParam = normalizedCategory
      ? `&category=${encodeURIComponent(normalizedCategory)}`
      : "";
    const url = "/easyuse_anima/autocomplete"
      + `?q=${encodeURIComponent(query)}`
      + `&limit=${limit}${categoryParam}`;
    return requestResults(key, async (signal) => {
      const data = await fetchJson(url, { signal });
      return Array.isArray(data.results) ? data.results : [];
    });
  }

  function loadWildcardItems() {
    if (Array.isArray(wildcardItemsCache)) {
      return Promise.resolve(wildcardItemsCache);
    }

    const epoch = wildcardSourceEpoch;
    if (
      wildcardLoadOwner?.epoch === epoch
      && !wildcardLoadOwner.controller.signal.aborted
    ) {
      return wildcardLoadOwner.promise;
    }

    /** @type {(value: string[]) => void} */
    let resolveRequest = () => {};
    /** @type {(reason?: any) => void} */
    let rejectRequest = () => {};
    /** @type {Promise<string[]>} */
    const promise = new Promise((resolve, reject) => {
      resolveRequest = resolve;
      rejectRequest = reject;
    });
    const controller = new AbortController();
    const owner = {
      epoch,
      promise,
      controller,
      settled: false,
    };
    wildcardLoadOwner = owner;

    /** @type {Promise<any>} */
    let loadPromise;
    try {
      loadPromise = fetchJson("/easyuse_anima/wildcards", {
        signal: controller.signal,
      });
    } catch (error) {
      owner.settled = true;
      if (wildcardLoadOwner === owner) {
        wildcardLoadOwner = null;
      }
      rejectRequest(error);
      return promise;
    }

    Promise.resolve(loadPromise).then(
      (data) => {
        owner.settled = true;
        const items = Array.isArray(data.items)
          ? data.items.map((item) => String(item || "")).filter(Boolean)
          : [];
        if (
          wildcardSourceEpoch === epoch
          && wildcardLoadOwner === owner
          && !controller.signal.aborted
        ) {
          wildcardItemsCache = items;
        }
        if (wildcardLoadOwner === owner) {
          wildcardLoadOwner = null;
        }
        resolveRequest(items);
      },
      (error) => {
        owner.settled = true;
        if (wildcardLoadOwner === owner) {
          wildcardLoadOwner = null;
        }
        rejectRequest(error);
      },
    );

    return promise;
  }

  function searchWildcards(query) {
    const normalized = normalizeWildcardSearchText(query);
    const limit = getLimit();
    const key = JSON.stringify(["wildcard", limit, normalized]);
    return requestResults(key, async () => {
      const items = await loadWildcardItems();
      return items
        .filter((item) => !normalized || normalizeWildcardSearchText(item).includes(normalized))
        .slice(0, limit)
        .map((item) => ({
          tag: item,
          category: "wildcard",
          count: 0,
          kind: "wildcard",
        }));
    });
  }

  return {
    search,
    searchWildcards,
    clearResults,
    clearWildcards,
    syncSourceSettings,
  };
}
