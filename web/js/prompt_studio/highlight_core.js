// @ts-check

import { normalizePromptTagText } from "../easyuse_anima_prompt_rules.js";

const WEIGHT_NUMBER_RE = /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$/;
const WEIGHTED_TOKEN_RE = /^\((.*):[+-]?(?:\d+(?:\.\d*)?|\.\d+)\)$/s;
const WEIGHT_NUMBER_COLOR = "#fb923c";
const WILDCARD_HIGHLIGHT_RE = /(?:\d+#)?__[\p{L}\p{N}_.\-+/*\\]+?__/gu;
const ARTIST_MIX_GROUP_HIGHLIGHT_RE = /\[\[[\s\S]*?(?::[-+]?(?:\d+(?:\.\d*)?|\.\d+))?\]\]/g;
const INLINE_SPACE_RE = /[ \t]+/g;

/**
 * @typedef {Object} PromptHighlightToken
 * @property {string} [token]
 * @property {string} [base]
 * @property {string} [section]
 * @property {string} [label]
 * @property {boolean} [learned]
 * @property {boolean} [weighted]
 * @property {number} [count]
 * @property {string} [description]
 */

/**
 * @typedef {Object} PromptHighlightRendererOptions
 * @property {(value: unknown) => string} escapeHtml
 * @property {(section: string) => string} sectionLabel
 * @property {(token: PromptHighlightToken) => string} tokenStyle
 * @property {(text: string, token: PromptHighlightToken) => string} tokenSpanHtml
 * @property {() => boolean} weightSyntaxUnderlineEnabled
 * @property {boolean} [preferSyntaxBeforeToken]
 */

function normalize(value) {
  return normalizePromptTagText(value, { unescapeAll: true })
    .toLocaleLowerCase()
    .replace(INLINE_SPACE_RE, " ")
    .trim();
}

function tokenBase(token) {
  let value = String(token ?? "").trim();
  const weighted = WEIGHTED_TOKEN_RE.exec(value);
  if (weighted) {
    value = weighted[1].trim();
  }
  value = value.replace(/:+$/, "").trim();
  value = value.replace(/\\(.)/g, "$1");
  if (value.startsWith("@")) {
    return value.slice(1).trim();
  }
  return value;
}

function isEscapedAt(value, index) {
  let slashCount = 0;
  for (let cursor = index - 1; cursor >= 0 && value[cursor] === "\\"; cursor -= 1) {
    slashCount += 1;
  }
  return slashCount % 2 === 1;
}

function findDynamicPromptEnd(value, start) {
  for (let cursor = start + 1; cursor < value.length; cursor += 1) {
    if (value[cursor] === "\\" && cursor + 1 < value.length) {
      cursor += 1;
      continue;
    }
    if (value[cursor] === "{") {
      return -1;
    }
    if (value[cursor] === "}") {
      return cursor + 1;
    }
  }
  return -1;
}

function findDynamicPromptRange(value, offset) {
  for (let start = offset; start < value.length; start += 1) {
    if (value[start] !== "{" || isEscapedAt(value, start)) {
      continue;
    }
    const end = findDynamicPromptEnd(value, start);
    if (end > start) {
      return { start, end };
    }
  }
  return null;
}

function findPromptTranslationRange(value, offset) {
  for (let start = offset; start < value.length; start += 1) {
    if (value[start] !== "%" || value[start + 1] !== "{" || isEscapedAt(value, start)) {
      continue;
    }
    for (let cursor = start + 2; cursor < value.length; cursor += 1) {
      if (value[cursor] === "}" && !isEscapedAt(value, cursor)) {
        return { start, end: cursor + 1 };
      }
    }
    return null;
  }
  return null;
}

function findWildcardSyntaxRange(value, offset) {
  WILDCARD_HIGHLIGHT_RE.lastIndex = offset;
  const wildcardMatch = WILDCARD_HIGHLIGHT_RE.exec(value);
  const wildcard = wildcardMatch
    ? { start: wildcardMatch.index, end: wildcardMatch.index + wildcardMatch[0].length }
    : null;
  const dynamic = findDynamicPromptRange(value, offset);
  if (!wildcard) {
    return dynamic;
  }
  if (!dynamic || wildcard.start <= dynamic.start) {
    return wildcard;
  }
  return dynamic;
}

function findArtistMixGroupSyntaxRange(value, offset) {
  ARTIST_MIX_GROUP_HIGHLIGHT_RE.lastIndex = offset;
  const match = ARTIST_MIX_GROUP_HIGHLIGHT_RE.exec(value);
  return match
    ? { start: match.index, end: match.index + match[0].length }
    : null;
}

function firstSyntaxRange(value, offset) {
  const ranges = [
    findWildcardSyntaxRange(value, offset),
    findPromptTranslationRange(value, offset),
    findArtistMixGroupSyntaxRange(value, offset),
  ].filter(Boolean);
  if (!ranges.length) {
    return null;
  }
  return ranges.reduce((first, range) => (range.start < first.start ? range : first), ranges[0]);
}

function hasHighlightSyntax(text) {
  return !!firstSyntaxRange(String(text ?? ""), 0);
}

function isPromptLineCommentStart(value, index) {
  if (value[index] !== "#") {
    return false;
  }
  const lineStart = value.lastIndexOf("\n", index - 1) + 1;
  return /^[ \t]*$/.test(value.slice(lineStart, index));
}

function splitPromptText(text) {
  const parts = [];
  let start = 0;
  let depth = 0;
  let artistGroupDepth = 0;
  let escaped = false;
  const value = String(text ?? "");

  for (let index = 0; index < value.length; index += 1) {
    const char = value[index];
    if (escaped) {
      escaped = false;
      continue;
    }
    if (char === "\\") {
      escaped = true;
      continue;
    }
    if (char === "[" && value[index + 1] === "[") {
      artistGroupDepth += 1;
      index += 1;
      continue;
    }
    if (char === "]" && value[index + 1] === "]" && artistGroupDepth > 0) {
      artistGroupDepth -= 1;
      index += 1;
      continue;
    }
    if (isPromptLineCommentStart(value, index)) {
      const nextNewLine = value.indexOf("\n", index);
      index = nextNewLine === -1 ? value.length : nextNewLine - 1;
      continue;
    }
    if (char === "(") {
      depth += 1;
      continue;
    }
    if (char === ")" && depth > 0) {
      depth -= 1;
      continue;
    }
    if (char === "{") {
      const dynamicEnd = findDynamicPromptEnd(value, index);
      if (dynamicEnd > index) {
        index = dynamicEnd - 1;
      }
      continue;
    }
    if ((char === "," || char === "\n") && depth === 0 && artistGroupDepth === 0) {
      if (index > start) {
        parts.push({ text: value.slice(start, index), delimiter: false });
      }
      parts.push({ text: char, delimiter: true });
      start = index + 1;
    }
  }

  if (start < value.length) {
    parts.push({ text: value.slice(start), delimiter: false });
  }
  return parts;
}

function findTopLevelWeightColon(value) {
  let depth = 0;
  let colon = -1;
  let escaped = false;
  const text = String(value ?? "");
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (escaped) {
      escaped = false;
      continue;
    }
    if (char === "\\") {
      escaped = true;
      continue;
    }
    if (char === "(") {
      depth += 1;
      continue;
    }
    if (char === ")" && depth > 0) {
      depth -= 1;
      continue;
    }
    if (char === ":" && depth === 0) {
      colon = index;
    }
  }
  return colon;
}

function artistMixGroupParts(text) {
  const match = /^(\[\[)([\s\S]*?)(\]\])$/.exec(String(text ?? ""));
  if (!match) {
    return null;
  }
  const body = match[2];
  const colon = findTopLevelWeightColon(body);
  if (colon < 0) {
    return { open: match[1], body, weight: "", close: match[3], syntaxError: false };
  }
  const weight = body.slice(colon + 1).trim();
  if (!weight || !WEIGHT_NUMBER_RE.test(weight)) {
    return { open: match[1], body, weight: "", close: match[3], syntaxError: true };
  }
  return {
    open: match[1],
    body: body.slice(0, colon).replace(/[ \t\r\n,]+$/g, ""),
    weight,
    close: match[3],
    syntaxError: false,
  };
}

function findTokenMatch(body, offset, token) {
  let start = offset;
  while (
    start < body.length
    && (
      /\s/.test(body[start])
      || body[start] === ","
      || body[start] === "("
    )
  ) {
    start += 1;
  }

  const candidates = [
    String(token?.token || ""),
    String(token?.base || ""),
  ].filter(Boolean);
  for (const candidate of candidates) {
    if (body.slice(start, start + candidate.length) === candidate) {
      return { start, end: start + candidate.length };
    }
    const normalized = normalize(candidate);
    const maxEnd = Math.min(body.length, start + candidate.length + 32);
    for (let end = start + 1; end <= maxEnd; end += 1) {
      const prefix = normalize(body.slice(start, end));
      if (prefix === normalized) {
        return { start, end };
      }
      if (prefix.length > normalized.length + 8) {
        break;
      }
    }
  }
  return null;
}

function weightedTokenSegmentRange(body, cursor, match) {
  const open = body.lastIndexOf("(", Math.max(cursor, match.start));
  if (open < cursor) {
    return null;
  }
  const suffix = /^\s*:\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)\s*\)/.exec(body.slice(match.end));
  if (!suffix) {
    return null;
  }
  return { start: open, end: match.end + suffix[0].length };
}

function tokenKey(token) {
  return normalize(token?.base || token?.token);
}

function nextUnconsumedToken(tokens, startIndex, consumed) {
  let index = startIndex;
  while (index < (tokens?.length || 0) && consumed.has(tokens[index])) {
    index += 1;
  }
  return { token: tokens?.[index], index };
}

function takeTokenByBase(byBase, baseKey, consumed) {
  const candidates = byBase.get(baseKey);
  while (candidates?.length) {
    const token = candidates.shift();
    if (!consumed.has(token)) {
      consumed.add(token);
      return token;
    }
  }
  return null;
}

/**
 * @param {PromptHighlightRendererOptions} options
 * @returns {(text: string, tokens?: Array<PromptHighlightToken>) => string}
 */
function createPromptHighlightRenderer(options) {
  const {
    escapeHtml,
    sectionLabel,
    tokenStyle,
    tokenSpanHtml,
    weightSyntaxUnderlineEnabled,
    preferSyntaxBeforeToken = false,
  } = options;
  function weightSyntaxDecoration() {
    return weightSyntaxUnderlineEnabled()
      ? [
        "text-decoration-line: underline",
        "text-decoration-style: solid",
        "text-decoration-color: rgba(148, 163, 184, 0.95)",
        "text-underline-offset: 3px",
        "text-decoration-skip-ink: none",
      ].join("; ")
      : "";
  }

  function wrapWeightSyntaxHtml(html) {
    const decoration = weightSyntaxDecoration();
    return decoration
      ? `<span style="${decoration}">${html}</span>`
      : html;
  }

  function weightSyntaxSpanHtml(text, style = "") {
    const rules = [style].filter(Boolean).join("; ");
    return rules
      ? `<span style="${rules}">${escapeHtml(text)}</span>`
      : escapeHtml(text);
  }

  function syntaxErrorSpanHtml(text, title = sectionLabel("syntax")) {
    return `<span style="${tokenStyle({ section: "syntax" })}" title="${escapeHtml(title)}">`
      + escapeHtml(text)
      + "</span>";
  }

  function weightedParenSyntaxHtml(text) {
    const match = /^(\()([\s\S]*?)(:)(\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+))(\s*\))$/.exec(String(text ?? ""));
    if (!match) {
      return syntaxErrorSpanHtml(text);
    }
    const [, open, body, colon, weight, close] = match;
    return wrapWeightSyntaxHtml(
      weightSyntaxSpanHtml(open)
      + escapeHtml(body)
      + weightSyntaxSpanHtml(colon)
      + weightSyntaxSpanHtml(weight, `color: ${WEIGHT_NUMBER_COLOR}`)
      + weightSyntaxSpanHtml(close),
    );
  }

  function basicSyntaxHtml(text) {
    const value = String(text ?? "");
    const html = [];
    const pattern = /\([^()\n]*:[^()\n]*\)/g;
    let cursor = 0;
    let match = null;
    while ((match = pattern.exec(value))) {
      html.push(escapeHtml(value.slice(cursor, match.index)));
      html.push(weightedParenSyntaxHtml(match[0]));
      cursor = match.index + match[0].length;
    }
    html.push(escapeHtml(value.slice(cursor)));
    return html.join("");
  }

  function wildcardSyntaxSpanHtml(text) {
    return `<span style="${tokenStyle({ section: "wildcard" })}" title="${escapeHtml(sectionLabel("wildcard"))}">`
      + escapeHtml(text)
      + "</span>";
  }

  function translationSyntaxSpanHtml(text) {
    return `<span style="${tokenStyle({ section: "translation" })}" title="${escapeHtml(sectionLabel("translation"))}">`
      + escapeHtml(text)
      + "</span>";
  }

  function artistMixGroupShellHtml(parts, bodyHtml) {
    if (!parts || parts.syntaxError) {
      return syntaxErrorSpanHtml(`${parts?.open || ""}${parts?.body || ""}${parts?.close || ""}`);
    }
    const openHtml = weightSyntaxSpanHtml(parts.open);
    const closeHtml = weightSyntaxSpanHtml(parts.close);
    const weightHtml = parts.weight
      ? weightSyntaxSpanHtml(":")
        + weightSyntaxSpanHtml(parts.weight, `color: ${WEIGHT_NUMBER_COLOR}`)
      : "";
    const html = `${openHtml}${bodyHtml}${weightHtml}${closeHtml}`;
    return wrapWeightSyntaxHtml(html);
  }

  function artistMixGroupSyntaxHtml(text) {
    const parts = artistMixGroupParts(text);
    if (!parts) {
      return basicSyntaxHtml(text);
    }
    if (parts.syntaxError) {
      return syntaxErrorSpanHtml(text);
    }
    return artistMixGroupShellHtml(parts, syntaxHtml(parts.body));
  }

  function syntaxHtml(text) {
    const value = String(text ?? "");
    let cursor = 0;
    const html = [];
    while (cursor < value.length) {
      const range = firstSyntaxRange(value, cursor);
      if (!range) {
        break;
      }
      html.push(basicSyntaxHtml(value.slice(cursor, range.start)));
      const snippet = value.slice(range.start, range.end);
      if (snippet.startsWith("[[")) {
        html.push(artistMixGroupSyntaxHtml(snippet));
      } else if (snippet.startsWith("%{")) {
        html.push(translationSyntaxSpanHtml(snippet));
      } else {
        html.push(wildcardSyntaxSpanHtml(snippet));
      }
      cursor = range.end;
    }
    html.push(basicSyntaxHtml(value.slice(cursor)));
    return html.join("");
  }

  function weightedTokenSpanHtml(text, token) {
    const match = findTokenMatch(text, 0, token);
    if (!match) {
      return tokenSpanHtml(text, token);
    }
    const html = [
      syntaxHtml(text.slice(0, match.start)),
      tokenSpanHtml(text.slice(match.start, match.end), token),
      syntaxHtml(text.slice(match.end)),
    ].join("");
    return WEIGHTED_TOKEN_RE.test(String(text ?? "").trim())
      ? wrapWeightSyntaxHtml(html)
      : html;
  }

  function renderSequentialBody(body, tokens, startIndex, consumed) {
    let cursor = 0;
    let index = startIndex;
    let matched = 0;
    const html = [];

    while (index < (tokens?.length || 0)) {
      const next = nextUnconsumedToken(tokens, index, consumed);
      const token = next.token;
      index = next.index;
      if (!token) {
        break;
      }
      const match = findTokenMatch(body, cursor, token);
      if (!match) {
        break;
      }
      const weightedRange = token?.weighted ? weightedTokenSegmentRange(body, cursor, match) : null;
      if (weightedRange) {
        html.push(syntaxHtml(body.slice(cursor, weightedRange.start)));
        html.push(weightedTokenSpanHtml(body.slice(weightedRange.start, weightedRange.end), token));
        cursor = weightedRange.end;
      } else {
        html.push(syntaxHtml(body.slice(cursor, match.start)));
        html.push(tokenSpanHtml(body.slice(match.start, match.end), token));
        cursor = match.end;
      }
      consumed.add(token);
      index += 1;
      matched += 1;
      if (!body.slice(cursor).trim()) {
        break;
      }
    }

    if (!matched) {
      return null;
    }
    html.push(syntaxHtml(body.slice(cursor)));
    return { html: html.join(""), nextIndex: index };
  }

  function renderHighlightedText(text, tokens) {
    const byBase = new Map();
    for (const token of tokens || []) {
      const key = tokenKey(token);
      if (!key) {
        continue;
      }
      byBase.set(key, [...(byBase.get(key) || []), token]);
    }

    let tokenIndex = 0;
    const consumed = new Set();
    const html = [];
    for (const part of splitPromptText(text)) {
      if (part.delimiter) {
        html.push(escapeHtml(part.text));
        continue;
      }

      const match = /^(\s*)([\s\S]*?)(\s*)$/.exec(part.text);
      const leading = match?.[1] || "";
      const body = match?.[2] || "";
      const trailing = match?.[3] || "";
      if (!body) {
        html.push(escapeHtml(part.text));
        continue;
      }

      const artistGroup = artistMixGroupParts(body);
      if (artistGroup) {
        const rendered = artistGroup.syntaxError
          ? null
          : renderSequentialBody(artistGroup.body, tokens, tokenIndex, consumed);
        html.push(escapeHtml(leading));
        if (artistGroup.syntaxError) {
          html.push(syntaxErrorSpanHtml(body));
        } else {
          if (rendered) {
            tokenIndex = rendered.nextIndex;
          }
          html.push(artistMixGroupShellHtml(
            artistGroup,
            rendered ? rendered.html : syntaxHtml(artistGroup.body),
          ));
        }
        html.push(escapeHtml(trailing));
        continue;
      }

      if (preferSyntaxBeforeToken && hasHighlightSyntax(body)) {
        html.push(escapeHtml(leading));
        html.push(syntaxHtml(body));
        html.push(escapeHtml(trailing));
        continue;
      }

      const baseKey = normalize(tokenBase(body));
      const next = nextUnconsumedToken(tokens, tokenIndex, consumed);
      const sequential = next.token;
      tokenIndex = next.index;
      let token = null;
      if (tokenKey(sequential) === baseKey) {
        token = sequential;
        consumed.add(token);
        tokenIndex += 1;
      } else {
        token = takeTokenByBase(byBase, baseKey, consumed);
      }

      if (token) {
        html.push(escapeHtml(leading));
        html.push(token?.weighted && WEIGHTED_TOKEN_RE.test(body)
          ? weightedTokenSpanHtml(body, token)
          : tokenSpanHtml(body, token));
        html.push(escapeHtml(trailing));
        continue;
      }

      const rendered = renderSequentialBody(body, tokens, tokenIndex, consumed);
      if (rendered) {
        tokenIndex = rendered.nextIndex;
        html.push(escapeHtml(leading));
        html.push(rendered.html);
        html.push(escapeHtml(trailing));
        continue;
      }

      html.push(syntaxHtml(part.text));
    }
    return html.join("") || " ";
  }

  return renderHighlightedText;
}

export {
  createPromptHighlightRenderer,
  hasHighlightSyntax,
};
