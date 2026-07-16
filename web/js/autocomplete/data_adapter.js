// @ts-check

/**
 * @typedef {object} AutocompleteDataAdapterDependencies
 * @property {(url: string) => Promise<any>} fetchJson
 * @property {(value: any) => string} normalizeWildcardSearchText
 * @property {() => number} getLimit
 */

/**
 * @typedef {object} ResultRequestOwner
 * @property {number} epoch
 * @property {Promise<any[]>} promise
 */

/**
 * @typedef {object} WildcardSourceRequestOwner
 * @property {number} epoch
 * @property {Promise<string[]>} promise
 */

/**
 * Own autocomplete result caching and wildcard source loading without taking
 * ownership of settings, DOM, popup, or extension lifecycle.
 *
 * @param {AutocompleteDataAdapterDependencies} dependencies
 */
export function createAutocompleteDataAdapter(dependencies) {
  const {
    fetchJson,
    normalizeWildcardSearchText,
    getLimit,
  } = dependencies;
  /** @type {Map<string, any[]>} */
  const cache = new Map();
  /** @type {Map<string, ResultRequestOwner>} */
  const pendingResults = new Map();
  let resultsEpoch = 0;
  let wildcardSourceEpoch = 0;
  /** @type {string[] | null} */
  let wildcardItemsCache = null;
  /** @type {WildcardSourceRequestOwner | null} */
  let wildcardLoadOwner = null;

  /**
   * @param {string} key
   * @param {() => Promise<any[]>} load
  * @returns {Promise<any[]>}
  */
  function requestResults(key, load) {
    const cachedResults = cache.get(key);
    if (cachedResults) {
      return Promise.resolve(cachedResults);
    }

    const epoch = resultsEpoch;
    const existingOwner = pendingResults.get(key);
    if (existingOwner?.epoch === epoch) {
      return existingOwner.promise;
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
    const owner = { epoch, promise };
    pendingResults.set(key, owner);

    /** @type {Promise<any[]>} */
    let loadPromise;
    try {
      loadPromise = load();
    } catch (error) {
      if (pendingResults.get(key) === owner) {
        pendingResults.delete(key);
      }
      rejectRequest(error);
      return promise;
    }

    Promise.resolve(loadPromise).then(
      (results) => {
        if (resultsEpoch === epoch && pendingResults.get(key) === owner) {
          cache.set(key, results);
        }
        if (pendingResults.get(key) === owner) {
          pendingResults.delete(key);
        }
        resolveRequest(results);
      },
      (error) => {
        if (pendingResults.get(key) === owner) {
          pendingResults.delete(key);
        }
        rejectRequest(error);
      },
    );

    return promise;
  }

  function clearResults() {
    resultsEpoch += 1;
    cache.clear();
    pendingResults.clear();
  }

  function clearWildcards() {
    wildcardSourceEpoch += 1;
    wildcardItemsCache = null;
    wildcardLoadOwner = null;
    clearResults();
  }

  async function search(query, category = "") {
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
    return requestResults(key, async () => {
      const data = await fetchJson(url);
      return Array.isArray(data.results) ? data.results : [];
    });
  }

  function loadWildcardItems() {
    if (Array.isArray(wildcardItemsCache)) {
      return Promise.resolve(wildcardItemsCache);
    }

    const epoch = wildcardSourceEpoch;
    if (wildcardLoadOwner?.epoch === epoch) {
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
    const owner = { epoch, promise };
    wildcardLoadOwner = owner;

    /** @type {Promise<any>} */
    let loadPromise;
    try {
      loadPromise = fetchJson("/easyuse_anima/wildcards");
    } catch (error) {
      if (wildcardLoadOwner === owner) {
        wildcardLoadOwner = null;
      }
      rejectRequest(error);
      return promise;
    }

    Promise.resolve(loadPromise).then(
      (data) => {
        const items = Array.isArray(data.items)
          ? data.items.map((item) => String(item || "")).filter(Boolean)
          : [];
        if (wildcardSourceEpoch === epoch && wildcardLoadOwner === owner) {
          wildcardItemsCache = items;
        }
        if (wildcardLoadOwner === owner) {
          wildcardLoadOwner = null;
        }
        resolveRequest(items);
      },
      (error) => {
        if (wildcardLoadOwner === owner) {
          wildcardLoadOwner = null;
        }
        rejectRequest(error);
      },
    );

    return promise;
  }

  async function searchWildcards(query) {
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
  };
}
