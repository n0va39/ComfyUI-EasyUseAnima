// @ts-check

const SENTENCE_PERIODS = new Set([".", "。", "．", "｡"]);
const AUTOCOMPLETE_COMMIT_MODES = new Set(["smart", "insert", "replace"]);

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
  while (value[cursor] === "(" && !isEscaped(value, cursor)) {
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
  while (value[cursor - 1] === ")" && !isEscaped(value, cursor - 1)) {
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

function syntaxOpeningAt(value, index) {
  if (isEscaped(value, index)) {
    return null;
  }
  if (value.slice(index, index + 2) === "[[") {
    return { kind: "double-bracket", length: 2, closing: "]]" };
  }
  if (value[index] === "(") {
    return { kind: "parenthesis", length: 1, closing: ")" };
  }
  if (value[index] === "{") {
    return { kind: "brace", length: 1, closing: "}" };
  }
  return null;
}

function syntaxClosingAt(value, index) {
  if (isEscaped(value, index)) {
    return null;
  }
  if (value.slice(index, index + 2) === "]]") {
    return { value: "]]", length: 2 };
  }
  if (value[index] === ")" || value[index] === "}") {
    return { value: value[index], length: 1 };
  }
  return null;
}

function topLevelNumericWeightRange(value) {
  const text = String(value ?? "");
  const match = /:\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*$/.exec(text);
  if (!match || isEscaped(text, match.index)) {
    return null;
  }
  const stack = [];
  for (let index = 0; index < match.index; index += 1) {
    const opening = syntaxOpeningAt(text, index);
    if (opening) {
      stack.push(opening.closing);
      index += opening.length - 1;
      continue;
    }
    const closing = syntaxClosingAt(text, index);
    if (closing && stack[stack.length - 1] === closing.value) {
      stack.pop();
      index += closing.length - 1;
    }
  }
  if (stack.length > 0) {
    return null;
  }
  const numericStart = match.index + match[0].indexOf(match[1]);
  return {
    start: numericStart,
    end: numericStart + match[1].length,
  };
}

export function planBracketInsertion(
  value,
  selectionStart,
  selectionEnd,
  key,
  options = {},
) {
  const text = String(value ?? "");
  const rawStart = Number(selectionStart);
  const rawEnd = Number(selectionEnd);
  const safeStart = clamp(Number.isFinite(rawStart) ? rawStart : 0, 0, text.length);
  const safeEnd = clamp(
    Number.isFinite(rawEnd) ? rawEnd : safeStart,
    0,
    text.length,
  );
  const start = Math.min(safeStart, safeEnd);
  const end = Math.max(safeStart, safeEnd);
  const selected = text.slice(start, end);
  const hasSelection = end > start;

  if (key === "(") {
    if (hasSelection && options.selectionParenthesisWeight === true) {
      const existingWeight = topLevelNumericWeightRange(selected);
      if (existingWeight) {
        return {
          start,
          end,
          replacement: `(${selected})`,
          selectionStartOffset: 1 + existingWeight.start,
          selectionEndOffset: 1 + existingWeight.end,
          insertedWeight: false,
        };
      }
      return {
        start,
        end,
        replacement: `(${selected}:1)`,
        selectionStartOffset: selected.length + 2,
        selectionEndOffset: selected.length + 3,
        insertedWeight: true,
      };
    }
    const caretOffset = 1 + selected.length;
    return {
      start,
      end,
      replacement: `(${selected})`,
      selectionStartOffset: caretOffset,
      selectionEndOffset: caretOffset,
      insertedWeight: false,
    };
  }

  if (key === "{") {
    const caretOffset = 1 + selected.length;
    return {
      start,
      end,
      replacement: `{${selected}}`,
      selectionStartOffset: caretOffset,
      selectionEndOffset: caretOffset,
    };
  }

  if (key === "[" && hasSelection) {
    const caretOffset = 2 + selected.length;
    return {
      start,
      end,
      replacement: `[[${selected}]]`,
      selectionStartOffset: caretOffset,
      selectionEndOffset: caretOffset,
    };
  }

  if (key === "[" && text[start - 1] === "[") {
    return {
      start,
      end,
      replacement: "[]]",
      selectionStartOffset: 1,
      selectionEndOffset: 1,
    };
  }

  return null;
}

function syntaxGroups(value) {
  const groups = [];
  const stack = [];
  for (let index = 0; index < value.length; index += 1) {
    const opening = syntaxOpeningAt(value, index);
    if (opening) {
      const group = {
        kind: opening.kind,
        openStart: index,
        contentStart: index + opening.length,
        closeStart: value.length,
        contentEnd: value.length,
      };
      groups.push(group);
      stack.push({ group, closing: opening.closing });
      index += opening.length - 1;
      continue;
    }
    const closing = syntaxClosingAt(value, index);
    const active = stack[stack.length - 1];
    if (!closing || !active || closing.value !== active.closing) {
      continue;
    }
    active.group.closeStart = index;
    active.group.contentEnd = index;
    stack.pop();
    index += closing.length - 1;
  }
  return groups;
}

function activeSyntaxGroup(value, caret) {
  let selected = null;
  for (const group of syntaxGroups(value)) {
    if (caret < group.contentStart || caret > group.contentEnd) {
      continue;
    }
    if (!selected || group.contentStart >= selected.contentStart) {
      selected = group;
    }
  }
  return selected || {
    kind: "root",
    openStart: -1,
    contentStart: 0,
    closeStart: value.length,
    contentEnd: value.length,
  };
}

function itemBoundsAtCaret(value, caret, groupKind, groupStart, groupEnd) {
  let itemStart = groupStart;
  let itemEnd = groupEnd;
  const stack = [];
  for (let index = groupStart; index < groupEnd; index += 1) {
    const opening = syntaxOpeningAt(value, index);
    if (opening) {
      stack.push(opening.closing);
      index += opening.length - 1;
      continue;
    }
    const closing = syntaxClosingAt(value, index);
    if (closing && stack[stack.length - 1] === closing.value) {
      stack.pop();
      index += closing.length - 1;
      continue;
    }
    const itemDelimiter = value[index] === ","
      || value[index] === "\n"
      || (groupKind === "brace" && value[index] === "|");
    if (stack.length > 0 || !itemDelimiter) {
      continue;
    }
    if (index < caret) {
      itemStart = index + 1;
      continue;
    }
    itemEnd = index;
    break;
  }
  return { itemStart, itemEnd };
}

function contiguousTailEnd(value, caret, itemEnd) {
  let end = caret;
  while (end < itemEnd) {
    const closing = syntaxClosingAt(value, end);
    if (closing || /[\s,\n]/.test(value[end])) {
      break;
    }
    end += 1;
  }
  const tail = value.slice(caret, end);
  const weight = /:\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)\s*$/.exec(tail);
  return weight ? caret + weight.index : end;
}

export function completionEditRangeContract(value, caret, options = {}) {
  const text = String(value || "");
  const safeCaret = clamp(
    caret == null ? text.length : Number(caret),
    0,
    text.length,
  );
  const rawSelectionStart = options.selectionStart == null
    ? safeCaret
    : Number(options.selectionStart);
  const rawSelectionEnd = options.selectionEnd == null
    ? safeCaret
    : Number(options.selectionEnd);
  const selectionStart = clamp(
    Math.min(rawSelectionStart, rawSelectionEnd),
    0,
    text.length,
  );
  const selectionEnd = clamp(
    Math.max(rawSelectionStart, rawSelectionEnd),
    0,
    text.length,
  );
  const selectionActive = selectionEnd > selectionStart;
  const contextCaret = selectionActive ? selectionStart : safeCaret;
  const group = activeSyntaxGroup(text, contextCaret);
  const { itemStart, itemEnd } = itemBoundsAtCaret(
    text,
    contextCaret,
    group.kind,
    group.contentStart,
    group.contentEnd,
  );

  if (selectionActive) {
    return {
      value: text,
      caret: safeCaret,
      selectionStart,
      selectionEnd,
      queryStart: selectionStart,
      queryEnd: selectionEnd,
      insertStart: selectionStart,
      insertEnd: selectionEnd,
      replaceStart: selectionStart,
      replaceEnd: selectionEnd,
      protectedSuffixStart: selectionEnd,
      groupKind: group.kind,
      groupStart: group.contentStart,
      groupEnd: group.contentEnd,
      itemStart,
      itemEnd,
    };
  }

  const naturalStart = naturalSentenceStart(
    text,
    itemStart,
    safeCaret,
    options.detectNaturalSentences !== false,
  );
  const sentenceDelimited = naturalStart > itemStart;
  const activeItemEnd = sentenceDelimited
    ? naturalSentenceEnd(text, safeCaret, itemEnd)
    : itemEnd;
  const rangeStart = trimPromptSyntaxPrefix(text, naturalStart, activeItemEnd);
  const queryEnd = clamp(safeCaret, rangeStart, activeItemEnd);
  const replaceEnd = contiguousTailEnd(text, queryEnd, activeItemEnd);

  return {
    value: text,
    caret: safeCaret,
    selectionStart,
    selectionEnd,
    queryStart: rangeStart,
    queryEnd,
    insertStart: rangeStart,
    insertEnd: queryEnd,
    replaceStart: rangeStart,
    replaceEnd,
    protectedSuffixStart: replaceEnd,
    groupKind: group.kind,
    groupStart: group.contentStart,
    groupEnd: group.contentEnd,
    itemStart,
    itemEnd,
  };
}

export function currentToken(value, caret, options = {}) {
  const text = String(value || "");
  const safeCaret = caret == null ? text.length : Number(caret);
  const editRanges = completionEditRangeContract(text, safeCaret, {
    selectionStart: options.selectionStart,
    selectionEnd: options.selectionEnd,
    detectNaturalSentences: options.detectNaturalSentences,
  });
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
    selectionStart: editRanges.selectionStart,
    selectionEnd: editRanges.selectionEnd,
    queryStart: editRanges.queryStart,
    queryEnd: editRanges.queryEnd,
    insertStart: editRanges.insertStart,
    insertEnd: editRanges.insertEnd,
    replaceStart: editRanges.replaceStart,
    replaceEnd: editRanges.replaceEnd,
    protectedSuffixStart: editRanges.protectedSuffixStart,
    groupKind: editRanges.groupKind,
    groupStart: editRanges.groupStart,
    groupEnd: editRanges.groupEnd,
    itemStart: editRanges.itemStart,
    itemEnd: editRanges.itemEnd,
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

export function normalizeAutocompleteArtistPrefix(value) {
  const prefix = String(value ?? "").trim();
  if (
    !prefix
    || prefix.length > 32
    || prefix.includes(",")
    || /[\u0000-\u001f\u007f-\u009f]/.test(prefix)
  ) {
    return "@";
  }
  return prefix;
}

export function artistCompletionText(value, artistPrefix = "@") {
  const tag = String(value ?? "");
  const prefix = normalizeAutocompleteArtistPrefix(artistPrefix);
  return tag.startsWith(prefix) ? tag : `${prefix}${tag}`;
}

export function parseAutocompleteText(value, artistPrefix = "@") {
  let query = String(value || "").trim();
  query = query.slice(trimPromptSyntaxPrefix(query, 0, query.length));
  const prefix = normalizeAutocompleteArtistPrefix(artistPrefix);
  const artistOnly = query.startsWith(prefix);
  if (artistOnly) {
    query = query.slice(prefix.length).trimStart();
  }
  query = stripPromptSyntaxClosingParens(query);
  query = query.replace(/:\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)\s*$/, "");
  query = stripPromptSyntaxClosingParens(query);
  return { query, artistOnly };
}

export function autocompleteQuery(token, forceArtistOnly = false, artistPrefix = "@") {
  const raw = String(token?.query || "");
  const parsed = parseAutocompleteText(raw, artistPrefix);
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
  if (/^[ \t]/.test(after)) {
    return "";
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

export function normalizeAutocompleteCommitMode(value) {
  const mode = String(value || "").trim().toLocaleLowerCase();
  return AUTOCOMPLETE_COMMIT_MODES.has(mode) ? mode : "smart";
}

function tokenRange(value, fallback, sourceLength) {
  const range = Number(value);
  return Number.isFinite(range)
    ? clamp(range, 0, sourceLength)
    : fallback;
}

function normalizedSmartMatchText(value) {
  return String(value || "")
    .trim()
    .toLocaleLowerCase()
    .replace(/[_\s]+/g, " ");
}

function smartUsesReplaceRange(
  token,
  sourceValue,
  insertedText,
  insertStart,
  insertEnd,
  replaceStart,
  replaceEnd,
) {
  if (replaceEnd <= insertEnd) {
    return true;
  }
  if (Number(token.selectionEnd) > Number(token.selectionStart)) {
    return true;
  }
  const currentItem = normalizedSmartMatchText(
    sourceValue.slice(replaceStart, replaceEnd),
  );
  const typedPrefix = normalizedSmartMatchText(
    sourceValue.slice(insertStart, insertEnd),
  );
  const completion = normalizedSmartMatchText(insertedText);
  return !!currentItem
    && !!typedPrefix
    && completion.startsWith(typedPrefix)
    && completion.startsWith(currentItem);
}

export function planAutocompleteInsertion(token, insert, options = {}) {
  if (!token) {
    return null;
  }
  const sourceValue = String(token.value || "");
  const fallbackStart = clamp(Number(token.start) || 0, 0, sourceValue.length);
  const fallbackEnd = tokenRange(token.end, fallbackStart, sourceValue.length);
  const insertedText = String(insert || "");
  if (token.wildcard) {
    return {
      start: fallbackStart,
      end: fallbackEnd,
      replacement: insertedText,
      caretOffset: insertedText.length,
      prefix: "",
      suffix: "",
      consumeAfter: 0,
      caretExtra: 0,
    };
  }

  const insertStart = tokenRange(token.insertStart, fallbackStart, sourceValue.length);
  const insertEnd = tokenRange(token.insertEnd, fallbackEnd, sourceValue.length);
  const replaceStart = tokenRange(token.replaceStart, fallbackStart, sourceValue.length);
  const replaceEnd = tokenRange(token.replaceEnd, fallbackEnd, sourceValue.length);
  const modeUsed = normalizeAutocompleteCommitMode(options.commitMode);
  const useReplaceRange = modeUsed === "replace"
    || (
      modeUsed === "smart"
      && smartUsesReplaceRange(
        token,
        sourceValue,
        insertedText,
        insertStart,
        insertEnd,
        replaceStart,
        replaceEnd,
      )
    );
  const start = useReplaceRange ? replaceStart : insertStart;
  const tokenEnd = useReplaceRange ? replaceEnd : insertEnd;
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
    preservedSuffix: sourceValue.slice(tokenEnd + suffixPlan.consumeAfter),
    modeUsed,
    editRange: useReplaceRange ? "replace" : "insert",
  };
}
