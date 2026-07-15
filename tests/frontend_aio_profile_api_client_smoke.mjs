import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

const apiClientModule = await import(dataModule("../web/js/aio/profile_api_client.js"));

assert.deepEqual(
  Object.keys(apiClientModule),
  ["createAioProfileApiClient"],
  "AiO profile API client must expose only its factory contract",
);

const calls = [];
const responses = [];
const encodedValues = [];

async function fetchJson(url, options) {
  calls.push({
    url,
    options,
    argumentCount: arguments.length,
  });
  const response = responses.shift();
  if (response instanceof Error) {
    throw response;
  }
  return response;
}

function encodeURIComponent(value) {
  encodedValues.push(value);
  return `encoded:${value.length}`;
}

const client = apiClientModule.createAioProfileApiClient({
  fetchJson,
  encodeURIComponent,
});

assert.deepEqual(Object.keys(client).sort(), [
  "deleteProfile",
  "listProfiles",
  "loadProfile",
  "renameProfile",
  "saveProfile",
]);
assert.equal(calls.length, 0, "factory creation must not make a request");
assert.equal(encodedValues.length, 0, "factory creation must not encode a name");

const profilesResponse = { profiles: [{ name: "Portrait" }] };
responses.push(profilesResponse);
assert.equal(await client.listProfiles(), profilesResponse);
assert.deepEqual(calls.at(-1), {
  url: "/easyuse_anima/aio_profiles",
  options: undefined,
  argumentCount: 1,
});

const loadName = "set /?#[] !'()* 初音";
const loadResponse = { profile: { name: loadName, settings: { sampler: { steps: 20 } } } };
responses.push(loadResponse);
assert.equal(await client.loadProfile(loadName), loadResponse);
assert.deepEqual(encodedValues, [loadName]);
assert.deepEqual(calls.at(-1), {
  url: `/easyuse_anima/aio_profiles/load?name=encoded:${loadName.length}`,
  options: undefined,
  argumentCount: 1,
});

const settings = {
  schema_version: 4,
  sampler: { steps: 28 },
  future: { keep: true },
};
const settingsBefore = JSON.stringify(settings);
const saveResponse = { profile: { name: "Portrait" } };
responses.push(saveResponse);
assert.equal(await client.saveProfile("Portrait", true, settings), saveResponse);
assert.deepEqual(calls.at(-1), {
  url: "/easyuse_anima/aio_profiles/save",
  options: {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: "Portrait",
      overwrite: true,
      settings,
    }),
  },
  argumentCount: 2,
});
assert.equal(JSON.stringify(settings), settingsBefore, "save must not mutate settings");

const renameResponse = { profile: { name: "Portrait 2" } };
responses.push(renameResponse);
assert.equal(await client.renameProfile("Portrait", "Portrait 2", false), renameResponse);
assert.deepEqual(calls.at(-1), {
  url: "/easyuse_anima/aio_profiles/rename",
  options: {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      old_name: "Portrait",
      new_name: "Portrait 2",
      overwrite: false,
    }),
  },
  argumentCount: 2,
});

const deleteResponse = { profile: { name: "Portrait 2" } };
responses.push(deleteResponse);
assert.equal(await client.deleteProfile("Portrait 2"), deleteResponse);
assert.deepEqual(calls.at(-1), {
  url: "/easyuse_anima/aio_profiles/delete",
  options: {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: "Portrait 2" }),
  },
  argumentCount: 2,
});

const requestError = new Error("backend unavailable");
responses.push(requestError);
await assert.rejects(
  client.listProfiles(),
  (error) => error === requestError,
  "transport errors must propagate without UI fallback",
);

assert.equal(responses.length, 0);
console.log("AiO profile API client smoke passed.");
