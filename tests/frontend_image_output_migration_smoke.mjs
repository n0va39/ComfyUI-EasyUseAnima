import assert from "node:assert/strict";
import { migrateImageOutputWorkflow } from "../web/js/image_output/workflow_migration.js";

const metadata = (id, embed, sidecar) => ({
  id, type: "EasyUseAnimaImageMetadata",
  widgets_values: ["positive", "negative", "model", 42, 20, 7, "euler", "normal", 1, 0, "custom", embed, sidecar],
});
const saver = (id, link) => ({
  id, type: "EasyUseAnimaSaveImage", widgets_values: ["album", "test", "png", 95, false, false],
  inputs: [{ name: "images", link: null }, { name: "exif_metadata", link }],
});
for (const objectLinks of [false, true]) {
  const graph = {
    nodes: [metadata(1, false, true), saver(2, 11), saver(3, 12), saver(4, null)],
    links: objectLinks
      ? [{ id: 11, origin_id: 1, target_id: 2 }, { id: 12, origin_id: 1, target_id: 3 }]
      : [[11, 1, 0, 2, 1, "EASYUSE_IMAGE_METADATA"], [12, 1, 0, 3, 1, "EASYUSE_IMAGE_METADATA"]],
  };
  const originalPrefix = graph.nodes[0].widgets_values.slice(0, 11);
  migrateImageOutputWorkflow(graph);
  assert.deepEqual(graph.nodes[0].widgets_values, originalPrefix);
  assert.deepEqual(graph.nodes[1].widgets_values.slice(6), [false, true]);
  assert.deepEqual(graph.nodes[2].widgets_values.slice(6), [false, true]);
  assert.deepEqual(graph.nodes[3].widgets_values.slice(6), [false, false]);
  const migrated = structuredClone(graph);
  migrateImageOutputWorkflow(graph);
  assert.deepEqual(graph, migrated);
}
const current = saver(2, 11);
current.widgets_values.push(true, false);
const subgraph = { nodes: [metadata(1, false, true), current], links: [[11, 1, 0, 2, 1, "EASYUSE_IMAGE_METADATA"]] };
migrateImageOutputWorkflow({ nodes: [], definitions: { subgraphs: [subgraph] } });
assert.deepEqual(current.widgets_values.slice(6), [true, false]);
assert.equal(subgraph.nodes[0].widgets_values.length, 11);
console.log("Image output workflow migration smoke passed.");
