// @ts-check

/**
 * @typedef {object} AutocompleteDataAdapterDependencies
 * @property {(url: string) => Promise<any>} fetchJson
 * @property {(value: any) => string} normalizeWildcardSearchText
 * @property {() => number} getLimit
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
  const cache = new Map();
  let wildcardItemsCache = null;

  function clearResults() {
    cache.clear();
  }

  function clearWildcards() {
    wildcardItemsCache = null;
    cache.clear();
  }

  async function search(query, category = "") {
    const key = `${category || "all"}:${getLimit()}:${query.toLocaleLowerCase()}`;
    if (cache.has(key)) {
      return cache.get(key);
    }
    const categoryParam = category ? `&category=${encodeURIComponent(category)}` : "";
    const data = await fetchJson(
      `/easyuse_anima/autocomplete?q=${encodeURIComponent(query)}&limit=${getLimit()}${categoryParam}`,
    );
    const results = Array.isArray(data.results) ? data.results : [];
    cache.set(key, results);
    return results;
  }

  async function loadWildcardItems() {
    if (Array.isArray(wildcardItemsCache)) {
      return wildcardItemsCache;
    }
    const data = await fetchJson("/easyuse_anima/wildcards");
    wildcardItemsCache = Array.isArray(data.items)
      ? data.items.map((item) => String(item || "")).filter(Boolean)
      : [];
    return wildcardItemsCache;
  }

  async function searchWildcards(query) {
    const normalized = normalizeWildcardSearchText(query);
    const key = `wildcard:${getLimit()}:${normalized}`;
    if (cache.has(key)) {
      return cache.get(key);
    }
    const items = await loadWildcardItems();
    const results = items
      .filter((item) => !normalized || normalizeWildcardSearchText(item).includes(normalized))
      .slice(0, getLimit())
      .map((item) => ({
        tag: item,
        category: "wildcard",
        count: 0,
        kind: "wildcard",
      }));
    cache.set(key, results);
    return results;
  }

  return {
    search,
    searchWildcards,
    clearResults,
    clearWildcards,
  };
}
