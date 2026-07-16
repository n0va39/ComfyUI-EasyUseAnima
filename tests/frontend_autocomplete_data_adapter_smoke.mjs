import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

const dataAdapterModule = await import(dataModule("../web/js/autocomplete/data_adapter.js"));
const textModel = await import(dataModule("../web/js/autocomplete/text_model.js"));

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

function controlledFetch(requests) {
  return (url) => {
    const request = { url, ...deferred() };
    requests.push(request);
    return request.promise;
  };
}

async function flushMicrotasks(turns = 4) {
  for (let index = 0; index < turns; index += 1) {
    await Promise.resolve();
  }
}

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

const singleFlightRequests = [];
const singleFlightAdapter = dataAdapterModule.createAutocompleteDataAdapter({
  fetchJson: controlledFetch(singleFlightRequests),
  normalizeWildcardSearchText: textModel.normalizeWildcardSearchText,
  getLimit: () => 12,
});
const sharedSearchFirst = singleFlightAdapter.search("Concurrent", "artist");
const sharedSearchSecond = singleFlightAdapter.search("concurrent", "artist");
await flushMicrotasks();
assert.equal(singleFlightRequests.length, 1);
singleFlightRequests[0].resolve({ results: [{ tag: "shared" }] });
const [sharedSearchFirstResults, sharedSearchSecondResults] = await Promise.all([
  sharedSearchFirst,
  sharedSearchSecond,
]);
assert.equal(sharedSearchSecondResults, sharedSearchFirstResults);

const defaultCategorySearch = singleFlightAdapter.search("category-partition");
const explicitAllCategorySearch = singleFlightAdapter.search("category-partition", "all");
await flushMicrotasks();
assert.equal(singleFlightRequests.length, 3);
singleFlightRequests[1].resolve({ results: [{ tag: "default-category" }] });
singleFlightRequests[2].resolve({ results: [{ tag: "explicit-all-category" }] });
const [defaultCategoryResults, explicitAllCategoryResults] = await Promise.all([
  defaultCategorySearch,
  explicitAllCategorySearch,
]);
assert.equal(
  await singleFlightAdapter.search("category-partition"),
  defaultCategoryResults,
);
assert.equal(
  await singleFlightAdapter.search("category-partition", "all"),
  explicitAllCategoryResults,
);

let searchLimitSnapshotCalls = 0;
let searchLimitSnapshotUrl = "";
const searchLimitSnapshotAdapter = dataAdapterModule.createAutocompleteDataAdapter({
  fetchJson: async (url) => {
    searchLimitSnapshotUrl = url;
    return { results: [] };
  },
  normalizeWildcardSearchText: textModel.normalizeWildcardSearchText,
  getLimit: () => {
    searchLimitSnapshotCalls += 1;
    return searchLimitSnapshotCalls === 1 ? 7 : 99;
  },
});
await searchLimitSnapshotAdapter.search("snapshot", "artist");
assert.equal(searchLimitSnapshotCalls, 1, "search must snapshot its limit once");
assert.equal(
  searchLimitSnapshotUrl,
  "/easyuse_anima/autocomplete?q=snapshot&limit=7&category=artist",
);

let wildcardLimitSnapshotCalls = 0;
const wildcardLimitSnapshotAdapter = dataAdapterModule.createAutocompleteDataAdapter({
  fetchJson: async () => ({ items: ["alpha", "alpine", "alternate"] }),
  normalizeWildcardSearchText: textModel.normalizeWildcardSearchText,
  getLimit: () => {
    wildcardLimitSnapshotCalls += 1;
    return wildcardLimitSnapshotCalls === 1 ? 2 : 1;
  },
});
const wildcardLimitSnapshotResults = await wildcardLimitSnapshotAdapter.searchWildcards("al");
assert.equal(
  wildcardLimitSnapshotCalls,
  1,
  "wildcard search must snapshot its limit once",
);
assert.deepEqual(
  wildcardLimitSnapshotResults.map((item) => item.tag),
  ["alpha", "alpine"],
);

const staleResolveRequests = [];
const staleResolveAdapter = dataAdapterModule.createAutocompleteDataAdapter({
  fetchJson: controlledFetch(staleResolveRequests),
  normalizeWildcardSearchText: textModel.normalizeWildcardSearchText,
  getLimit: () => 8,
});
const staleResolveOld = staleResolveAdapter.search("epoch", "general");
await flushMicrotasks();
staleResolveAdapter.clearResults();
const staleResolveFresh = staleResolveAdapter.search("epoch", "general");
await flushMicrotasks();
assert.equal(staleResolveRequests.length, 2);
const staleResolveOldPayload = [{ tag: "old-result" }];
staleResolveRequests[0].resolve({ results: staleResolveOldPayload });
assert.equal(await staleResolveOld, staleResolveOldPayload);
const staleResolveSharedFresh = staleResolveAdapter.search("epoch", "general");
await flushMicrotasks();
assert.equal(staleResolveRequests.length, 2);
const staleResolveFreshPayload = [{ tag: "fresh-result" }];
staleResolveRequests[1].resolve({ results: staleResolveFreshPayload });
const [staleResolveFreshResults, staleResolveSharedFreshResults] = await Promise.all([
  staleResolveFresh,
  staleResolveSharedFresh,
]);
assert.equal(staleResolveFreshResults, staleResolveFreshPayload);
assert.equal(
  staleResolveSharedFreshResults,
  staleResolveFreshResults,
  "a stale resolve must not close or replace the newer in-flight request",
);
assert.equal(
  await staleResolveAdapter.search("epoch", "general"),
  staleResolveFreshPayload,
  "a stale resolve must not publish over the newer cache entry",
);

const staleRejectRequests = [];
const staleRejectAdapter = dataAdapterModule.createAutocompleteDataAdapter({
  fetchJson: controlledFetch(staleRejectRequests),
  normalizeWildcardSearchText: textModel.normalizeWildcardSearchText,
  getLimit: () => 8,
});
const staleRejectOld = staleRejectAdapter.search("epoch-reject");
await flushMicrotasks();
staleRejectAdapter.clearResults();
const staleRejectFresh = staleRejectAdapter.search("epoch-reject");
await flushMicrotasks();
const staleRejectAssertion = assert.rejects(staleRejectOld, /stale request failed/);
staleRejectRequests[0].reject(new Error("stale request failed"));
await staleRejectAssertion;
const staleRejectSharedFresh = staleRejectAdapter.search("epoch-reject");
await flushMicrotasks();
assert.equal(staleRejectRequests.length, 2);
staleRejectRequests[1].resolve({ results: [{ tag: "fresh-after-reject" }] });
const [staleRejectFreshResults, staleRejectSharedFreshResults] = await Promise.all([
  staleRejectFresh,
  staleRejectSharedFresh,
]);
assert.equal(
  staleRejectSharedFreshResults,
  staleRejectFreshResults,
  "a stale rejection must not delete the newer in-flight request",
);
assert.deepEqual(staleRejectFreshResults, [{ tag: "fresh-after-reject" }]);

const preservedWildcardRequests = [];
const preservedWildcardAdapter = dataAdapterModule.createAutocompleteDataAdapter({
  fetchJson: controlledFetch(preservedWildcardRequests),
  normalizeWildcardSearchText: textModel.normalizeWildcardSearchText,
  getLimit: () => 5,
});
const preservedWildcardOld = preservedWildcardAdapter.searchWildcards("folder");
await flushMicrotasks();
assert.equal(preservedWildcardRequests.length, 1);
preservedWildcardAdapter.clearResults();
const preservedWildcardFresh = preservedWildcardAdapter.searchWildcards("folder");
await flushMicrotasks();
assert.equal(
  preservedWildcardRequests.length,
  1,
  "clearResults must preserve and share an in-flight wildcard source load",
);
preservedWildcardRequests[0].resolve({ items: ["folder/one", "folder/two"] });
const [preservedWildcardOldResults, preservedWildcardFreshResults] = await Promise.all([
  preservedWildcardOld,
  preservedWildcardFresh,
]);
assert.notEqual(preservedWildcardOldResults, preservedWildcardFreshResults);
assert.equal(
  await preservedWildcardAdapter.searchWildcards("folder"),
  preservedWildcardFreshResults,
  "only the current result epoch may publish wildcard results",
);
assert.equal(preservedWildcardRequests.length, 1);

const staleWildcardResolveRequests = [];
const staleWildcardResolveAdapter = dataAdapterModule.createAutocompleteDataAdapter({
  fetchJson: controlledFetch(staleWildcardResolveRequests),
  normalizeWildcardSearchText: textModel.normalizeWildcardSearchText,
  getLimit: () => 5,
});
const staleWildcardResolveOld = staleWildcardResolveAdapter.searchWildcards("");
await flushMicrotasks();
staleWildcardResolveAdapter.clearWildcards();
const staleWildcardResolveFresh = staleWildcardResolveAdapter.searchWildcards("");
await flushMicrotasks();
assert.equal(staleWildcardResolveRequests.length, 2);
staleWildcardResolveRequests[0].resolve({ items: ["old/source"] });
assert.deepEqual(await staleWildcardResolveOld, [
  { tag: "old/source", category: "wildcard", count: 0, kind: "wildcard" },
]);
const staleWildcardDifferentQuery = staleWildcardResolveAdapter.searchWildcards("old");
const staleWildcardResolveSharedFresh = staleWildcardResolveAdapter.searchWildcards("");
await flushMicrotasks();
assert.equal(staleWildcardResolveRequests.length, 2);
staleWildcardResolveRequests[1].resolve({ items: ["new/source"] });
const [staleWildcardResolveFreshResults, staleWildcardResolveSharedFreshResults] = (
  await Promise.all([staleWildcardResolveFresh, staleWildcardResolveSharedFresh])
);
assert.equal(
  staleWildcardResolveSharedFreshResults,
  staleWildcardResolveFreshResults,
  "a stale wildcard resolve must not close the newer result request",
);
assert.deepEqual(staleWildcardResolveFreshResults, [
  { tag: "new/source", category: "wildcard", count: 0, kind: "wildcard" },
]);
assert.deepEqual(
  await staleWildcardDifferentQuery,
  [],
  "a stale wildcard source must not publish into a later source epoch",
);
assert.equal(
  await staleWildcardResolveAdapter.searchWildcards(""),
  staleWildcardResolveFreshResults,
);

const staleWildcardRejectRequests = [];
const staleWildcardRejectAdapter = dataAdapterModule.createAutocompleteDataAdapter({
  fetchJson: controlledFetch(staleWildcardRejectRequests),
  normalizeWildcardSearchText: textModel.normalizeWildcardSearchText,
  getLimit: () => 5,
});
const staleWildcardRejectOld = staleWildcardRejectAdapter.searchWildcards("reject");
await flushMicrotasks();
staleWildcardRejectAdapter.clearWildcards();
const staleWildcardRejectFresh = staleWildcardRejectAdapter.searchWildcards("reject");
await flushMicrotasks();
const staleWildcardRejectAssertion = assert.rejects(
  staleWildcardRejectOld,
  /stale wildcard failed/,
);
staleWildcardRejectRequests[0].reject(new Error("stale wildcard failed"));
await staleWildcardRejectAssertion;
const staleWildcardRejectSharedFresh = staleWildcardRejectAdapter.searchWildcards("reject");
await flushMicrotasks();
assert.equal(staleWildcardRejectRequests.length, 2);
staleWildcardRejectRequests[1].resolve({ items: ["reject/new"] });
const [staleWildcardRejectFreshResults, staleWildcardRejectSharedFreshResults] = (
  await Promise.all([staleWildcardRejectFresh, staleWildcardRejectSharedFresh])
);
assert.equal(
  staleWildcardRejectSharedFreshResults,
  staleWildcardRejectFreshResults,
  "a stale wildcard rejection must not close the newer source or result request",
);
assert.deepEqual(staleWildcardRejectFreshResults.map((item) => item.tag), ["reject/new"]);

const wildcardRetryRequests = [];
const wildcardRetryAdapter = dataAdapterModule.createAutocompleteDataAdapter({
  fetchJson: controlledFetch(wildcardRetryRequests),
  normalizeWildcardSearchText: textModel.normalizeWildcardSearchText,
  getLimit: () => 5,
});
const wildcardRetryFirst = wildcardRetryAdapter.searchWildcards("folder");
const wildcardRetrySame = wildcardRetryAdapter.searchWildcards("FOLDER");
const wildcardRetryDifferent = wildcardRetryAdapter.searchWildcards("other");
await flushMicrotasks();
assert.equal(
  wildcardRetryRequests.length,
  1,
  "different wildcard result queries must share one source load",
);
const wildcardRetryFirstAssertion = assert.rejects(
  wildcardRetryFirst,
  /wildcard source failed/,
);
const wildcardRetrySameAssertion = assert.rejects(
  wildcardRetrySame,
  /wildcard source failed/,
);
const wildcardRetryDifferentAssertion = assert.rejects(
  wildcardRetryDifferent,
  /wildcard source failed/,
);
wildcardRetryRequests[0].reject(new Error("wildcard source failed"));
await Promise.all([
  wildcardRetryFirstAssertion,
  wildcardRetrySameAssertion,
  wildcardRetryDifferentAssertion,
]);
const wildcardRetryFresh = wildcardRetryAdapter.searchWildcards("folder");
const wildcardRetryFreshSame = wildcardRetryAdapter.searchWildcards("FOLDER");
const wildcardRetryFreshDifferent = wildcardRetryAdapter.searchWildcards("other");
await flushMicrotasks();
assert.equal(wildcardRetryRequests.length, 2, "failed wildcard loads must be retryable");
wildcardRetryRequests[1].resolve({ items: ["folder/retried", "other/retried"] });
const [
  wildcardRetryFreshResults,
  wildcardRetryFreshSameResults,
  wildcardRetryFreshDifferentResults,
] = await Promise.all([
  wildcardRetryFresh,
  wildcardRetryFreshSame,
  wildcardRetryFreshDifferent,
]);
assert.equal(
  wildcardRetryFreshSameResults,
  wildcardRetryFreshResults,
  "same wildcard result key must be single-flight",
);
assert.notEqual(wildcardRetryFreshDifferentResults, wildcardRetryFreshResults);
assert.deepEqual(wildcardRetryFreshResults.map((item) => item.tag), ["folder/retried"]);
assert.deepEqual(wildcardRetryFreshDifferentResults.map((item) => item.tag), ["other/retried"]);

console.log("Autocomplete data adapter smoke passed.");
