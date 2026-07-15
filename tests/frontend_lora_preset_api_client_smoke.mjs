import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

const apiClientModule = await import(dataModule("../web/js/lora_preset/api_client.js"));

assert.deepEqual(Object.keys(apiClientModule), ["createLoraPresetApiClient"]);

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

const client = apiClientModule.createLoraPresetApiClient({
  fetchJson,
  encodeURIComponent,
});

assert.deepEqual(Object.keys(client).sort(), [
  "fixProfile",
  "listLoras",
  "listProfiles",
  "loadProfile",
  "saveProfile",
]);
assert.equal(calls.length, 0, "factory creation must not make a request");
assert.equal(encodedValues.length, 0, "factory creation must not encode a name");

const profilesResponse = { profiles: [{ name: "A" }] };
responses.push(profilesResponse);
assert.equal(await client.listProfiles(), profilesResponse);
assert.deepEqual(calls.at(-1), {
  url: "/easyuse_anima/lora_profiles",
  options: undefined,
  argumentCount: 1,
});

const loadName = "set /?#[] !'()* 初音";
const loadResponse = { profile: { name: loadName } };
responses.push(loadResponse);
assert.equal(await client.loadProfile(loadName), loadResponse);
assert.deepEqual(encodedValues, [loadName]);
assert.deepEqual(calls.at(-1), {
  url: `/easyuse_anima/lora_profiles/load?name=encoded:${loadName.length}`,
  options: undefined,
  argumentCount: 1,
});

const savePayload = {
  profile_count: 1,
  profile_index: 1,
  profile_data: {
    "1": { style_prompt: "style", loras: [{ name: "a.safetensors" }] },
  },
};
const savePayloadBefore = JSON.stringify(savePayload);
const saveResponse = { profile: { name: "Demo" } };
responses.push(saveResponse);
assert.equal(await client.saveProfile("Demo", savePayload), saveResponse);
assert.deepEqual(calls.at(-1), {
  url: "/easyuse_anima/lora_profiles/save",
  options: {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: "Demo", ...savePayload }),
  },
  argumentCount: 2,
});
assert.equal(JSON.stringify(savePayload), savePayloadBefore, "save must not mutate the payload");

const fixPayload = {
  profile_count: 2,
  profile_index: 2,
  profile_data: { "1": {}, "2": {} },
};
const fixPayloadBefore = JSON.stringify(fixPayload);
const fixResponse = { profile: fixPayload, fixed: [], unresolved: [] };
responses.push(fixResponse);
assert.equal(await client.fixProfile(fixPayload), fixResponse);
assert.deepEqual(calls.at(-1), {
  url: "/easyuse_anima/lora_profiles/fix",
  options: {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(fixPayload),
  },
  argumentCount: 2,
});
assert.equal(JSON.stringify(fixPayload), fixPayloadBefore, "fix must not mutate the payload");

const lorasResponse = { loras: ["a.safetensors"] };
responses.push(lorasResponse);
assert.equal(await client.listLoras(), lorasResponse);
assert.deepEqual(calls.at(-1), {
  url: "/easyuse_anima/loras",
  options: undefined,
  argumentCount: 1,
});

const requestError = new Error("backend unavailable");
responses.push(requestError);
await assert.rejects(
  client.listProfiles(),
  (error) => error === requestError,
  "request errors must propagate without UI policy or fallback",
);

assert.equal(responses.length, 0);
console.log("LoRA preset API client smoke passed.");
