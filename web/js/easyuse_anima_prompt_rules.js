const PONY_SCORE_TAG_RE = /^score[\s_]+(\d+)(:?)$/i;
const INLINE_SPACE_RE = /[ \t]+/g;

export function normalizePromptTagText(value, options = {}) {
  const unescapePattern = options.unescapeAll ? /\\(.)/g : /\\([()])/g;
  const text = String(value ?? "")
    .normalize("NFKC")
    .replace(unescapePattern, "$1")
    .replace(INLINE_SPACE_RE, " ")
    .trim();
  const ponyScore = PONY_SCORE_TAG_RE.exec(text);
  if (ponyScore) {
    return `score_${ponyScore[1]}${ponyScore[2] || ""}`;
  }
  return text.replaceAll("_", " ");
}

export function promptCompletionTagText(value) {
  return normalizePromptTagText(value).replace(/[()]/g, "\\$&");
}
