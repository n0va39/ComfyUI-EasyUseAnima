import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function assertJsonEqual(actual, expected, message) {
  assert(JSON.stringify(actual) === JSON.stringify(expected), message);
}

const preview = await import(dataModule("../web/js/aio/preview.js"));
const {
  aioAppendPreviewFeed,
  aioCreatePreviewProgressTracker,
  aioDefaultPreviewIndex,
  aioDeletePreviewStoreEntry,
  aioMainPreviewImage,
  aioMergePreviewImages,
  aioPreviewEventDetail,
  aioPreviewFileSize,
  aioPreviewImageLabel,
  aioPreviewImageName,
  aioPreviewImages,
  aioPreviewNodeIdsFromDetail,
  aioPreviewResolution,
  aioPreviewRunId,
  aioRemovePreviewRun,
  aioSelectedPreviewIndex,
  aioSuppressDefaultPreview,
  aioTagPreviewRun,
} = preview;

assertJsonEqual(
  aioPreviewNodeIdsFromDetail({
    displayNodeId: " 7:42 ",
    nodeId: 42,
    real_node_id: "42",
    node: "",
  }),
  ["7:42", "42"],
  "Preview node ids must preserve alias order while trimming and deduplicating values",
);

const progress = aioCreatePreviewProgressTracker();
progress.remember({ nodeId: "42", value: "3", max: "10", prompt_id: "job-a" });
assertJsonEqual(
  {
    value: progress.find({ node_id: "42", prompt_id: "job-a" })?.value,
    max: progress.find({ node_id: "42", prompt_id: "job-a" })?.max,
    promptId: progress.find({ node_id: "42", prompt_id: "job-a" })?.promptId,
  },
  { value: 3, max: 10, promptId: "job-a" },
  "Progress lookup must normalize numeric fields and node id aliases",
);
assert(
  progress.find({ nodeId: "42", prompt_id: "job-b" }) === null,
  "Progress from another prompt must not leak into the active preview",
);
progress.rememberState({
  prompt_id: "job-b",
  nodes: {
    first: { display_node_id: "43", value: 5, max: 8 },
    second: { realNodeId: "44", value: "invalid", max: 9, prompt_id: "job-c" },
  },
});
assert(
  progress.find({ nodeId: "43", prompt_id: "job-b" })?.value === 5,
  "Progress-state snapshots must inherit their parent prompt id",
);
assert(
  progress.find({ nodeId: "44", prompt_id: "job-c" })?.value === 0,
  "Invalid progress values must keep the existing zero fallback",
);
progress.remember({ nodeId: "42", value: 7, max: 10, prompt_id: "job-b" });
assert(
  progress.find({ nodeId: "42", prompt_id: "job-a" }) === null
    && progress.find({ nodeId: "42", prompt_id: "job-b" })?.value === 7,
  "The latest prompt for a node must replace stale progress without cross-prompt matches",
);
progress.clear();
assert(
  progress.find({ nodeId: "42", prompt_id: "job-b" }) === null,
  "Clearing progress must remove every cached node entry",
);

const firstImage = { stage: "first_pass", filename: "first.webp", type: "temp" };
const finalImage = { stage: "final", filename: "final.webp", type: "output" };
assertJsonEqual(
  aioPreviewImages({
    easyuse_anima_preview: [firstImage, [finalImage, null], "invalid", null, []],
  }),
  [firstImage, finalImage],
  "Preview payloads must flatten one nested image array and filter invalid entries",
);
assertJsonEqual(aioPreviewImages({}), [], "Missing preview payloads must normalize to an empty list");
assert(
  aioPreviewRunId({ easyuse_anima_run_id: ["run-primary"], run_id: "run-fallback" })
    === "run-primary",
  "The EasyUseAnima run id must retain precedence and first-value normalization",
);
assert(
  aioPreviewRunId({ run_id: 17 }) === "17",
  "Fallback run ids must normalize to strings",
);

const imagesToTag = [
  { filename: "a.webp" },
  { filename: "b.webp", __aio_run_id: "kept", __aio_run_index: 9 },
];
const imagesToTagSnapshot = JSON.stringify(imagesToTag);
const tagged = aioTagPreviewRun(imagesToTag, "run-tagged", 4);
assertJsonEqual(
  tagged.map((image) => [image.__aio_run_id, image.__aio_run_index]),
  [["run-tagged", 4], ["kept", 9]],
  "Run tagging must add stable ids and indexes without replacing existing tags",
);
assert(
  JSON.stringify(imagesToTag) === imagesToTagSnapshot,
  "Run tagging must not mutate its input images",
);

const existingImages = [
  {
    stage: "first_pass",
    filename: "first.webp",
    type: "temp",
    subfolder: "",
    width: 512,
    __aio_run_id: "run-old",
    __aio_run_index: 0,
  },
  { stage: "highres", filename: "high.webp", type: "temp", subfolder: "" },
];
const nextImages = [
  {
    stage: "first_pass",
    filename: "first.webp",
    type: "temp",
    subfolder: "",
    width: 768,
    bytes: 2048,
  },
  { stage: "final", filename: "final.webp", type: "output", subfolder: "" },
];
const existingSnapshot = JSON.stringify(existingImages);
const nextSnapshot = JSON.stringify(nextImages);
const merged = aioMergePreviewImages(existingImages, nextImages, "run-new");
assert(merged.length === 3, "Duplicate preview identities must merge instead of appending");
assert(
  merged[0].width === 768 && merged[0].bytes === 2048,
  "New preview metadata must update an existing matching image",
);
assert(
  merged[2].stage === "final",
  "New unique preview images must retain their append order",
);
assert(
  JSON.stringify(existingImages) === existingSnapshot && JSON.stringify(nextImages) === nextSnapshot,
  "Preview merging must not mutate either input list",
);
assertJsonEqual(
  aioMergePreviewImages([], [{ filename: "1" }, { filename: "2" }, { filename: "3" }], "run", 2)
    .map((image) => image.filename),
  ["2", "3"],
  "Limited preview merges must retain the most recent images",
);
assert(
  aioMergePreviewImages([], [{}, {}], "run").length === 2,
  "Images without an identity must not collapse into one entry",
);
assertJsonEqual(
  aioAppendPreviewFeed(
    [],
    [{ filename: "1" }, { filename: "2" }, { filename: "3" }],
    { preview: { feed_count: 2 } },
    "run",
    9,
  ).map((image) => image.filename),
  ["2", "3"],
  "Preview feeds must honor the configured history limit",
);

const multipleRuns = [
  { filename: "old.webp", __aio_run_id: "old" },
  { filename: "current.webp", __aio_run_id: "current" },
];
assertJsonEqual(
  aioRemovePreviewRun(multipleRuns, "old"),
  [multipleRuns[1]],
  "Removing a preview run must preserve images from every other run",
);
const replacedCurrentRunFeed = aioAppendPreviewFeed(
  aioRemovePreviewRun(
    [
      { filename: "old-run.webp", __aio_run_id: "old" },
      { filename: "stale-current.webp", __aio_run_id: "current" },
    ],
    "current",
  ),
  [{ filename: "fresh-current.webp", stage: "final" }],
  { preview: { feed_count: 4 } },
  "current",
);
assertJsonEqual(
  replacedCurrentRunFeed.map((image) => image.filename),
  ["old-run.webp", "fresh-current.webp"],
  "Replacing one run must preserve prior feed history while removing stale images from that run",
);

const selectableImages = [
  { stage: "final", filename: "old-final.webp" },
  { stage: "highres", filename: "high.webp" },
  { stage: "final", filename: "new-final.webp" },
];
assert(
  aioDefaultPreviewIndex(selectableImages) === 2,
  "The newest final image must be the default preview",
);
assert(
  aioDefaultPreviewIndex([{ stage: "first" }, { stage: "highres" }]) === 1
    && aioDefaultPreviewIndex([]) === -1,
  "Preview selection must fall back to the last image or -1 for an empty list",
);
assert(
  aioSelectedPreviewIndex({ __easyuseAnimaSelectedPreviewIndex: 1 }, selectableImages) === 1,
  "A valid explicit preview selection must take precedence",
);
assert(
  aioSelectedPreviewIndex({ __easyuseAnimaSelectedPreviewIndex: 99 }, selectableImages) === 2,
  "An invalid explicit selection must fall back to the default final image",
);
assert(
  aioMainPreviewImage({ __easyuseAnimaSelectedPreviewIndex: 1 }, selectableImages)
    === selectableImages[1]
    && aioMainPreviewImage({}, []) === null,
  "Main preview lookup must return the selected image or null",
);

const wrappedDetail = { node: "42", images: [finalImage] };
assert(
  aioPreviewEventDetail({ detail: { data: wrappedDetail } }) === wrappedDetail,
  "Wrapped event payloads must expose their nested data object",
);
assertJsonEqual(
  aioPreviewEventDetail({ detail: { node: "42" } }),
  { node: "42" },
  "Plain event details must pass through unchanged",
);
assert(aioPreviewImageLabel({ label: "Result", stage: "final" }) === "Result", "Explicit labels must win");
assert(aioPreviewImageLabel({ stage: "final" }) === "final", "Stages must remain label fallbacks");
assert(aioPreviewImageName({ name: "named.webp" }) === "named.webp", "Image names must remain supported");
assert(
  aioPreviewResolution({ width: 1024.9, height: 1536.7 }) === "1024 x 1536"
    && aioPreviewResolution({ width: 0, height: 1536 }) === "-",
  "Preview resolution formatting must truncate valid dimensions and reject incomplete sizes",
);
assert(
  aioPreviewFileSize({ bytes: 1536 }) === "1.5 KB"
    && aioPreviewFileSize({ size: 12 * 1024 }) === "12 KB"
    && aioPreviewFileSize({ bytes: 0 }) === "-",
  "Preview file sizes must retain binary-unit formatting and empty fallbacks",
);

const mapStore = new Map([["map-node", true]]);
aioDeletePreviewStoreEntry(mapStore, "map-node");
assert(!mapStore.has("map-node"), "Preview store deletion must support Map containers");
const refMapStore = { value: new Map([["ref-map-node", true]]) };
aioDeletePreviewStoreEntry(refMapStore, "ref-map-node");
assert(!refMapStore.value.has("ref-map-node"), "Preview store deletion must support ref-wrapped Maps");
const objectStore = { "object-node": true };
aioDeletePreviewStoreEntry(objectStore, "object-node");
assert(!Object.hasOwn(objectStore, "object-node"), "Preview store deletion must support plain objects");
const refObjectStore = { value: { "ref-object-node": true } };
aioDeletePreviewStoreEntry(refObjectStore, "ref-object-node");
assert(
  !Object.hasOwn(refObjectStore.value, "ref-object-node"),
  "Preview store deletion must support ref-wrapped objects",
);

const dirtyNodes = [];
const legacyNode = {
  imgs: [{ src: "native" }],
  images: [{ src: "native" }],
  imageRects: [{ x: 0 }],
  imageIndex: 2,
  overIndex: 1,
  previewMediaType: "image",
};
const changed = aioSuppressDefaultPreview(legacyNode, {
  markNodeDirty(node) {
    dirtyNodes.push(node);
  },
});
assert(changed === true, "The first native preview suppression must report a state change");
assert(legacyNode.hideOutputImages === true, "Native output images must remain hidden");
assert(
  legacyNode.imgs.length === 0
    && legacyNode.images.length === 0
    && legacyNode.imageRects.length === 0,
  "Every native preview image collection must be empty",
);
assert(
  legacyNode.imageIndex === null
    && legacyNode.overIndex === null
    && legacyNode.previewMediaType === undefined,
  "Native preview selection and media state must be cleared",
);
assert(dirtyNodes.length === 1 && dirtyNodes[0] === legacyNode, "Changed nodes must be marked dirty once");
legacyNode.imgs = [{ src: "late-native" }];
assert(
  legacyNode.imgs.length === 0,
  "The legacy canvas lock must reject ComfyUI's later node.imgs assignment",
);
const imgsDescriptor = Object.getOwnPropertyDescriptor(legacyNode, "imgs");
assert(
  imgsDescriptor?.configurable === true && imgsDescriptor?.enumerable === false,
  "The legacy imgs lock must retain its configurable non-enumerable descriptor",
);
assert(
  aioSuppressDefaultPreview(legacyNode, { markNodeDirty: () => dirtyNodes.push(legacyNode) }) === false
    && dirtyNodes.length === 1,
  "Repeated suppression must be idempotent and avoid redundant dirty updates",
);
let disabledDirtyCalls = 0;
const quietNode = {};
assert(
  aioSuppressDefaultPreview(quietNode, {
    markDirty: false,
    markNodeDirty() {
      disabledDirtyCalls += 1;
    },
  }) === true
    && disabledDirtyCalls === 0,
  "markDirty false must preserve setup-time suppression without canvas invalidation",
);
assert(aioSuppressDefaultPreview(null) === false, "Missing nodes must be a safe no-op");

console.log("AiO preview core smoke passed.");
