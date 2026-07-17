import { readFileSync } from "node:fs";

function dataModule(relativePath, replacements = {}) {
  let source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  for (const [specifier, replacement] of Object.entries(replacements)) {
    source = source.replaceAll(`"${specifier}"`, `"${replacement}"`);
  }
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

const constantsUrl = dataModule("../web/js/prompt_studio/regional/constants.js");
const maskGeometryUrl = dataModule("../web/js/prompt_studio/regional/mask_geometry.js");
const resolutionUrl = dataModule("../web/js/prompt_studio/regional/resolution.js", {
  "./constants.js": constantsUrl,
});
const schemaUrl = dataModule("../web/js/prompt_studio/regional/schema.js", {
  "./constants.js": constantsUrl,
  "./mask_geometry.js": maskGeometryUrl,
  "./resolution.js": resolutionUrl,
});
const serializationUrl = dataModule("../web/js/prompt_studio/regional/serialization.js", {
  "./constants.js": constantsUrl,
  "./schema.js": schemaUrl,
});

const constants = await import(constantsUrl);
const geometry = await import(maskGeometryUrl);
const resolution = await import(resolutionUrl);
const schema = await import(schemaUrl);
const serialization = await import(serializationUrl);

assert(constants.REGIONAL_WIDGET_INDEX.regional_config === 1, "Regional widget order changed");
assert(constants.PROMPT_STUDIO_VARIANT_FIELD_TYPES.join(",") === "quality,artist,trigger,general", "Regional field type order changed");

assert(resolution.ratioLabel(1024, 1536) === "2:3", "Resolution ratio label changed");
assert(resolution.resolutionOptions("1024").includes("896 * 1152 (7:9)"), "1024 resolution options changed");
assert(resolution.normalizeResolutionBucket("unknown") === "1024", "Resolution bucket fallback changed");
assert(resolution.normalizeResolutionSize("1024", "896 * 1152 (7:9)") === "896 * 1152 (7:9)", "Resolution size normalization changed");
assert(resolution.snapResolution32(1000) === 992, "32-pixel resolution snapping changed");
assert(
  JSON.stringify(resolution.readRegionalResolutionValues({
    bucket: "1024",
    size: "896 * 1152 (7:9)",
    customWidth: 1024,
    customHeight: 1024,
  })) === JSON.stringify({ width: 896, height: 1152 }),
  "Bucket resolution reading changed",
);
assert(
  JSON.stringify(resolution.readRegionalResolutionValues({
    bucket: "Custom",
    size: "896 * 1152 (7:9)",
    customWidth: 1000,
    customHeight: 777,
  })) === JSON.stringify({ width: 1000, height: 777 }),
  "Custom resolution reading changed",
);

assert(
  JSON.stringify(schema.normalizeRegionalConditioningWidgetValues(["default", "0.35"]))
    === JSON.stringify([0.35, "default"]),
  "Regional conditioning widget migration changed",
);
assert(schema.createDefaultRegionalFields().length === 5, "Default Regional fields changed");
const positiveField = schema.normalizeRegionalField({
  pane: "positive",
  type: "unknown",
  height: 12,
  enabled: "false",
  mask_ids: "2, 2; -1 3",
});
assert(positiveField.type === "general", "Unknown Regional field type fallback changed");
assert(positiveField.height === 36, "Regional field minimum height changed");
assert(positiveField.enabled === false, "Regional field boolean normalization changed");
assert(JSON.stringify(positiveField.mask_ids) === JSON.stringify([2, 3]), "Regional mask id normalization changed");
const negativeField = schema.normalizeRegionalField({ pane: "negative", type: "trigger", mask_ids: [1] });
assert(negativeField.type === "general", "Negative trigger migration changed");
assert(negativeField.mask_ids.length === 0, "Negative mask assignment filtering changed");

const migratedConfig = schema.normalizeRegionalConfig({
  regions: [
    { id: 2, color: "#abcdef", geometry: { type: "ellipse", x: 0.9, y: -1, width: 0.5, height: 2 } },
    { id: 2, geometry: { x: 0.1, y: 0.1, width: 0.2, height: 0.2 } },
    { id: 0 },
  ],
  mask_authoring: { preview_enabled: false },
  artist_mix: { mode: "hybrid" },
}, { width: 640, height: 480 });
assert(migratedConfig.canvas.width === 640 && migratedConfig.canvas.height === 480, "Regional canvas resolution changed");
assert(migratedConfig.canvas.aspect_ratio === "4:3", "Regional canvas aspect ratio changed");
assert(migratedConfig.masks.length === 1 && migratedConfig.masks[0].mask_id === 2, "Region-to-mask migration changed");
assert(migratedConfig.masks[0].geometry.width === 0.1, "Mask geometry boundary clamp changed");
assert(migratedConfig.next_mask_id === 3, "Next mask id migration changed");
assert(migratedConfig.mask_authoring.preview_enabled === false, "Mask authoring settings migration changed");
assert(migratedConfig.mask_authoring.storage_space === "normalized_canvas", "Mask authoring defaults changed");

const normalizedRect = geometry.normalizeGeometry({ type: "rect", x: -1, y: 0.2, width: 0.25, height: 0.3 });
assert(normalizedRect.x === 0 && normalizedRect.width === 0.25, "Rectangle normalization changed");
const ellipse = geometry.normalizeGeometry({ type: "ellipse", x: 0.2, y: 0.2, width: 0.4, height: 0.4 });
assert(geometry.maskContainsPoint(ellipse, { x: 0.4, y: 0.4 }), "Ellipse center hit-test changed");
assert(!geometry.maskContainsPoint(ellipse, { x: 0.2, y: 0.2 }), "Ellipse corner hit-test changed");
assert(geometry.hitTestMaskHandle(ellipse, { x: 0.2, y: 0.2 }) === "nw", "Mask handle hit-test changed");
const moved = geometry.moveGeometry({ type: "rect", x: 0.2, y: 0.2, width: 0.3, height: 0.3 }, 1, 1);
assert(moved.x === 0.7 && moved.y === 0.7, "Mask movement boundary changed");
const resized = geometry.resizeGeometry({ type: "rect", x: 0.2, y: 0.2, width: 0.3, height: 0.3 }, "nw", 1, 1);
assert(resized.width >= 0.01 && resized.height >= 0.01, "Mask resize minimum changed");

const propertyFields = JSON.stringify([{ id: "property", pane: "positive", type: "general" }]);
const widgetFields = JSON.stringify([{ id: "widget", pane: "positive", type: "general" }]);
const selectedFields = serialization.serializedRegionalValue({
  properties: { easyuse_anima_regional_fields: propertyFields },
  widgets_values: [widgetFields],
}, "regional_fields");
assert(JSON.parse(selectedFields)[0].id === "property", "Serialized Regional property precedence changed");
const selectedConfig = serialization.serializedRegionalValue({
  properties: { easyuse_anima_regional_config: JSON.stringify({ regions: [{ id: 4 }] }) },
  widgets_values: [],
}, "regional_config", { width: 800, height: 600 });
assert(JSON.parse(selectedConfig).canvas.aspect_ratio === "4:3", "Serialized Regional config normalization changed");
assert(JSON.parse(selectedConfig).masks[0].mask_id === 4, "Serialized Regional config migration changed");
assert(
  serialization.normalizeRegionalFieldsString(selectedFields)
    === selectedFields,
  "Regional field save/reload normalization changed",
);
assert(
  serialization.normalizeRegionalConfigString(selectedConfig, { width: 800, height: 600 })
    === selectedConfig,
  "Regional config save/reload normalization changed",
);

console.log("Regional pure data smoke passed.");
