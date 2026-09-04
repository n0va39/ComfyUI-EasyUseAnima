// @ts-check

const JPEG_SCAN_LIMIT_BYTES = 256 * 1024;
const EXIF_VALUE_LIMIT_BYTES = 65_535;
// Native output allows 128 extra_pnginfo keys in addition to prompt and EXIF
// pointer fields, so the reader's bounded directory must leave room for them.
const IFD_ENTRY_LIMIT = 256;
const EXIF_HEADER = Object.freeze([0x45, 0x78, 0x69, 0x66, 0x00, 0x00]);
const TIFF_TYPE_WIDTH = Object.freeze({
  1: 1,
  2: 1,
  3: 2,
  4: 4,
  5: 8,
  7: 1,
  9: 4,
  10: 8,
});
const ASCII_DECODER = new TextDecoder("utf-8");

/**
 * @param {number} length
 * @param {number} offset
 * @param {number} size
 */
function rangeIsValid(length, offset, size) {
  return Number.isSafeInteger(offset)
    && Number.isSafeInteger(size)
    && offset >= 0
    && size >= 0
    && offset <= length - size;
}

/** @param {Uint8Array} value */
function hasExifHeader(value) {
  return EXIF_HEADER.every((byte, index) => value[index] === byte);
}

/**
 * @param {Uint8Array} tiff
 * @returns {{ littleEndian: boolean, view: DataView } | null}
 */
function createTiffReader(tiff) {
  if (tiff.byteLength < 8) return null;
  const littleEndian = tiff[0] === 0x49 && tiff[1] === 0x49;
  const bigEndian = tiff[0] === 0x4d && tiff[1] === 0x4d;
  if (!littleEndian && !bigEndian) return null;
  const view = new DataView(tiff.buffer, tiff.byteOffset, tiff.byteLength);
  if (view.getUint16(2, littleEndian) !== 42) return null;
  return { littleEndian, view };
}

/**
 * @param {Uint8Array} tiff
 * @param {DataView} view
 * @param {boolean} littleEndian
 * @param {number} entryOffset
 * @param {number} type
 * @param {number} count
 */
function readIfdField(tiff, view, littleEndian, entryOffset, type, count) {
  const width = TIFF_TYPE_WIDTH[type];
  if (!width || !Number.isSafeInteger(count)) return null;
  const byteLength = width * count;
  if (byteLength > EXIF_VALUE_LIMIT_BYTES) return null;
  let valueOffset = entryOffset + 8;
  if (byteLength > 4) {
    valueOffset = view.getUint32(entryOffset + 8, littleEndian);
  }
  if (!rangeIsValid(tiff.byteLength, valueOffset, byteLength)) return null;
  return tiff.subarray(valueOffset, valueOffset + byteLength);
}

/** @param {Uint8Array} value */
function decodeAscii(value) {
  let end = value.indexOf(0);
  if (end < 0) end = value.byteLength;
  return ASCII_DECODER.decode(value.subarray(0, end));
}

/** @param {string | undefined} value */
function parseMetadataObject(value) {
  if (value === undefined) return undefined;
  try {
    const parsed = JSON.parse(value);
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return parsed;
    }
  } catch {
    // Malformed metadata delegates to ComfyUI's existing file handler.
  }
  return undefined;
}

/**
 * Parse the bounded TIFF payload emitted by EasyUse's Pillow EXIF writer.
 *
 * @param {Uint8Array} payload
 */
function parseExifPayload(payload) {
  if (payload.byteLength < EXIF_HEADER.length + 8 || !hasExifHeader(payload)) {
    return undefined;
  }
  const tiff = payload.subarray(EXIF_HEADER.length);
  const reader = createTiffReader(tiff);
  if (!reader) return undefined;
  const { littleEndian, view } = reader;
  const ifdOffset = view.getUint32(4, littleEndian);
  if (!rangeIsValid(tiff.byteLength, ifdOffset, 2)) return undefined;
  const entryCount = view.getUint16(ifdOffset, littleEndian);
  if (entryCount > IFD_ENTRY_LIMIT) return undefined;
  const entriesOffset = ifdOffset + 2;
  if (!rangeIsValid(tiff.byteLength, entriesOffset, entryCount * 12)) {
    return undefined;
  }

  let workflowText;
  let promptText;
  for (let index = 0; index < entryCount; index += 1) {
    const entryOffset = entriesOffset + index * 12;
    const type = view.getUint16(entryOffset + 2, littleEndian);
    if (type !== 2) continue;
    const count = view.getUint32(entryOffset + 4, littleEndian);
    const field = readIfdField(
      tiff,
      view,
      littleEndian,
      entryOffset,
      type,
      count,
    );
    if (!field) continue;
    const text = decodeAscii(field);
    const lower = text.toLowerCase();
    if (workflowText === undefined && lower.startsWith("workflow:")) {
      workflowText = text.slice("workflow:".length);
    } else if (promptText === undefined && lower.startsWith("prompt:")) {
      promptText = text.slice("prompt:".length);
    }
  }

  const workflow = parseMetadataObject(workflowText);
  const prompt = parseMetadataObject(promptText);
  if (workflow === undefined && prompt === undefined) return undefined;
  return { workflow, prompt };
}

/** @param {unknown} file */
export function aioIsJpegFile(file) {
  if (!file || typeof file !== "object") return false;
  const candidate = /** @type {{ type?: unknown, name?: unknown }} */ (file);
  const type = String(candidate.type || "").trim().toLowerCase();
  if (type === "image/jpeg" || type === "image/jpg") return true;
  return !type && /\.jpe?g$/i.test(String(candidate.name || ""));
}

/**
 * Parse workflow/prompt metadata from a bounded JPEG prefix.
 *
 * @param {ArrayBuffer | Uint8Array} input
 */
export function aioParseNativeJpegMetadata(input) {
  const source = input instanceof Uint8Array ? input : new Uint8Array(input);
  const bytes = source.subarray(0, JPEG_SCAN_LIMIT_BYTES);
  if (bytes.byteLength < 4 || bytes[0] !== 0xff || bytes[1] !== 0xd8) {
    return undefined;
  }

  let offset = 2;
  while (offset < bytes.byteLength) {
    if (bytes[offset] !== 0xff) return undefined;
    while (offset < bytes.byteLength && bytes[offset] === 0xff) offset += 1;
    if (offset >= bytes.byteLength) return undefined;
    const marker = bytes[offset];
    offset += 1;
    if (marker === 0xd9 || marker === 0xda) return undefined;
    if (marker === 0x01 || (marker >= 0xd0 && marker <= 0xd8)) continue;
    if (!rangeIsValid(bytes.byteLength, offset, 2)) return undefined;
    const segmentLength = (bytes[offset] << 8) | bytes[offset + 1];
    if (segmentLength < 2) return undefined;
    const payloadOffset = offset + 2;
    const segmentEnd = offset + segmentLength;
    if (!rangeIsValid(bytes.byteLength, payloadOffset, segmentLength - 2)) {
      return undefined;
    }
    if (marker === 0xe1) {
      const metadata = parseExifPayload(bytes.subarray(payloadOffset, segmentEnd));
      if (metadata) return metadata;
    }
    offset = segmentEnd;
  }
  return undefined;
}

/**
 * Read at most the bounded prefix required for native JPEG APP1/EXIF data.
 *
 * @param {unknown} file
 */
export async function aioReadNativeJpegMetadata(file) {
  if (!aioIsJpegFile(file)) return undefined;
  const candidate = /** @type {{ size?: unknown, slice?: Function }} */ (file);
  if (typeof candidate.slice !== "function") return undefined;
  const size = Number(candidate.size);
  const end = Number.isFinite(size) && size >= 0
    ? Math.min(size, JPEG_SCAN_LIMIT_BYTES)
    : JPEG_SCAN_LIMIT_BYTES;
  const blob = candidate.slice(0, end);
  if (!blob || typeof blob.arrayBuffer !== "function") return undefined;
  const buffer = await blob.arrayBuffer();
  if (!(buffer instanceof ArrayBuffer) || buffer.byteLength > JPEG_SCAN_LIMIT_BYTES) {
    return undefined;
  }
  return aioParseNativeJpegMetadata(buffer);
}

export const AIO_JPEG_METADATA_LIMITS = Object.freeze({
  scanBytes: JPEG_SCAN_LIMIT_BYTES,
  exifValueBytes: EXIF_VALUE_LIMIT_BYTES,
  ifdEntries: IFD_ENTRY_LIMIT,
});
