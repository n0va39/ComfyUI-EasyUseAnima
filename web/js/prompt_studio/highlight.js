import { easyuseAnimaClassifyPrompt } from "../easyuse_anima_api.js";
import { normalizePromptTagText } from "../easyuse_anima_prompt_rules.js";
import {
  SECTION_STYLES,
  WEIGHT_NUMBER_RE,
  WEIGHTED_TOKEN_RE,
  WEIGHT_NUMBER_COLOR,
  WILDCARD_HIGHLIGHT_RE,
  ARTIST_MIX_GROUP_HIGHLIGHT_RE,
  INLINE_SPACE_RE,
  HIGHLIGHT_TEXT_METRIC_PROPERTIES,
  AUTOCOMPLETE_TOOLTIP_SECTIONS,
} from "./constants.js";
import {
  escapeHtml,
  escapeAttr,
} from "./utils.js";
import { PROMPT_STUDIO_SETTINGS } from "./settings.js";
import { ensureHighlightStyle } from "./style.js";
import { psText, sectionLabel } from "./text.js";
import { installTrainedTagTooltipListeners } from "./tooltip.js";

async function classifyPrompt(text) {
  return easyuseAnimaClassifyPrompt(text);
}



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

function tokenStyle(token) {
  const style = SECTION_STYLES[token?.section] || SECTION_STYLES.unknown;
  const opacity = token?.learned || token?.section === "count" ? 1 : 0.88;
  const rules = [
    `color: ${style.color}`,
    `opacity: ${opacity}`,
  ];
  if (style.background && style.background !== "transparent") {
    rules.push(`background: ${style.background}`, "border-radius: 3px");
  }
  if (style.italic && PROMPT_STUDIO_SETTINGS.commentItalic) {
    rules.push("font-style: italic");
  }
  if (style.underline && PROMPT_STUDIO_SETTINGS.typoIndicator && !token?.weighted) {
    rules.push(
      "text-decoration-line: underline",
      "text-decoration-style: wavy",
      "text-decoration-color: #ef4444",
      "text-underline-offset: 2px",
    );
  }
  return rules.join("; ");
}

function tokenTitle(token) {
  const style = SECTION_STYLES[token?.section] || SECTION_STYLES.unknown;
  const label = token?.label || sectionLabel(token?.section) || style.label || token?.section || psText("tag.generic");
  const learned = token?.learned ? ` / ${psText("tag.learned")}` : "";
  return `${label}${learned}`;
}

function trainedTagTooltipEntry(text, token) {
  if (!PROMPT_STUDIO_SETTINGS.trainedTagTooltip) {
    return null;
  }
  const section = String(token?.section || "");
  if (!AUTOCOMPLETE_TOOLTIP_SECTIONS.has(section) || !token?.learned) {
    return null;
  }
  const tag = String(token?.base || text || token?.token || "").trim();
  if (!tag) {
    return null;
  }
  return {
    tag,
    category: section,
    count: Number(token?.count || 0),
    description: String(token?.description || ""),
  };
}

function trainedTagTooltipData(text, token) {
  const entry = trainedTagTooltipEntry(text, token);
  if (!entry) {
    return null;
  }
  const tooltip = typeof window !== "undefined" && typeof window.easyuseAnimaAutocompleteEntryTooltip === "function"
    ? window.easyuseAnimaAutocompleteEntryTooltip(entry)
    : {
      tag: entry.tag,
      meta: `${sectionLabel(entry.category)} · ${Number(entry.count || 0).toLocaleString()}`,
      description: entry.description,
    };
  return {
    tag: String(tooltip?.tag || entry.tag),
    meta: String(tooltip?.meta || ""),
    description: String(tooltip?.description || ""),
  };
}

function trainedTagTooltipAttrs(text, token) {
  const tooltip = trainedTagTooltipData(text, token);
  if (!tooltip) {
    return "";
  }
  const title = [tooltip.tag, tooltip.meta, tooltip.description].filter(Boolean).join("\n");
  return [
    'data-easyuse-anima-trained-tag-tooltip="true"',
    `data-easyuse-anima-tooltip-tag="${escapeAttr(tooltip.tag)}"`,
    `data-easyuse-anima-tooltip-meta="${escapeAttr(tooltip.meta)}"`,
    `data-easyuse-anima-tooltip-description="${escapeAttr(tooltip.description)}"`,
    `aria-label="${escapeAttr(title)}"`,
  ].join(" ");
}

function tokenSpanHtml(text, token) {
  const tooltip = trainedTagTooltipData(text, token);
  const title = tooltip
    ? [tooltip.tag, tooltip.meta, tooltip.description].filter(Boolean).join("\n")
    : tokenTitle(token);
  const attrs = trainedTagTooltipAttrs(text, token);
  return `<span style="${tokenStyle(token)}" title="${escapeAttr(title)}"${attrs ? ` ${attrs}` : ""}>`
    + escapeHtml(text)
    + "</span>";
}

function weightSyntaxDecoration() {
  return PROMPT_STUDIO_SETTINGS.weightSyntaxUnderline
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

    const artistGroupParts = artistMixGroupParts(body);
    if (artistGroupParts) {
      const rendered = artistGroupParts.syntaxError
        ? null
        : renderSequentialBody(artistGroupParts.body, tokens, tokenIndex, consumed);
      html.push(escapeHtml(leading));
      if (artistGroupParts.syntaxError) {
        html.push(syntaxErrorSpanHtml(body));
      } else {
        if (rendered) {
          tokenIndex = rendered.nextIndex;
        }
        html.push(artistMixGroupShellHtml(
          artistGroupParts,
          rendered ? rendered.html : syntaxHtml(artistGroupParts.body),
        ));
      }
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

function cssPixelNumber(value) {
  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function cssPixel(value) {
  const rounded = Math.round(Number(value || 0) * 100) / 100;
  return `${rounded}px`;
}

function overlayScrollbarPadding(input, style = getComputedStyle(input)) {
  const verticalGutter = Math.max(
    0,
    (Number(input.offsetWidth) || 0)
      - (Number(input.clientWidth) || 0)
      - cssPixelNumber(style.borderLeftWidth)
      - cssPixelNumber(style.borderRightWidth),
  );
  const horizontalGutter = Math.max(
    0,
    (Number(input.offsetHeight) || 0)
      - (Number(input.clientHeight) || 0)
      - cssPixelNumber(style.borderTopWidth)
      - cssPixelNumber(style.borderBottomWidth),
  );
  return {
    right: cssPixel(cssPixelNumber(style.paddingRight) + verticalGutter),
    bottom: cssPixel(cssPixelNumber(style.paddingBottom) + horizontalGutter),
  };
}

function applyOverlayScrollbarPadding(input, overlay, style = getComputedStyle(input)) {
  const padding = overlayScrollbarPadding(input, style);
  if (overlay.style.paddingRight !== padding.right) overlay.style.paddingRight = padding.right;
  if (overlay.style.paddingBottom !== padding.bottom) overlay.style.paddingBottom = padding.bottom;
}

function overlayBounds(input) {
  return {
    left: `${input.offsetLeft}px`,
    top: `${input.offsetTop}px`,
    width: `${input.offsetWidth}px`,
    height: `${input.offsetHeight}px`,
  };
}

function autocompletePreviewSpanHtml(text, preview, opacity = 0.95) {
  const color = String(preview?.color || "rgba(203, 213, 225, 0.86)");
  return `<span style="font: inherit; line-height: inherit; letter-spacing: inherit; vertical-align: baseline; color: ${escapeHtml(color)}; opacity: ${opacity}">`
    + escapeHtml(text)
    + "</span>";
}

function highlightOverlayPreviewHtml(value, tokens, preview) {
  if (!preview || String(preview.sourceValue || "") !== String(value || "")) {
    return null;
  }
  const text = String(preview.value || "");
  const candidateStart = Math.max(0, Math.min(Number(preview.candidateStart ?? preview.ghostStart) || 0, text.length));
  const candidateEnd = Math.max(candidateStart, Math.min(Number(preview.candidateEnd ?? preview.ghostEnd) || 0, text.length));
  const ghostStart = Math.max(0, Math.min(Number(preview.ghostStart) || 0, text.length));
  const ghostEnd = Math.max(ghostStart, Math.min(Number(preview.ghostEnd) || 0, text.length));
  if (!text || candidateEnd <= candidateStart || ghostEnd <= ghostStart) {
    return null;
  }
  const safeGhostStart = Math.max(candidateStart, Math.min(ghostStart, candidateEnd));
  const safeGhostEnd = Math.max(safeGhostStart, Math.min(ghostEnd, candidateEnd));
  const html = [
    renderHighlightedText(text.slice(0, candidateStart), tokens || []),
    autocompletePreviewSpanHtml(text.slice(candidateStart, safeGhostStart), preview, 0.95),
    autocompletePreviewSpanHtml(text.slice(safeGhostStart, safeGhostEnd), preview, 0.52),
    autocompletePreviewSpanHtml(text.slice(safeGhostEnd, candidateEnd), preview, 0.95),
    renderHighlightedText(text.slice(candidateEnd), tokens || []),
  ].join("");
  return text.endsWith("\n") ? `${html} ` : html;
}

function highlightOverlayHtml(value, tokens, placeholder = "", input = null) {
  const text = String(value || "");
  if (!text) {
    return `<span style="opacity: 0.45">${escapeHtml(placeholder)}</span>`;
  }
  const previewHtml = highlightOverlayPreviewHtml(text, tokens, input?.__easyuseAnimaAutocompletePreview);
  if (previewHtml != null) {
    return previewHtml;
  }
  const html = renderHighlightedText(text, tokens);
  return text.endsWith("\n") ? `${html} ` : html;
}

function copyInputTextMetrics(input, overlay, style = getComputedStyle(input)) {
  for (const property of HIGHLIGHT_TEXT_METRIC_PROPERTIES) {
    const val = style[property];
    if (overlay.style[property] !== val) {
      overlay.style[property] = val;
    }
  }
  overlay.style.boxSizing = "border-box";
  overlay.style.whiteSpace = "pre-wrap";
  overlay.style.overflowWrap = "break-word";
  overlay.style.wordWrap = "break-word";
  overlay.style.wordBreak = "normal";
  overlay.style.margin = "0";
  applyOverlayScrollbarPadding(input, overlay, style);
}

function syncOverlayBounds(input, overlay) {
  if (!overlay) return;
  const style = getComputedStyle(input);
  const { left, top, width, height } = overlayBounds(input);

  if (overlay.style.left !== left) overlay.style.left = left;
  if (overlay.style.top !== top) overlay.style.top = top;
  if (overlay.style.width !== width) overlay.style.width = width;
  if (overlay.style.height !== height) overlay.style.height = height;
  applyOverlayScrollbarPadding(input, overlay, style);

  if (overlay.scrollTop !== input.scrollTop) overlay.scrollTop = input.scrollTop;
  if (overlay.scrollLeft !== input.scrollLeft) overlay.scrollLeft = input.scrollLeft;
}

function requestOverlaySync(input, forceCopyMetrics = false) {
  const overlay = input?.__easyuseAnimaHighlightOverlay;
  if (!overlay) {
    return;
  }
  input.__easyuseAnimaHighlightForceCopyMetrics ||= forceCopyMetrics;
  if (input.__easyuseAnimaHighlightSyncRaf) {
    return;
  }
  input.__easyuseAnimaHighlightSyncRaf = requestAnimationFrame(() => {
    input.__easyuseAnimaHighlightSyncRaf = 0;
    const currentOverlay = input.__easyuseAnimaHighlightOverlay;
    if (!input.isConnected || !currentOverlay?.isConnected) {
      input.__easyuseAnimaHighlightForceCopyMetrics = false;
      return;
    }
    if (input.__easyuseAnimaHighlightForceCopyMetrics) {
      copyInputTextMetrics(input, currentOverlay);
    }
    input.__easyuseAnimaHighlightForceCopyMetrics = false;
    syncOverlayBounds(input, currentOverlay);
    requestAnimationFrame(() => {
      if (input.isConnected && currentOverlay.isConnected) {
        syncOverlayBounds(input, currentOverlay);
      }
    });
  });
}

function installOverlaySyncListeners(input) {
  if (input.__easyuseAnimaHighlightSyncInstalled) {
    return;
  }
  const schedule = () => requestOverlaySync(input);
  const scheduleMetrics = () => requestOverlaySync(input, true);
  input.addEventListener("scroll", schedule, { passive: true });
  input.addEventListener("input", schedule);
  input.addEventListener("keyup", schedule);
  input.addEventListener("click", schedule);
  input.addEventListener("compositionupdate", schedule);
  input.addEventListener("compositionend", scheduleMetrics);
  input.__easyuseAnimaHighlightSyncInstalled = true;
}

function ensureHighlightOverlay(input) {
  input.spellcheck = false;
  input.autocomplete = "off";
  input.setAttribute("autocorrect", "off");
  input.setAttribute("autocapitalize", "off");

  if (input.__easyuseAnimaHighlightOverlay) {
    const overlay = input.__easyuseAnimaHighlightOverlay;
    if (overlay.isConnected && overlay.parentElement === input.parentElement) {
      return overlay;
    }
    overlay.remove?.();
    input.__easyuseAnimaHighlightOverlay = null;
  }

  const parent = input.parentElement;
  if (!parent) {
    return null;
  }
  if (getComputedStyle(parent).position === "static") {
    parent.style.position = "relative";
  }

  const overlay = document.createElement("pre");
  overlay.className = "easyuse-anima-highlight-overlay";
  overlay.setAttribute("aria-hidden", "true");
  overlay.style.cssText = [
    "position: absolute",
    "box-sizing: border-box",
    "margin: 0",
    "overflow: hidden",
    "white-space: pre-wrap",
    "overflow-wrap: break-word",
    "word-break: normal",
    "pointer-events: none",
    "z-index: 0",
    "background: rgba(15, 23, 42, 0.62)",
    "color: var(--input-text, #ddd)",
  ].join("; ");
  copyInputTextMetrics(input, overlay);
  parent.insertBefore(overlay, input);

  ensureHighlightStyle();
  input.classList.add("easyuse-anima-highlight-input");
  input.style.position = input.style.position || "relative";
  input.style.zIndex = "1";
  input.style.background = "transparent";
  input.style.color = "transparent";
  input.style.caretColor = "var(--input-text, #ddd)";
  input.style.webkitTextFillColor = "transparent";
  input.style.whiteSpace = "pre-wrap";
  input.style.overflowWrap = "break-word";
  input.style.wordBreak = "normal";
  input.style.textSizeAdjust = "100%";
  input.style.webkitTextSizeAdjust = "100%";

  input.__easyuseAnimaHighlightOverlay = overlay;
  installOverlaySyncListeners(input);
  installTrainedTagTooltipListeners(input);
  return overlay;
}

let promptHighlightRefreshRaf = 0;

function refreshConnectedHighlightOverlays(applyTextStyle) {
  const inputs = Array.from(document.querySelectorAll(".easyuse-anima-highlight-input"));
  const updates = [];

  // DOM Style Read
  for (const input of inputs) {
    if (!(input instanceof HTMLTextAreaElement || input instanceof HTMLInputElement)) {
      continue;
    }
    applyTextStyle?.(input);
    const overlay = ensureHighlightOverlay(input);
    if (!overlay) {
      continue;
    }

    // Font metrics reads
    const style = getComputedStyle(input);
    const metricValues = {};
    for (const prop of HIGHLIGHT_TEXT_METRIC_PROPERTIES) {
      metricValues[prop] = style[prop];
    }

    // Bounds reads
    const { left, top, width, height } = overlayBounds(input);
    const padding = overlayScrollbarPadding(input, style);
    const scrollTop = input.scrollTop;
    const scrollLeft = input.scrollLeft;

    updates.push({
      overlay,
      metricValues,
      left,
      top,
      width,
      height,
      padding,
      scrollTop,
      scrollLeft
    });
  }

  // DOM Style Write
  for (const update of updates) {
    const { overlay, metricValues, left, top, width, height, padding, scrollTop, scrollLeft } = update;

    // Apply metrics (only if they changed)
    for (const prop in metricValues) {
      const val = metricValues[prop];
      if (overlay.style[prop] !== val) {
        overlay.style[prop] = val;
      }
    }

    // Apply bounds styles (only if they changed)
    if (overlay.style.left !== left) overlay.style.left = left;
    if (overlay.style.top !== top) overlay.style.top = top;
    if (overlay.style.width !== width) overlay.style.width = width;
    if (overlay.style.height !== height) overlay.style.height = height;
    overlay.style.boxSizing = "border-box";
    overlay.style.whiteSpace = "pre-wrap";
    overlay.style.overflowWrap = "break-word";
    overlay.style.wordWrap = "break-word";
    overlay.style.wordBreak = "normal";
    if (overlay.style.paddingRight !== padding.right) overlay.style.paddingRight = padding.right;
    if (overlay.style.paddingBottom !== padding.bottom) overlay.style.paddingBottom = padding.bottom;
    if (overlay.scrollTop !== scrollTop) overlay.scrollTop = scrollTop;
    if (overlay.scrollLeft !== scrollLeft) overlay.scrollLeft = scrollLeft;
  }
}

function requestConnectedHighlightOverlayRefresh(applyTextStyle) {
  if (promptHighlightRefreshRaf) {
    return;
  }
  promptHighlightRefreshRaf = requestAnimationFrame(() => {
    promptHighlightRefreshRaf = 0;
    refreshConnectedHighlightOverlays(applyTextStyle);
    setTimeout(() => refreshConnectedHighlightOverlays(applyTextStyle), 80);
  });
}

function installPromptHighlightOverlayRefresh(app, applyTextStyle) {
  if (window.__easyuseAnimaHighlightOverlayRefreshInstalled) {
    return;
  }
  window.__easyuseAnimaHighlightOverlayRefreshInstalled = true;
  const schedule = () => requestConnectedHighlightOverlayRefresh(applyTextStyle);
  window.addEventListener("focus", schedule);
  window.addEventListener("resize", schedule);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
      schedule();
    }
  });
  const installCanvasListeners = () => {
    const canvas = app?.canvas?.canvas;
    if (!canvas || canvas.__easyuseAnimaHighlightRefreshInstalled) {
      return;
    }
    canvas.__easyuseAnimaHighlightRefreshInstalled = true;
    canvas.addEventListener("pointerup", schedule, { passive: true });
    canvas.addEventListener("wheel", schedule, { passive: true });
  };
  installCanvasListeners();
  setTimeout(installCanvasListeners, 250);
}

function refreshAllPromptHighlights(app, hooks, forceCopyMetrics = false) {
  const {
    findWidget,
    isAdvancedNode,
    scheduleAdvancedHighlights,
    studioFieldNames,
    updateHighlight,
  } = hooks || {};
  for (const node of app?.graph?._nodes || []) {
    if (isAdvancedNode?.(node)) {
      scheduleAdvancedHighlights?.(node, { forceCopyMetrics });
      continue;
    }
    for (const name of studioFieldNames?.(node) || []) {
      const widget = findWidget?.(node, name);
      if (widget) {
        updateHighlight?.(node, widget, widget.__easyuseAnimaTokens || [], forceCopyMetrics);
      }
    }
  }
}

export {
  classifyPrompt,
  copyInputTextMetrics,
  ensureHighlightOverlay,
  hasHighlightSyntax,
  highlightOverlayHtml,
  installPromptHighlightOverlayRefresh,
  overlayBounds,
  overlayScrollbarPadding,
  refreshAllPromptHighlights,
  refreshConnectedHighlightOverlays,
  renderHighlightedText,
  requestConnectedHighlightOverlayRefresh,
  requestOverlaySync,
  syncOverlayBounds,
};
