import { readFileSync } from "node:fs";

const source = readFileSync(
  new URL("../web/js/prompt_studio/highlight_revision.js", import.meta.url),
  "utf8",
);
const moduleUrl = `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
const {
  highlightRequestOwnsText,
  highlightTokensForText,
} = await import(moduleUrl);

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

const tokensA = [{ token: "text A", section: "general" }];
assert(
  highlightTokensForText("text A", "text A", tokensA) === tokensA,
  "Matching text must keep its classification token identity",
);
assert(
  highlightTokensForText("text B", "text A", tokensA).length === 0,
  "Pasted text must not render the previous text token cache",
);
assert(
  highlightTokensForText("text A", "text A", null).length === 0,
  "Malformed token caches must fail closed",
);

const requestA = { sequence: 1, text: "text A" };
assert(
  highlightRequestOwnsText(requestA, 1, "text A"),
  "Matching sequence and text must own the highlight result",
);
assert(
  !highlightRequestOwnsText(requestA, 1, "text B"),
  "A response must become stale as soon as paste changes the text",
);
assert(
  !highlightRequestOwnsText(requestA, 2, "text A"),
  "A superseded request sequence must not publish",
);
assert(
  !highlightRequestOwnsText(requestA, 1, "text A", false),
  "A disconnected textarea must not receive a result",
);

const requestB = { sequence: 2, text: "text B" };
const requestC = { sequence: 3, text: "text C" };
assert(
  !highlightRequestOwnsText(requestA, 3, "text C")
    && !highlightRequestOwnsText(requestB, 3, "text C")
    && highlightRequestOwnsText(requestC, 3, "text C"),
  "Rapid A to B to C input must leave only C as the publishing owner",
);

console.log("Prompt Studio highlight revision smoke passed.");
