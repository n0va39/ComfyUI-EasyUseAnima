// @ts-check

/** Move the pre-release metadata node's trailing workflow controls to each saver.
 * @param {any} graph
 */
export function migrateImageOutputWorkflow(graph) {
  if (!Array.isArray(graph?.nodes)) return;
  const nodes = new Map(graph.nodes.map((node) => [String(node.id), node]));
  const legacyOptions = new Map();
  for (const node of graph.nodes) {
    if (node.type !== "EasyUseAnimaImageMetadata") continue;
    const values = node.widgets_values;
    if (Array.isArray(values) && values.length === 13
      && typeof values[11] === "boolean" && typeof values[12] === "boolean") {
      legacyOptions.set(String(node.id), values.slice(11));
      node.widgets_values = values.slice(0, 11);
    }
  }
  for (const node of graph.nodes) {
    if (node.type !== "EasyUseAnimaSaveImage"
      || !Array.isArray(node.widgets_values) || node.widgets_values.length !== 6) continue;
    const input = node.inputs?.find((entry) => entry.name === "exif_metadata");
    const link = graph.links?.find((entry) => String(Array.isArray(entry) ? entry[0] : entry.id) === String(input?.link));
    const origin = link && String(Array.isArray(link) ? link[1] : link.origin_id);
    // A disconnected old saver saved pixels only, even when a workflow was queued.
    const options = origin && nodes.has(origin) ? legacyOptions.get(origin) : null;
    node.widgets_values.push(...(options ?? [false, false]));
  }
  for (const subgraph of graph.definitions?.subgraphs ?? []) {
    migrateImageOutputWorkflow(subgraph);
  }
}
