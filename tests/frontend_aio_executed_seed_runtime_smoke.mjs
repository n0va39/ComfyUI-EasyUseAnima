import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

const seedModule = await import(dataModule(
  "../web/js/aio/executed_seed_runtime.js",
));

assert.deepEqual(
  Object.keys(seedModule),
  ["aioApplyExecutedSeedDisplay"],
);

{
  const node = {};
  const updates = [];
  assert.equal(seedModule.aioApplyExecutedSeedDisplay(
    node,
    {
      easyuse_anima_aio_seed: [{
        execution_seed: "41",
        next_seed: "42",
      }],
    },
    {
      maximum: 100,
      updateSeed(candidate, seed, options) {
        updates.push([candidate, seed, options]);
      },
    },
  ), true);
  assert.equal(node.__easyuseAnimaLastExecutedSeed, 41);
  assert.deepEqual(updates, [[node, 42, { markDirty: false }]]);
}

{
  const node = {};
  const updates = [];
  assert.equal(seedModule.aioApplyExecutedSeedDisplay(
    node,
    {
      easyuse_anima_aio_seed: [{
        execution_seed: "18446744073709551615",
        next_seed: "100",
      }],
    },
    {
      maximum: 100,
      updateSeed(_candidate, seed) {
        updates.push(seed);
      },
    },
  ), true);
  assert.equal(node.__easyuseAnimaLastExecutedSeed, undefined);
  assert.deepEqual(updates, [100]);
}

{
  const node = {};
  assert.equal(seedModule.aioApplyExecutedSeedDisplay(
    node,
    {
      easyuse_anima_aio_seed: [{
        execution_seed: "7",
        next_seed: "8",
      }],
    },
    {
      maximum: 100,
      updateSeed() {
        throw new Error("disposed panel");
      },
    },
  ), true);
  assert.equal(
    node.__easyuseAnimaLastExecutedSeed,
    7,
    "backend acceptance remains visible after next-seed publication fails",
  );
}

for (const message of [
  null,
  {},
  { easyuse_anima_aio_seed: [] },
  {
    easyuse_anima_aio_seed: [{
      execution_seed: "-1",
      next_seed: "not-a-seed",
    }],
  },
]) {
  assert.equal(seedModule.aioApplyExecutedSeedDisplay(
    {},
    message,
    {
      maximum: 100,
      updateSeed() {
        throw new Error("must not update");
      },
    },
  ), false);
}

console.log("AiO executed seed runtime smoke passed.");
