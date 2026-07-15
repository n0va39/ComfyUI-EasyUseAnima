import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

const dataAdapterModule = await import(dataModule("../web/js/autocomplete/data_adapter.js"));
const textModel = await import(dataModule("../web/js/autocomplete/text_model.js"));

assert.deepEqual(Object.keys(dataAdapterModule), ["createAutocompleteDataAdapter"]);

const fetchCalls = [];
const autocompleteFetchCounts = new Map();
let wildcardFetchCount = 0;
let normalizeCalls = 0;
let limitCalls = 0;
let limit = 20;

async function fetchJson(url) {
  fetchCalls.push(url);
  if (url === "/easyuse_anima/wildcards") {
    wildcardFetchCount += 1;
    return {
      items: [
        "Folder/表情",
        "Ｆｏｌｄｅｒ\\Alt Path",
        "",
        null,
        42,
        "Other",
      ],
    };
  }

  const count = (autocompleteFetchCounts.get(url) || 0) + 1;
  autocompleteFetchCounts.set(url, count);
  if (url.includes("q=retry") && count === 1) {
    throw new Error("transient fetch failure");
  }
  if (url.includes("q=nonarray")) {
    return { results: null };
  }
  return {
    results: [{
      tag: `result:${url}`,
      category: "general",
      count,
    }],
  };
}

function normalizeWildcardSearchText(value) {
  normalizeCalls += 1;
  return textModel.normalizeWildcardSearchText(value);
}

function getLimit() {
  limitCalls += 1;
  return limit;
}

const adapter = dataAdapterModule.createAutocompleteDataAdapter({
  fetchJson,
  normalizeWildcardSearchText,
  getLimit,
});

assert.deepEqual(Object.keys(adapter).sort(), [
  "clearResults",
  "clearWildcards",
  "search",
  "searchWildcards",
]);
assert.equal(fetchCalls.length, 0, "factory creation must not fetch data");
assert.equal(normalizeCalls, 0, "factory creation must not normalize data");
assert.equal(limitCalls, 0, "factory creation must not read settings");

const firstQuery = "Miku Hatsune/初音";
const firstCategory = "artist,general";
const firstUrl = "/easyuse_anima/autocomplete"
  + `?q=${encodeURIComponent(firstQuery)}`
  + "&limit=20"
  + `&category=${encodeURIComponent(firstCategory)}`;
const firstResults = await adapter.search(firstQuery, firstCategory);
assert.equal(fetchCalls.at(-1), firstUrl);
assert.deepEqual(firstResults, [{
  tag: `result:${firstUrl}`,
  category: "general",
  count: 1,
}]);

const warmResults = await adapter.search("miku hatsune/初音", firstCategory);
assert.equal(warmResults, firstResults, "case-folded warm query must reuse cached result identity");
assert.equal(autocompleteFetchCounts.get(firstUrl), 1);

const artistUrl = "/easyuse_anima/autocomplete"
  + `?q=${encodeURIComponent(firstQuery)}`
  + "&limit=20&category=artist";
await adapter.search(firstQuery, "artist");
assert.equal(autocompleteFetchCounts.get(artistUrl), 1, "category must partition the cache");

limit = 5;
const limitedUrl = "/easyuse_anima/autocomplete"
  + `?q=${encodeURIComponent(firstQuery)}`
  + "&limit=5"
  + `&category=${encodeURIComponent(firstCategory)}`;
await adapter.search(firstQuery, firstCategory);
assert.equal(autocompleteFetchCounts.get(limitedUrl), 1, "limit must partition the cache");
limit = 20;
assert.equal(await adapter.search(firstQuery, firstCategory), firstResults);

const emptyResults = await adapter.search("nonarray");
assert.deepEqual(emptyResults, []);
assert.equal(await adapter.search("NONARRAY"), emptyResults);
const nonarrayUrl = "/easyuse_anima/autocomplete?q=nonarray&limit=20";
assert.equal(autocompleteFetchCounts.get(nonarrayUrl), 1);

await assert.rejects(adapter.search("retry"), /transient fetch failure/);
const retryResults = await adapter.search("retry");
const retryUrl = "/easyuse_anima/autocomplete?q=retry&limit=20";
assert.equal(autocompleteFetchCounts.get(retryUrl), 2, "failed requests must not enter the cache");
assert.equal(retryResults[0].count, 2);

limit = 2;
const wildcardResults = await adapter.searchWildcards("ＦＯＬＤＥＲ\\表情");
assert.deepEqual(wildcardResults, [{
  tag: "Folder/表情",
  category: "wildcard",
  count: 0,
  kind: "wildcard",
}]);
assert.equal(wildcardFetchCount, 1);
const warmWildcardResults = await adapter.searchWildcards("folder/表情");
assert.equal(warmWildcardResults, wildcardResults);
assert.equal(wildcardFetchCount, 1);

const folderResults = await adapter.searchWildcards("folder");
assert.deepEqual(folderResults, [
  { tag: "Folder/表情", category: "wildcard", count: 0, kind: "wildcard" },
  { tag: "Ｆｏｌｄｅｒ\\Alt Path", category: "wildcard", count: 0, kind: "wildcard" },
]);
assert.equal(wildcardFetchCount, 1, "different wildcard queries must reuse source items");

const clearableUrl = "/easyuse_anima/autocomplete?q=clearable&limit=2";
const clearableBefore = await adapter.search("clearable");
const clearResultsReturn = adapter.clearResults();
assert.equal(clearResultsReturn, undefined);
const clearableAfter = await adapter.search("clearable");
assert.notEqual(clearableAfter, clearableBefore);
assert.equal(autocompleteFetchCounts.get(clearableUrl), 2);
const folderAfterClearResults = await adapter.searchWildcards("folder");
assert.notEqual(folderAfterClearResults, folderResults);
assert.deepEqual(folderAfterClearResults, folderResults);
assert.equal(wildcardFetchCount, 1, "result invalidation must preserve wildcard source items");

const clearWildcardsReturn = adapter.clearWildcards();
assert.equal(clearWildcardsReturn, undefined);
const folderAfterClearWildcards = await adapter.searchWildcards("folder");
assert.deepEqual(folderAfterClearWildcards, folderResults);
assert.equal(wildcardFetchCount, 2, "wildcard invalidation must reload source items");
await adapter.search("clearable");
assert.equal(
  autocompleteFetchCounts.get(clearableUrl),
  3,
  "wildcard invalidation must also clear autocomplete result entries",
);

limit = 1;
const oneWildcard = await adapter.searchWildcards("folder");
assert.deepEqual(oneWildcard, [folderResults[0]]);
assert.equal(wildcardFetchCount, 2, "limit changes must not reload wildcard source items");

console.log("Autocomplete data adapter smoke passed.");
