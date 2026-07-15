// @ts-check

const SENTENCE_PERIODS = new Set([".", "。", "．", "｡"]);

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function isEscaped(value, index) {
  let count = 0;
  for (let cursor = index - 1; cursor >= 0 && value[cursor] === "\\"; cursor -= 1) {
    count += 1;
  }
  return count % 2 === 1;
}

function isSentencePeriod(value, index) {
  if (!SENTENCE_PERIODS.has(value[index]) || isEscaped(value, index)) {
    return false;
  }
  return !(/\d/.test(value[index - 1] || "") && /\d/.test(value[index + 1] || ""));
}

function naturalSentenceStart(value, segmentStart, caret, detectNaturalSentences) {
  if (!detectNaturalSentences) {
    return segmentStart;
  }
  for (let index = caret - 1; index >= segmentStart; index -= 1) {
    if (!isSentencePeriod(value, index)) {
      continue;
    }
    let start = index + 1;
    while (start < caret && /[ \t]/.test(value[start])) {
      start += 1;
    }
    return start < caret ? start : segmentStart;
  }
  return segmentStart;
}

function naturalSentenceEnd(value, caret, segmentEnd) {
  for (let index = caret; index < segmentEnd; index += 1) {
    if (isSentencePeriod(value, index)) {
      return index;
    }
  }
  return segmentEnd;
}

function trimPromptSyntaxPrefix(value, start, end) {
  let cursor = start;
  while (cursor < end && /[ \t]/.test(value[cursor])) {
    cursor += 1;
  }
  if (value.slice(cursor, cursor + 2) === "[[") {
    cursor += 2;
    while (cursor < end && /[ \t]/.test(value[cursor])) {
      cursor += 1;
    }
  }
  if (value[cursor] === "(") {
    cursor += 1;
    while (cursor < end && /[ \t]/.test(value[cursor])) {
      cursor += 1;
    }
  }
  return cursor;
}

function trimPromptSyntaxSuffix(value, start, end) {
  let cursor = end;
  while (cursor > start && /[ \t]/.test(value[cursor - 1])) {
    cursor -= 1;
  }
  if (value.slice(Math.max(start, cursor - 2), cursor) === "]]") {
    cursor -= 2;
    while (cursor > start && /[ \t]/.test(value[cursor - 1])) {
      cursor -= 1;
    }
  }
  if (value[cursor - 1] === ")" && !isEscaped(value, cursor - 1)) {
    cursor -= 1;
    while (cursor > start && /[ \t]/.test(value[cursor - 1])) {
      cursor -= 1;
    }
  }
  const tokenText = value.slice(start, cursor);
  const weight = /\s*:\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)\s*$/.exec(tokenText);
  if (weight) {
    cursor -= weight[0].length;
  }
  return Math.max(start, cursor);
}

export function currentToken(value, caret, options = {}) {
  const text = String(value || "");
  const safeCaret = caret == null ? text.length : Number(caret);
  let segmentStart = safeCaret;
  while (segmentStart > 0 && text[segmentStart - 1] !== "," && text[segmentStart - 1] !== "\n") {
    segmentStart -= 1;
  }
  let segmentEnd = safeCaret;
  while (segmentEnd < text.length && text[segmentEnd] !== "," && text[segmentEnd] !== "\n") {
    segmentEnd += 1;
  }
  const naturalStart = naturalSentenceStart(
    text,
    segmentStart,
    safeCaret,
    options.detectNaturalSentences !== false,
  );
  const sentenceDelimited = naturalStart > segmentStart;
  if (sentenceDelimited) {
    segmentStart = naturalStart;
    segmentEnd = naturalSentenceEnd(text, safeCaret, segmentEnd);
  }
  const replaceStart = trimPromptSyntaxPrefix(text, segmentStart, segmentEnd);
  const replaceEnd = trimPromptSyntaxSuffix(text, replaceStart, segmentEnd);
  const queryEnd = clamp(safeCaret, replaceStart, replaceEnd);
  const strictRaw = text.slice(replaceStart, queryEnd);
  const legacyRaw = text.slice(segmentStart, safeCaret);
  const segment = text.slice(segmentStart, segmentEnd);
  const strictActive = safeCaret >= replaceStart && safeCaret <= replaceEnd && queryEnd > replaceStart;
  const legacyActive = legacyRaw.trim().length > 0;
  const useStrictToken = options.previewCompletion === true;
  return {
    value: text,
    start: replaceStart,
    end: replaceEnd,
    caret: safeCaret,
    segmentStart,
    segmentEnd,
    segment,
    tokenSegment: text.slice(replaceStart, replaceEnd),
    sentenceDelimited,
    query: (useStrictToken ? strictRaw : legacyRaw).trim(),
    active: useStrictToken ? strictActive : legacyActive,
  };
}

export function currentWildcardToken(value, caret) {
  const text = String(value || "");
  const safeCaret = caret == null ? text.length : Number(caret);
  let opening = -1;
  let index = 0;
  while (index < safeCaret) {
    const found = text.indexOf("__", index);
    if (found < 0 || found >= safeCaret) {
      break;
    }
    opening = opening < 0 ? found : -1;
    index = found + 2;
  }
  if (opening < 0) {
    return null;
  }
  const query = text.slice(opening + 2, safeCaret);
  if (/[\r\n,]/.test(query)) {
    return null;
  }
  const closing = text.indexOf("__", safeCaret);
  const end = closing >= 0 ? closing + 2 : safeCaret;
  const active = safeCaret >= opening + 2 && (closing < 0 || safeCaret <= closing);
  return {
    value: text,
    start: opening,
    end,
    caret: safeCaret,
    segment: text.slice(opening, end),
    query,
    wildcard: true,
    active,
  };
}

export function isCaretInPromptTranslationMarker(value, caret) {
  const text = String(value || "");
  const safeCaret = caret == null ? text.length : Number(caret);
  let index = 0;
  while (index < safeCaret) {
    const start = text.indexOf("%{", index);
    if (start < 0 || start >= safeCaret) {
      return false;
    }
    if (isEscaped(text, start)) {
      index = start + 2;
      continue;
    }
    let end = -1;
    for (let cursor = start + 2; cursor < text.length; cursor += 1) {
      if (text[cursor] === "}" && !isEscaped(text, cursor)) {
        end = cursor + 1;
        break;
      }
    }
    if (end < 0) {
      return safeCaret > start;
    }
    if (safeCaret > start && safeCaret < end) {
      return true;
    }
    index = end;
  }
  return false;
}

export function isCaretInComment(value, caret) {
  const text = String(value ?? "");
  const safeCaret = Math.max(0, Math.min(Number(caret) || 0, text.length));
  const lineStart = text.lastIndexOf("\n", safeCaret - 1) + 1;
  return /^[ \t]*#/.test(text.slice(lineStart, safeCaret));
}

function stripPromptSyntaxClosingParens(value) {
  let cursor = String(value || "").length;
  while (cursor > 0 && /[ \t]/.test(value[cursor - 1])) {
    cursor -= 1;
  }
  while (cursor > 0 && value[cursor - 1] === ")" && !isEscaped(value, cursor - 1)) {
    cursor -= 1;
    while (cursor > 0 && /[ \t]/.test(value[cursor - 1])) {
      cursor -= 1;
    }
  }
  return value.slice(0, cursor);
}

export function parseAutocompleteText(value) {
  let query = String(value || "").trim();
  query = query.replace(/^\[\[\s*/g, "");
  query = query.replace(/^\(\s*/g, "");
  const artistOnly = query.startsWith("@");
  if (artistOnly) {
    query = query.slice(1).trimStart();
  }
  query = stripPromptSyntaxClosingParens(query);
  query = query.replace(/:\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)\s*$/, "");
  query = stripPromptSyntaxClosingParens(query);
  return { query, artistOnly };
}

export function autocompleteQuery(token, forceArtistOnly = false) {
  const raw = String(token?.query || "");
  const parsed = parseAutocompleteText(raw);
  const artistOnly = forceArtistOnly || parsed.artistOnly;
  const query = parsed.query;
  const category = artistOnly ? "artist" : "";
  return { query, artistOnly, category };
}

export function wildcardAutocompleteQuery(token) {
  return {
    query: String(token?.query || "").toLocaleLowerCase(),
    artistOnly: false,
    category: "wildcard",
    kind: "wildcard",
  };
}

export function normalizeWildcardSearchText(value) {
  return String(value || "")
    .normalize("NFKC")
    .replaceAll("\\", "/")
    .replace(/[ _]+/g, "-")
    .trim()
    .toLocaleLowerCase();
}

function endsWithSentencePeriod(value) {
  const text = String(value || "").replace(/[ \t]+$/g, "");
  return text.length > 0 && isSentencePeriod(text, text.length - 1);
}

function startsWithSentencePeriod(value) {
  const text = String(value || "").replace(/^[ \t]+/g, "");
  return text.length > 0 && isSentencePeriod(text, 0);
}

function insertPrefixForBefore(before, noCommaAfterPeriod) {
  if (!before || before.endsWith("\n")) {
    return "";
  }
  const trimmed = before.replace(/[ \t]+$/g, "");
  if (trimmed.endsWith("(") || trimmed.endsWith("[[")) {
    return "";
  }
  if (before.endsWith(",")) {
    return " ";
  }
  if (/[ \t]$/.test(before)) {
    return "";
  }
  if (noCommaAfterPeriod && endsWithSentencePeriod(before)) {
    return " ";
  }
  return ", ";
}

function insertSuffixForAfter(after, appendSeparator, noCommaAfterPeriod) {
  if (!after) {
    return appendSeparator ? ", " : "";
  }
  if (/^[ \t]*:\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)/.test(after) || /^[ \t]*(?:\)|\]\])/.test(after)) {
    return "";
  }
  if (after.startsWith("\n") || after.startsWith(",")) {
    return "";
  }
  if (noCommaAfterPeriod && startsWithSentencePeriod(after)) {
    return "";
  }
  return ", ";
}

function insertSuffixPlanForAfter(after, appendSeparator, noCommaAfterPeriod) {
  const text = String(after || "");
  const suffix = insertSuffixForAfter(text, appendSeparator, noCommaAfterPeriod);
  if (!text) {
    return { suffix, consumeAfter: 0, caretExtra: suffix.length };
  }
  if (appendSeparator && text.startsWith(",")) {
    const match = /^,[ \t]*/.exec(text);
    return { suffix: ", ", consumeAfter: match?.[0]?.length || 1, caretExtra: 2 };
  }
  return { suffix, consumeAfter: 0, caretExtra: 0 };
}

export function planAutocompleteInsertion(token, insert, options = {}) {
  if (!token) {
    return null;
  }
  const sourceValue = String(token.value || "");
  const start = Number(token.start) || 0;
  const tokenEnd = Number(token.end) || start;
  const insertedText = String(insert || "");
  if (token.wildcard) {
    return {
      start,
      end: tokenEnd,
      replacement: insertedText,
      caretOffset: insertedText.length,
      prefix: "",
      suffix: "",
      consumeAfter: 0,
      caretExtra: 0,
    };
  }

  const before = sourceValue.slice(0, start);
  const after = sourceValue.slice(tokenEnd);
  const appendSeparator = options.appendSeparator === true;
  const noCommaAfterPeriod = options.noCommaAfterPeriod !== false;
  const prefix = insertPrefixForBefore(before, noCommaAfterPeriod);
  const suffixPlan = insertSuffixPlanForAfter(after, appendSeparator, noCommaAfterPeriod);
  const suffix = suffixPlan.suffix;
  const replacement = `${prefix}${insertedText}${suffix}`;
  return {
    start,
    end: tokenEnd + suffixPlan.consumeAfter,
    replacement,
    caretOffset: prefix.length + insertedText.length + suffixPlan.caretExtra,
    prefix,
    suffix,
    consumeAfter: suffixPlan.consumeAfter,
    caretExtra: suffixPlan.caretExtra,
  };
}
