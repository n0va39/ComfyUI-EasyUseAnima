import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

const textModel = await import(dataModule("../web/js/autocomplete/text_model.js"));

assert.deepEqual(Object.keys(textModel).sort(), [
  "artistCompletionText",
  "autocompleteQuery",
  "completionEditRangeContract",
  "currentToken",
  "currentWildcardToken",
  "isCaretInComment",
  "isCaretInPromptTranslationMarker",
  "normalizeAutocompleteArtistPrefix",
  "normalizeAutocompleteCommitMode",
  "normalizeWildcardSearchText",
  "parseAutocompleteText",
  "planAutocompleteInsertion",
  "planBracketInsertion",
  "wildcardAutocompleteQuery",
].sort());

const {
  artistCompletionText,
  autocompleteQuery,
  completionEditRangeContract,
  currentToken,
  currentWildcardToken,
  isCaretInComment,
  isCaretInPromptTranslationMarker,
  normalizeAutocompleteArtistPrefix,
  normalizeAutocompleteCommitMode,
  normalizeWildcardSearchText,
  parseAutocompleteText,
  planAutocompleteInsertion,
  planBracketInsertion,
  wildcardAutocompleteQuery,
} = textModel;

function contractRanges(value, marker, options = {}) {
  const caret = value.indexOf(marker);
  assert.notEqual(caret, -1);
  const text = value.replace(marker, "");
  return completionEditRangeContract(text, caret, {
    detectNaturalSentences: false,
    ...options,
  });
}

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

function appliedBracketPlan(value, selectionStart, selectionEnd, key, options = {}) {
  const plan = planBracketInsertion(
    value,
    selectionStart,
    selectionEnd,
    key,
    options,
  );
  assert.ok(plan);
  return {
    ...plan,
    value: value.slice(0, plan.start)
      + plan.replacement
      + value.slice(plan.end),
    selectionStart: plan.start + plan.selectionStartOffset,
    selectionEnd: plan.start + plan.selectionEndOffset,
  };
}

function completionToken(value, marker, options = {}) {
  const caret = value.indexOf(marker);
  assert.notEqual(caret, -1);
  const text = value.replace(marker, "");
  return currentToken(text, caret, {
    detectNaturalSentences: false,
    previewCompletion: true,
    ...options,
  });
}

const whitespaceSuffix = contractRanges("blue ha|ir solo", "|");
assert.deepEqual(
  {
    query: [
      whitespaceSuffix.queryStart,
      whitespaceSuffix.queryEnd,
    ],
    insert: [
      whitespaceSuffix.insertStart,
      whitespaceSuffix.insertEnd,
    ],
    replace: [
      whitespaceSuffix.replaceStart,
      whitespaceSuffix.replaceEnd,
    ],
    protectedSuffix: whitespaceSuffix.value.slice(
      whitespaceSuffix.protectedSuffixStart,
    ),
    item: [whitespaceSuffix.itemStart, whitespaceSuffix.itemEnd],
    group: [
      whitespaceSuffix.groupKind,
      whitespaceSuffix.groupStart,
      whitespaceSuffix.groupEnd,
    ],
  },
  {
    query: [0, "blue ha".length],
    insert: [0, "blue ha".length],
    replace: [0, "blue hair".length],
    protectedSuffix: " solo",
    item: [0, "blue hair solo".length],
    group: ["root", 0, "blue hair solo".length],
  },
);

for (const [value, expectedSuffix] of [
  ["foo|, bar", ", bar"],
  ["foo|\nbar", "\nbar"],
]) {
  const ranges = contractRanges(value, "|");
  assert.equal(ranges.replaceEnd, "foo".length);
  assert.equal(ranges.value.slice(ranges.protectedSuffixStart), expectedSuffix);
}

const parenthesisGroup = contractRanges("(foo|, bar:1.2)", "|");
assert.deepEqual(
  {
    range: [
      parenthesisGroup.replaceStart,
      parenthesisGroup.replaceEnd,
    ],
    suffix: parenthesisGroup.value.slice(
      parenthesisGroup.protectedSuffixStart,
    ),
    item: [parenthesisGroup.itemStart, parenthesisGroup.itemEnd],
    group: [
      parenthesisGroup.groupKind,
      parenthesisGroup.groupStart,
      parenthesisGroup.groupEnd,
    ],
  },
  {
    range: [1, 4],
    suffix: ", bar:1.2)",
    item: [1, 4],
    group: ["parenthesis", 1, "(foo, bar:1.2".length],
  },
);

const artistGroup = contractRanges(
  "[[artist_a, art|ist_b:0.7]]",
  "|",
);
assert.deepEqual(
  {
    query: [artistGroup.queryStart, artistGroup.queryEnd],
    replace: [artistGroup.replaceStart, artistGroup.replaceEnd],
    suffix: artistGroup.value.slice(artistGroup.protectedSuffixStart),
    item: [artistGroup.itemStart, artistGroup.itemEnd],
    group: [
      artistGroup.groupKind,
      artistGroup.groupStart,
      artistGroup.groupEnd,
    ],
  },
  {
    query: [12, 15],
    replace: [12, 20],
    suffix: ":0.7]]",
    item: [11, 24],
    group: ["double-bracket", 2, 24],
  },
);

const escapedGroup = contractRanges("\\(foo| bar\\)", "|");
assert.equal(escapedGroup.groupKind, "root");
assert.equal(escapedGroup.replaceEnd, "\\(foo".length);
assert.equal(
  escapedGroup.value.slice(escapedGroup.protectedSuffixStart),
  " bar\\)",
);

const braceChoice = contractRanges("{choice_a|cho^ice_b}", "^");
assert.deepEqual(
  {
    query: [braceChoice.queryStart, braceChoice.queryEnd],
    replace: [braceChoice.replaceStart, braceChoice.replaceEnd],
    suffix: braceChoice.value.slice(braceChoice.protectedSuffixStart),
    item: [braceChoice.itemStart, braceChoice.itemEnd],
    groupKind: braceChoice.groupKind,
  },
  {
    query: ["{choice_a|".length, "{choice_a|cho".length],
    replace: ["{choice_a|".length, "{choice_a|choice_b".length],
    suffix: "}",
    item: ["{choice_a|".length, "{choice_a|choice_b".length],
    groupKind: "brace",
  },
);

const selectedRange = completionEditRangeContract(
  "(first, second)",
  "(first, second".length,
  {
    selectionStart: "(first, ".length,
    selectionEnd: "(first, second".length,
  },
);
assert.deepEqual(
  {
    query: [selectedRange.queryStart, selectedRange.queryEnd],
    insert: [selectedRange.insertStart, selectedRange.insertEnd],
    replace: [selectedRange.replaceStart, selectedRange.replaceEnd],
    group: [
      selectedRange.groupKind,
      selectedRange.groupStart,
      selectedRange.groupEnd,
    ],
  },
  {
    query: [8, 14],
    insert: [8, 14],
    replace: [8, 14],
    group: ["parenthesis", 1, 14],
  },
);

const unweightedSelection = appliedBracketPlan("tag", 0, 3, "(");
assert.deepEqual(
  {
    value: unweightedSelection.value,
    selection: [
      unweightedSelection.selectionStart,
      unweightedSelection.selectionEnd,
    ],
    insertedWeight: unweightedSelection.insertedWeight,
  },
  {
    value: "(tag)",
    selection: [4, 4],
    insertedWeight: false,
  },
);

const weightedSelection = appliedBracketPlan(
  "tag",
  0,
  3,
  "(",
  { selectionParenthesisWeight: true },
);
assert.deepEqual(
  {
    value: weightedSelection.value,
    selected: weightedSelection.value.slice(
      weightedSelection.selectionStart,
      weightedSelection.selectionEnd,
    ),
    insertedWeight: weightedSelection.insertedWeight,
  },
  {
    value: "(tag:1)",
    selected: "1",
    insertedWeight: true,
  },
);

for (const [selected, expected, selectedWeight] of [
  ["tag:1.2", "(tag:1.2)", "1.2"],
  ["(tag:1.2)", "((tag:1.2):1)", "1"],
  ["tag\\:1.2", "(tag\\:1.2:1)", "1"],
  ["first\nsecond", "(first\nsecond:1)", "1"],
]) {
  const plan = appliedBracketPlan(
    selected,
    0,
    selected.length,
    "(",
    { selectionParenthesisWeight: true },
  );
  assert.equal(plan.value, expected);
  assert.equal(
    plan.value.slice(plan.selectionStart, plan.selectionEnd),
    selectedWeight,
  );
}

for (const [key, expected] of [
  ["{", "{choice_a|choice_b}"],
  ["[", "[[choice_a|choice_b]]"],
]) {
  const selected = "choice_a|choice_b";
  const plan = appliedBracketPlan(selected, 0, selected.length, key);
  assert.equal(plan.value, expected);
  assert.equal(plan.selectionStart, expected.length - (key === "[" ? 2 : 1));
  assert.equal(plan.selectionEnd, plan.selectionStart);
}

const emptyParenthesis = appliedBracketPlan("", 0, 0, "(", {
  selectionParenthesisWeight: true,
});
assert.deepEqual(
  {
    value: emptyParenthesis.value,
    selection: [emptyParenthesis.selectionStart, emptyParenthesis.selectionEnd],
  },
  { value: "()", selection: [1, 1] },
);

const doubleBracket = appliedBracketPlan("[", 1, 1, "[");
assert.deepEqual(
  {
    value: doubleBracket.value,
    selection: [doubleBracket.selectionStart, doubleBracket.selectionEnd],
  },
  { value: "[[]]", selection: [2, 2] },
);
assert.equal(planBracketInsertion("", 0, 0, "["), null);
assert.equal(planBracketInsertion("", 0, 0, "x"), null);

assert.equal(normalizeAutocompleteCommitMode("smart"), "smart");
assert.equal(normalizeAutocompleteCommitMode("insert"), "insert");
assert.equal(normalizeAutocompleteCommitMode("replace"), "replace");
assert.equal(normalizeAutocompleteCommitMode("INVALID"), "smart");

const smartWhitespace = appliedPlan(
  completionToken("blue ha|ir solo", "|"),
  "blue hair",
  { commitMode: "smart" },
);
assert.equal(smartWhitespace.value, "blue hair solo");
assert.equal(smartWhitespace.editRange, "replace");
assert.equal(smartWhitespace.modeUsed, "smart");
assert.equal(smartWhitespace.preservedSuffix, " solo");

for (const [value, insert, expected] of [
  ["foo|, bar", "foo tag", "foo tag, bar"],
  ["foo|\nbar", "foo tag", "foo tag\nbar"],
  ["(foo|, bar:1.2)", "foo tag", "(foo tag, bar:1.2)"],
  [
    "[[artist_a, art|ist_b:0.7]]",
    "artist b",
    "[[artist_a, artist b:0.7]]",
  ],
]) {
  const plan = appliedPlan(
    completionToken(value, "|"),
    insert,
    { commitMode: "smart" },
  );
  assert.equal(plan.value, expected);
  assert.equal(plan.editRange, "replace");
}

const smartContiguousTail = appliedPlan(
  completionToken("old_t|ag", "|"),
  "old tag",
  { commitMode: "smart" },
);
assert.equal(smartContiguousTail.value, "old tag");
assert.equal(smartContiguousTail.editRange, "replace");

const smartAmbiguousTail = appliedPlan(
  completionToken("old_t|ail", "|"),
  "old train",
  { commitMode: "smart" },
);
assert.equal(smartAmbiguousTail.value, "old train, ail");
assert.equal(smartAmbiguousTail.editRange, "insert");
assert.equal(smartAmbiguousTail.preservedSuffix, "ail");

const insertTail = appliedPlan(
  completionToken("old_t|ag", "|"),
  "old tag",
  { commitMode: "insert" },
);
assert.equal(insertTail.value, "old tag, ag");
assert.equal(insertTail.editRange, "insert");
assert.equal(insertTail.preservedSuffix, "ag");

const replaceTail = appliedPlan(
  completionToken("old_t|ail", "|"),
  "old train",
  { commitMode: "replace" },
);
assert.equal(replaceTail.value, "old train");
assert.equal(replaceTail.editRange, "replace");
assert.equal(replaceTail.preservedSuffix, "");

const previewPlan = planAutocompleteInsertion(
  completionToken("(foo|, bar:1.2)", "|"),
  "foo tag",
  { commitMode: "smart" },
);
const commitPlan = planAutocompleteInsertion(
  completionToken("(foo|, bar:1.2)", "|"),
  "foo tag",
  { commitMode: "smart" },
);
assert.deepEqual(previewPlan, commitPlan);

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
  "alpha. beta tag gamma. delta",
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
  assert.equal(appliedPlan(token, "new tag").value, "((new tag, _tag:1.2))");
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
assert.deepEqual(parseAutocompleteText("((artist:artist_name))", "artist:"), {
  query: "artist_name",
  artistOnly: true,
});
assert.deepEqual(parseAutocompleteText("((@artist_name))", "artist:"), {
  query: "@artist_name",
  artistOnly: false,
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
assert.deepEqual(
  autocompleteQuery({ query: "artist:custom_name" }, false, "artist:"),
  {
    query: "custom_name",
    artistOnly: true,
    category: "artist",
  },
);
assert.equal(normalizeAutocompleteArtistPrefix(undefined), "@");
assert.equal(normalizeAutocompleteArtistPrefix("  artist:  "), "artist:");
for (const invalidPrefix of ["", " ", "bad,prefix", "bad\nprefix", "\u0000bad", "x".repeat(33)]) {
  assert.equal(normalizeAutocompleteArtistPrefix(invalidPrefix), "@");
}
assert.equal(artistCompletionText("artist name"), "@artist name");
assert.equal(artistCompletionText("@artist name"), "@artist name");
assert.equal(artistCompletionText("artist name", "artist:"), "artist:artist name");
assert.equal(artistCompletionText("artist:artist name", "artist:"), "artist:artist name");
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
    preservedSuffix: "",
    modeUsed: "smart",
    editRange: "replace",
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
