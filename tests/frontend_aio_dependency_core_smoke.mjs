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

const dependencies = await import(dataModule("../web/js/aio/dependencies.js"));
const {
  AIO_BACKEND_DEPENDENCIES,
  AIO_OPTIONAL_DEPENDENCY_SPECS,
  aioNodeInputMap,
  aioNodeInputSpec,
  aioNodeInputSupported,
  aioNodeInputTooltip,
  aioOptionalDependencyAvailable,
  aioOptionalDependencyPack,
  aioOptionalDependencyStatus,
  aioQueryOptionalDependencies,
  aioUpscaleBackendDependencyKeys,
  aioUpscaleBackendMissingPacks,
} = dependencies;

assert(
  AIO_BACKEND_DEPENDENCIES.spectrum_mod_guidance_advanced === "spectrumAdvanced",
  "Spectrum Mod Guidance must keep its optional-dependency mapping",
);
assert(
  AIO_OPTIONAL_DEPENDENCY_SPECS.imageSaver.nodeId === "Image Saver",
  "The Image Saver object-info node id must remain stable",
);
assert(
  AIO_OPTIONAL_DEPENDENCY_SPECS.checkpointLoader.nodeId === "CheckpointLoaderSimple",
  "SAM3 choices must use the built-in checkpoint loader object-info catalog",
);

const queriedSpecs = {
  present: { nodeId: "PresentNode", pack: "Present Pack" },
  absent: { nodeId: "AbsentNode", pack: "Absent Pack" },
  broken: { nodeId: "BrokenNode", pack: "Broken Pack" },
};
const queriedSpecsSnapshot = JSON.stringify(queriedSpecs);
const presentInfo = {
  input: {
    required: {
      mode: [["fast", "quality"], { tooltip: "Required mode" }],
      shared: ["INT", { tooltip: "Required shared" }],
    },
    optional: {
      strength: ["FLOAT", { tooltip: "Optional strength" }],
      shared: ["STRING", { tooltip: "Optional shared" }],
    },
  },
};
const queryCalls = [];
let activeQueries = 0;
let maxConcurrentQueries = 0;
const queryResult = await aioQueryOptionalDependencies(
  queriedSpecs,
  async (spec, key) => {
    queryCalls.push([key, spec.nodeId]);
    activeQueries += 1;
    maxConcurrentQueries = Math.max(maxConcurrentQueries, activeQueries);
    await Promise.resolve();
    activeQueries -= 1;
    if (key === "present") {
      return presentInfo;
    }
    if (key === "absent") {
      return null;
    }
    throw new Error("object-info unavailable");
  },
);

assert(queryCalls.length === 3, "Every optional dependency must be queried once");
assert(maxConcurrentQueries === 1, "Optional dependencies must keep sequential object-info queries");
assert(queryResult.status.present === "available", "Returned node info must be available");
assert(queryResult.available.present === true, "Available results must set the boolean cache");
assert(queryResult.nodeInfo.present === presentInfo, "Available node info must be preserved");
assert(queryResult.status.absent === "missing", "Null node info must be missing");
assert(queryResult.available.absent === false, "Missing results must set the boolean cache");
assert(queryResult.nodeInfo.absent === null, "Missing node info must normalize to null");
assert(queryResult.status.broken === "error", "Query failures must remain error states");
assert(queryResult.nodeInfo.broken === null, "Failed node info must normalize to null");
assert(
  queryResult.errors.broken === "object-info unavailable",
  "Query failure messages must be preserved",
);
assert(
  !Object.prototype.hasOwnProperty.call(queryResult.available, "broken"),
  "Query failures must not be cached as missing",
);
assert(
  JSON.stringify(queriedSpecs) === queriedSpecsSnapshot,
  "Dependency queries must not mutate their specs",
);

const capabilityState = {
  loaded: true,
  status: {
    present: "available",
    absent: "missing",
    broken: "error",
    ultimateSdUpscale: "missing",
    upscaleModelLoader: "error",
    resShiftLoader: "available",
    resShiftUpscale: "missing",
  },
  nodeInfo: { present: presentInfo },
};
const capabilityStateSnapshot = JSON.stringify(capabilityState);

assert(
  aioOptionalDependencyStatus({ loaded: false, status: { present: "available" } }, "present")
    === "unknown",
  "Dependencies must remain unknown before the query cache is loaded",
);
assert(
  aioOptionalDependencyStatus(capabilityState, "unregistered") === "unknown",
  "Unregistered dependency keys must remain unknown",
);
assert(
  aioOptionalDependencyAvailable(capabilityState, "present") === true,
  "Available dependencies must remain enabled",
);
assert(
  aioOptionalDependencyAvailable(capabilityState, "absent") === false,
  "Only confirmed-missing dependencies may be disabled",
);
assert(
  aioOptionalDependencyAvailable(capabilityState, "broken") === true,
  "Query failures must not be treated as missing dependencies",
);
assert(
  aioOptionalDependencyAvailable({ loaded: false, status: {} }, "present") === true,
  "Unknown dependency state must keep settings available until queried",
);

assert(
  aioOptionalDependencyPack("imageSaver") === "ComfyUI-Image-Saver",
  "Known dependencies must expose their pack label",
);
assert(
  aioOptionalDependencyPack("custom", queriedSpecs) === "custom",
  "Unknown dependencies must fall back to their key",
);
assert(aioOptionalDependencyPack("") === "", "Empty dependency keys must stay empty");

assert(
  JSON.stringify(aioUpscaleBackendDependencyKeys("usdu"))
    === JSON.stringify(["ultimateSdUpscale", "upscaleModelLoader"]),
  "USDU must keep both runtime dependencies",
);
assert(
  JSON.stringify(aioUpscaleBackendDependencyKeys("resshift"))
    === JSON.stringify(["resShiftLoader", "resShiftUpscale"]),
  "ResShift must keep both runtime dependencies",
);
assert(
  aioUpscaleBackendDependencyKeys("unknown").length === 0,
  "Unknown upscale backends must have no dependency keys",
);
assert(
  JSON.stringify(aioUpscaleBackendMissingPacks(capabilityState, "usdu"))
    === JSON.stringify(["ComfyUI_UltimateSDUpscale"]),
  "USDU must report confirmed-missing packs without treating query errors as missing",
);
assert(
  JSON.stringify(aioUpscaleBackendMissingPacks(capabilityState, "resshift"))
    === JSON.stringify(["ComfyUI-Distilled-ResShift"]),
  "ResShift must report the pack for its confirmed-missing node",
);

const inputMap = aioNodeInputMap(capabilityState, "present");
assert(inputMap.mode === presentInfo.input.required.mode, "Required inputs must be exposed");
assert(inputMap.strength === presentInfo.input.optional.strength, "Optional inputs must be exposed");
assert(
  inputMap.shared === presentInfo.input.optional.shared,
  "Optional input metadata must retain the existing override order",
);
assert(
  aioNodeInputSpec(capabilityState, "present", "mode") === presentInfo.input.required.mode,
  "Known input specs must be returned unchanged",
);
assert(
  aioNodeInputSpec(capabilityState, "present", "missing") === null,
  "Unknown input specs must resolve to null",
);
assert(
  aioNodeInputTooltip(capabilityState, "present", "mode") === "Required mode",
  "Object-info tooltips must be exposed",
);
assert(
  aioNodeInputTooltip(capabilityState, "present", "missing") === "",
  "Inputs without metadata must have an empty tooltip",
);
assert(
  aioNodeInputSupported(capabilityState, "present", "mode") === true,
  "Available declared inputs must be supported",
);
assert(
  aioNodeInputSupported(capabilityState, "present", "missing") === false,
  "Available nodes must reject undeclared inputs",
);
assert(
  aioNodeInputSupported(capabilityState, "absent", "mode") === false,
  "Missing nodes must reject all inputs",
);
assert(
  aioNodeInputSupported(capabilityState, "broken", "mode") === true,
  "Query errors must preserve optimistic input support",
);
assert(
  aioNodeInputSupported({ loaded: false, status: {}, nodeInfo: {} }, "present", "mode")
    === true,
  "Unknown nodes must preserve optimistic input support",
);
assert(
  JSON.stringify(capabilityState) === capabilityStateSnapshot,
  "Capability helpers must not mutate dependency state",
);

console.log("AiO dependency core smoke passed.");
