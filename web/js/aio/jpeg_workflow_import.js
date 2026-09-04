// @ts-check

import {
  aioIsJpegFile,
  aioReadNativeJpegMetadata,
} from "./jpeg_workflow_metadata.js";

const JPEG_IMPORT_MARKER = Symbol.for("easyuse-anima.jpeg-workflow-import");

/** @param {unknown} value */
function supportsJpegMime(value) {
  if (Array.isArray(value)) return value.includes("image/jpeg");
  if (value instanceof Set) return value.has("image/jpeg");
  if (value && typeof value === "object") {
    const candidate = /** @type {{ has?: Function, includes?: Function }} */ (value);
    if (typeof candidate.has === "function") return Boolean(candidate.has("image/jpeg"));
    if (typeof candidate.includes === "function") {
      return Boolean(candidate.includes("image/jpeg"));
    }
  }
  return false;
}

/**
 * Detect an explicit host JPEG metadata capability without importing private
 * ComfyUI frontend modules.
 *
 * @param {unknown} app
 * @param {unknown} globalObject
 */
export function aioHostSupportsNativeJpegMetadata(app, globalObject = globalThis) {
  try {
    const root = /** @type {{ comfyAPI?: { pnginfo?: Record<string, unknown> } }} */ (
      globalObject
    );
    if (typeof root.comfyAPI?.pnginfo?.getJpegMetadata === "function") return true;
    const candidate = /** @type {{ handleFile?: Function }} */ (app || {});
    const handleFile = /** @type {(Function & {
     *   supportedMetadataMimeTypes?: unknown,
     * }) | undefined} */ (candidate.handleFile);
    return supportsJpegMime(handleFile?.supportedMetadataMimeTypes);
  } catch {
    return false;
  }
}

/** @param {unknown} value */
function metadataObject(value) {
  return value && typeof value === "object" && !Array.isArray(value);
}

/** @param {unknown} value */
function apiPromptObject(value) {
  if (!metadataObject(value)) return false;
  const nodes = Object.values(value);
  return nodes.length > 0 && nodes.every((node) => {
    if (!metadataObject(node)) return false;
    const candidate = /** @type {{ class_type?: unknown, inputs?: unknown }} */ (node);
    return typeof candidate.class_type === "string"
      && metadataObject(candidate.inputs);
  });
}

/** @param {unknown} file */
function workflowName(file) {
  const name = String(
    /** @type {{ name?: unknown }} */ (file && typeof file === "object" ? file : {}).name
      || "",
  );
  return name.replace(/\.\w+$/, "");
}

/**
 * Install a chain-preserving JPEG handler around the current ComfyUI handler.
 *
 * @param {unknown} app
 * @param {{
 *   globalObject?: unknown,
 *   readMetadata?: typeof aioReadNativeJpegMetadata,
 *   logger?: Pick<Console, "warn">,
 * }} [dependencies]
 */
export function aioInstallJpegWorkflowImport(app, dependencies = {}) {
  const host = /** @type {{
   *   handleFile?: Function,
   *   loadGraphData?: Function,
   *   loadApiJson?: Function,
   * }} */ (app || {});
  const previous = host.handleFile;
  if (
    typeof previous !== "function"
    || previous[JPEG_IMPORT_MARKER]
    || aioHostSupportsNativeJpegMetadata(host, dependencies.globalObject)
  ) {
    return false;
  }

  const readMetadata = dependencies.readMetadata || aioReadNativeJpegMetadata;
  const logger = dependencies.logger || console;
  const globalObject = dependencies.globalObject ?? globalThis;

  async function easyuseJpegHandleFile(file, ...args) {
    const delegate = () => Reflect.apply(previous, this, [file, ...args]);
    if (
      !aioIsJpegFile(file)
      || aioHostSupportsNativeJpegMetadata({ handleFile: previous }, globalObject)
    ) {
      return delegate();
    }

    let metadata;
    try {
      metadata = await readMetadata(file);
    } catch (error) {
      logger.warn("[EasyUseAnima] JPEG workflow metadata could not be read.", error);
      return delegate();
    }
    if (!metadata || typeof metadata !== "object") return delegate();

    const receiver = this && typeof this === "object" ? this : host;
    const openSource = args[0];
    const options = args[1];
    const deferWarnings = options && typeof options === "object"
      ? options.deferWarnings
      : undefined;
    const name = workflowName(file);
    if (metadataObject(metadata.workflow) && typeof receiver.loadGraphData === "function") {
      try {
        return await Reflect.apply(receiver.loadGraphData, receiver, [
          metadata.workflow,
          true,
          true,
          name,
          { openSource, deferWarnings },
        ]);
      } catch (error) {
        logger.warn(
          "[EasyUseAnima] JPEG workflow could not be loaded; trying prompt fallback.",
          error,
        );
      }
    }
    if (apiPromptObject(metadata.prompt) && typeof receiver.loadApiJson === "function") {
      try {
        return await Reflect.apply(receiver.loadApiJson, receiver, [
          metadata.prompt,
          name,
          { deferWarnings },
        ]);
      } catch (error) {
        logger.warn(
          "[EasyUseAnima] JPEG API prompt could not be loaded; delegating to ComfyUI.",
          error,
        );
      }
    }
    return delegate();
  }

  Object.defineProperty(easyuseJpegHandleFile, JPEG_IMPORT_MARKER, {
    value: true,
  });
  host.handleFile = easyuseJpegHandleFile;
  return true;
}
