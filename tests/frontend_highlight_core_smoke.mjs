import { readFileSync } from "node:fs";

const webJsRoot = new URL("../web/js/", import.meta.url);
const rulesSource = readFileSync(
  new URL("easyuse_anima_prompt_rules.js", webJsRoot),
  "utf8",
);
const rulesUrl = `data:text/javascript;base64,${Buffer.from(rulesSource).toString("base64")}`;
const coreSource = readFileSync(
  new URL("prompt_studio/highlight_core.js", webJsRoot),
  "utf8",
).replace("../easyuse_anima_prompt_rules.js", rulesUrl);
const coreUrl = `data:text/javascript;base64,${Buffer.from(coreSource).toString("base64")}`;
const { createPromptHighlightRenderer } = await import(coreUrl);

const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;");
const tokenStyle = (token) => `section:${token?.section || "unknown"}`;
const tokenSpanHtml = (text, token) => (
  `<token section="${token?.section || "unknown"}">${escapeHtml(text)}</token>`
);

function renderer(preferSyntaxBeforeToken) {
  return createPromptHighlightRenderer({
    escapeHtml,
    sectionLabel: (section) => String(section),
    tokenStyle,
    tokenSpanHtml,
    weightSyntaxUnderlineEnabled: () => false,
    preferSyntaxBeforeToken,
  });
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

const regional = renderer(true);
const modular = renderer(false);
const wildcardToken = {
  token: "__한글__",
  base: "__한글__",
  section: "general",
  learned: true,
};

assert(regional("__한글__", []).includes("section:wildcard"), "Unicode wildcard was not highlighted");
assert(regional("{red|blue}", []).includes("section:wildcard"), "Dynamic prompt was not highlighted");
assert(
  regional(
    "(artist_name:1.25)",
    [{ token: "artist_name", base: "artist_name", section: "artist", weighted: true }],
  ).includes('<token section="artist">artist_name</token>'),
  "Weighted token body was not preserved",
);
assert(
  regional("[[artist_a, artist_b:0.7]]", [
    { token: "artist_a", base: "artist_a", section: "artist" },
    { token: "artist_b", base: "artist_b", section: "artist" },
  ]).includes("color: #fb923c"),
  "Artist mix weight was not highlighted",
);
assert(regional("__한글__", [wildcardToken]).includes("section:wildcard"), "Regional syntax priority changed");
assert(modular("__한글__", [wildcardToken]).includes('<token section="general">'), "Modular token priority changed");
assert(
  regional("<lora:styles/portrait.safetensors:0.8>", []).includes("section:lora"),
  "Canonical LoRA syntax was not highlighted separately",
);
assert(
  regional("<<lora:styles/portrait:0.8:0.6>", []).includes("section:lora"),
  "Tolerated doubled LoRA opener was not highlighted separately",
);
assert(regional("<:portrait", []).includes("section:lora"), "LoRA autocomplete trigger was not highlighted");
assert(
  modular(
    "<lora:styles/portrait:1.0>",
    [{ token: "<lora:styles/portrait:1.0>", base: "<lora:styles/portrait:1.0>", section: "unknown" }],
  ).includes("section:lora"),
  "LoRA syntax must keep priority over backend tag classification",
);
assert(
  !regional("<|> <|> <|start_of_text|>", []).includes("section:lora"),
  "Angle-pipe tags must not be classified as LoRA syntax",
);

console.log("Highlight core smoke passed.");
