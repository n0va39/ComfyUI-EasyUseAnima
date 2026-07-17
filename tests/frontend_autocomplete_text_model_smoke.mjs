import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

const textModel = await import(dataModule("../web/js/autocomplete/text_model.js"));

assert.deepEqual(Object.keys(textModel).sort(), [
  "autocompleteQuery",
  "currentToken",
  "currentWildcardToken",
  "isCaretInComment",
  "isCaretInPromptTranslationMarker",
  "normalizeWildcardSearchText",
  "parseAutocompleteText",
  "planAutocompleteInsertion",
  "wildcardAutocompleteQuery",
].sort());

const {
  autocompleteQuery,
  currentToken,
  currentWildcardToken,
  isCaretInComment,
  isCaretInPromptTranslationMarker,
  normalizeWildcardSearchText,
  parseAutocompleteText,
  planAutocompleteInsertion,
  wildcardAutocompleteQuery,
} = textModel;

function appliedPlan(token, insert, options = {}) {
  const plan = planAutocompleteInsertion(token, insert, options);
  assert.ok(plan);
  return {
    ...plan,
    value: token.value.slice(0, plan.start)
      + plan.replacement
      + token.value.slice(plan.end),
    caret: plan.start + plan.caretOffset,
  };
}

const segmented = currentToken(
  "first tag, second tag\nthird tag",
  "first tag, second".length,
  { detectNaturalSentences: false, previewCompletion: true },
);
assert.equal(segmented.start, "first tag, ".length);
assert.equal(segmented.end, "first tag, second tag".length);
assert.equal(segmented.query, "second");
assert.equal(segmented.tokenSegment, "second tag");
assert.equal(segmented.active, true);

for (const period of [".", "。", "．", "｡"]) {
  const value = "alpha" + period + " beta gamma";
  const caret = value.indexOf("beta") + "beta".length;
  const token = currentToken(value, caret, {
    detectNaturalSentences: true,
    previewCompletion: true,
  });
  assert.equal(token.start, value.indexOf("beta"));
  assert.equal(token.query, "beta");
  assert.equal(token.sentenceDelimited, true);
}

const sentenceValue = "alpha. beta gamma";
const sentenceCaret = sentenceValue.indexOf("beta") + "beta".length;
assert.equal(
  currentToken(sentenceValue, sentenceCaret, {
    detectNaturalSentences: false,
    previewCompletion: true,
  }).query,
  "alpha. beta",
);
assert.equal(
  currentToken("version 1.5 beta", "version 1.5 beta".length, {
    detectNaturalSentences: true,
    previewCompletion: true,
  }).sentenceDelimited,
  false,
);
assert.equal(
  currentToken("alpha\\. beta", "alpha\\. beta".length, {
    detectNaturalSentences: true,
    previewCompletion: true,
  }).sentenceDelimited,
  false,
);

const boundedSentenceValue = "alpha. beta gamma. delta";
const boundedSentenceToken = currentToken(
  boundedSentenceValue,
  boundedSentenceValue.indexOf("beta") + "beta".length,
  { detectNaturalSentences: true, previewCompletion: true },
);
assert.equal(boundedSentenceToken.start, boundedSentenceValue.indexOf("beta"));
assert.equal(boundedSentenceToken.end, boundedSentenceValue.indexOf(". delta"));
assert.equal(
  appliedPlan(
    boundedSentenceToken,
    "beta tag",
    { appendSeparator: false, noCommaAfterPeriod: true },
  ).value,
  "alpha. beta tag. delta",
);

const weightedValue = "[[ @old_name:1.25]]";
const weightedCaret = weightedValue.indexOf(":");
const weightedToken = currentToken(weightedValue, weightedCaret, {
  detectNaturalSentences: true,
  previewCompletion: true,
});
assert.equal(weightedToken.start, weightedValue.indexOf("@"));
assert.equal(weightedToken.end, weightedValue.indexOf(":"));
assert.equal(weightedToken.query, "@old_name");
assert.equal(weightedToken.tokenSegment, "@old_name");
assert.equal(
  appliedPlan(weightedToken, "@new_name").value,
  "[[ @new_name:1.25]]",
);

for (const previewCompletion of [false, true]) {
  for (const [value, typed, insert, expected, artistOnly] of [
    ["((old_tag))", "old_tag", "new tag", "((new tag))", false],
    ["(((old_tag)))", "old_tag", "new tag", "(((new tag)))", false],
    ["((old_tag:1.2))", "old_tag", "new tag", "((new tag:1.2))", false],
    ["((@old_artist))", "@old_artist", "@new artist", "((@new artist))", true],
    ["manual_trigger, ((old_tag))", "old_tag", "new tag", "manual_trigger, ((new tag))", false],
  ]) {
    const start = value.indexOf(typed);
    const caret = start + typed.length;
    const token = currentToken(value, caret, {
      detectNaturalSentences: false,
      previewCompletion,
    });
    const query = autocompleteQuery(token);
    assert.equal(token.start, start);
    assert.equal(token.end, caret);
    assert.equal(query.artistOnly, artistOnly);
    assert.equal(query.query, typed.replace(/^@/, ""));
    const applied = appliedPlan(token, insert);
    assert.equal(applied.value, expected);
    assert.equal(applied.caret, start + insert.length);
    assert.equal(applied.value.slice(applied.caret), expected.slice(start + insert.length));
  }
}

for (const previewCompletion of [false, true]) {
  const value = "((old_tag:1.2))";
  const start = value.indexOf("old_tag");
  const token = currentToken(value, start + "old".length, {
    detectNaturalSentences: false,
    previewCompletion,
  });
  assert.equal(autocompleteQuery(token).query, "old");
  assert.equal(token.start, start);
  assert.equal(token.end, start + "old_tag".length);
  assert.equal(appliedPlan(token, "new tag").value, "((new tag:1.2))");
}

const strictAtClosing = currentToken(
  weightedValue,
  weightedValue.length,
  { detectNaturalSentences: true, previewCompletion: true },
);
const legacyAtClosing = currentToken(
  weightedValue,
  weightedValue.length,
  { detectNaturalSentences: true, previewCompletion: false },
);
assert.equal(strictAtClosing.active, false);
assert.equal(strictAtClosing.query, "@old_name");
assert.equal(legacyAtClosing.active, true);
assert.equal(legacyAtClosing.query, weightedValue);

const escapedLiteral = "\\(blue archive\\)";
const escapedToken = currentToken(
  escapedLiteral,
  escapedLiteral.length,
  { detectNaturalSentences: true, previewCompletion: true },
);
assert.equal(escapedToken.start, 0);
assert.equal(escapedToken.end, escapedLiteral.length);
assert.equal(escapedToken.query, escapedLiteral);

assert.deepEqual(parseAutocompleteText("(@artist_name):1.25"), {
  query: "artist_name",
  artistOnly: true,
});
assert.deepEqual(parseAutocompleteText("[[ (@artist_name)))"), {
  query: "artist_name",
  artistOnly: true,
});
assert.deepEqual(parseAutocompleteText("((@artist_name))"), {
  query: "artist_name",
  artistOnly: true,
});
assert.deepEqual(autocompleteQuery({ query: "(@artist_name):1.25" }), {
  query: "artist_name",
  artistOnly: true,
  category: "artist",
});
assert.deepEqual(autocompleteQuery({ query: "general_tag" }, true), {
  query: "general_tag",
  artistOnly: true,
  category: "artist",
});
assert.deepEqual(wildcardAutocompleteQuery({ query: "Folder/표정" }), {
  query: "folder/표정",
  artistOnly: false,
  category: "wildcard",
  kind: "wildcard",
});
assert.equal(
  normalizeWildcardSearchText("Ａ＿Ｂ\\Folder Name"),
  "a-b/folder-name",
);

assert.deepEqual(
  {
    query: currentWildcardToken("__", 2)?.query,
    active: currentWildcardToken("__", 2)?.active,
  },
  { query: "", active: true },
);
const unicodeWildcard = "prefix __캐릭터/표정";
assert.equal(
  currentWildcardToken(unicodeWildcard, unicodeWildcard.length)?.query,
  "캐릭터/표정",
);
const closedWildcard = "__foo__";
assert.equal(currentWildcardToken(closedWildcard, closedWildcard.length), null);
assert.equal(currentWildcardToken(closedWildcard, 4)?.end, closedWildcard.length);
const secondWildcard = "__one__ + __two";
assert.equal(
  currentWildcardToken(secondWildcard, secondWildcard.length)?.query,
  "two",
);
assert.equal(currentWildcardToken("__bad,query", "__bad,query".length), null);
assert.equal(currentWildcardToken("__bad\nquery", "__bad\nquery".length), null);

const marker = "before %{inside} after";
assert.equal(
  isCaretInPromptTranslationMarker(marker, marker.indexOf("inside") + 3),
  true,
);
assert.equal(
  isCaretInPromptTranslationMarker(marker, marker.indexOf("}") + 1),
  false,
);
assert.equal(
  isCaretInPromptTranslationMarker("before %{inside", "before %{inside".length),
  true,
);
assert.equal(
  isCaretInPromptTranslationMarker("\\%{escaped}", "\\%{escaped}".length - 1),
  false,
);
assert.equal(isCaretInComment("  # comment", "  # comment".length), true);
assert.equal(isCaretInComment("tag # inline", "tag # inline".length), false);
assert.equal(isCaretInComment("tag\n\t# next", "tag\n\t# next".length), true);

const emptyToken = currentToken("", 0, {
  detectNaturalSentences: true,
  previewCompletion: true,
});
assert.deepEqual(
  appliedPlan(emptyToken, "tag", {
    appendSeparator: true,
    noCommaAfterPeriod: true,
  }),
  {
    start: 0,
    end: 0,
    replacement: "tag, ",
    caretOffset: 5,
    prefix: "",
    suffix: ", ",
    consumeAfter: 0,
    caretExtra: 2,
    value: "tag, ",
    caret: 5,
  },
);

const commaValue = "foo,bar";
const commaToken = currentToken(commaValue, commaValue.length, {
  detectNaturalSentences: false,
  previewCompletion: true,
});
assert.equal(appliedPlan(commaToken, "baz").value, "foo, baz");

const newlineValue = "foo\nbar";
const newlineToken = currentToken(newlineValue, newlineValue.length, {
  detectNaturalSentences: false,
  previewCompletion: true,
});
assert.equal(appliedPlan(newlineToken, "baz").value, "foo\nbaz");

const afterPeriod = {
  value: "sentence.old",
  start: "sentence.".length,
  end: "sentence.old".length,
};
assert.equal(
  appliedPlan(afterPeriod, "new", { noCommaAfterPeriod: true }).value,
  "sentence. new",
);
assert.equal(
  appliedPlan(afterPeriod, "new", { noCommaAfterPeriod: false }).value,
  "sentence., new",
);

for (const [value, start, end, expected] of [
  ["(old)", 1, 4, "(new)"],
  ["[[old]]", 2, 5, "[[new]]"],
  ["old:1.25", 0, 3, "new:1.25"],
  ["old,next", 0, 3, "new,next"],
  ["old\nnext", 0, 3, "new\nnext"],
  ["old. next", 0, 3, "new. next"],
]) {
  assert.equal(
    appliedPlan(
      { value, start, end },
      "new",
      { appendSeparator: false, noCommaAfterPeriod: true },
    ).value,
    expected,
  );
}

const regressionValue = "wisteria,dd";
const regressionToken = currentToken(regressionValue, "wisteria".length, {
  detectNaturalSentences: false,
  previewCompletion: true,
});
const regression = appliedPlan(regressionToken, "wisteria", {
  appendSeparator: true,
  noCommaAfterPeriod: true,
});
assert.equal(regression.value, "wisteria, dd");
assert.equal(regression.caret, "wisteria, ".length);
assert.equal(regression.value.slice(regression.caret), "dd");

const normalizedSeparator = appliedPlan(
  { value: "old,   tail", start: 0, end: 3 },
  "new",
  { appendSeparator: true, noCommaAfterPeriod: true },
);
assert.equal(normalizedSeparator.value, "new, tail");
assert.equal(normalizedSeparator.consumeAfter, 4);
assert.equal(normalizedSeparator.caret, "new, ".length);

const wildcardToken = currentWildcardToken("__old/path__", "__old".length);
assert.ok(wildcardToken);
assert.deepEqual(
  appliedPlan(wildcardToken, "__new/path__"),
  {
    start: 0,
    end: "__old/path__".length,
    replacement: "__new/path__",
    caretOffset: "__new/path__".length,
    prefix: "",
    suffix: "",
    consumeAfter: 0,
    caretExtra: 0,
    value: "__new/path__",
    caret: "__new/path__".length,
  },
);

const frozenToken = Object.freeze({
  value: "old",
  start: 0,
  end: 3,
  wildcard: false,
});
const frozenOptions = Object.freeze({
  appendSeparator: true,
  noCommaAfterPeriod: true,
});
assert.doesNotThrow(() => planAutocompleteInsertion(frozenToken, "new", frozenOptions));
assert.deepEqual(frozenToken, {
  value: "old",
  start: 0,
  end: 3,
  wildcard: false,
});
assert.deepEqual(frozenOptions, {
  appendSeparator: true,
  noCommaAfterPeriod: true,
});

assert.equal(planAutocompleteInsertion(null, "unused"), null);
