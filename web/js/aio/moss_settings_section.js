// @ts-check

/**
 * MOSS owns this settings bank; the containing dialog owns Apply/Cancel and
 * serialization. Building or editing this section never executes a model.
 *
 * @param {any} dependencies
 * @param {any} settings
 */
export function aioCreateMossSettingsSection(dependencies, settings) {
  if (settings.model_family !== "moss_image") return null;
  const { document, controls, text, defaults, mergeDefaults, normalizeSeed } = dependencies;
  const { field, numberInput, checkbox, textInput, selectInput } = controls;
  const bank = mergeDefaults(defaults, settings.model_settings?.moss_image || {});
  const section = document.createElement("section");
  section.className = "easyuse-anima-aio-section full";
  section.append(Object.assign(document.createElement("h3"), { textContent: text("moss.section") }));

  const note = (parent, key) => {
    const element = document.createElement("p");
    element.className = "easyuse-anima-aio-warning";
    element.textContent = text(key);
    parent.append(element);
    return element;
  };
  const details = (parent, key) => {
    const element = document.createElement("details");
    element.className = "easyuse-anima-aio-subsection";
    element.append(Object.assign(document.createElement("summary"), { textContent: text(key) }));
    parent.append(element);
    return element;
  };
  const control = (parent, path, label, input, tip = "") => {
    input.setAttribute("data-moss-setting", path);
    return field(parent, text(label), input, tip);
  };
  const modeSelect = (current, prefix, ids) => {
    const options = ids.map((id) => ({ value: id, label: text(`${prefix}.${id}`) }));
    if (!ids.includes(current)) options.push({ value: current, label: current });
    return selectInput(options, current);
  };
  const slgMode = control(section, "slg.mode", "moss.slg.mode",
    modeSelect(bank.slg.mode, "moss.slg", ["off", "uncond", "standard"]), "moss.slg.hint");
  const slgHint = note(section, "moss.slg.hint");
  const slgDetails = details(section, "moss.slg.advanced");
  const layers = control(slgDetails, "slg.layers", "moss.slg.layers", textInput(bank.slg.layers));
  const scale = control(slgDetails, "slg.scale", "moss.slg.scale", numberInput(bank.slg.scale, "0.1"));
  scale.min = "0";
  scale.max = "10";
  const start = control(slgDetails, "slg.start_percent", "moss.slg.start", numberInput(bank.slg.start_percent, "0.01"));
  const end = control(slgDetails, "slg.end_percent", "moss.slg.end", numberInput(bank.slg.end_percent, "0.01"));
  for (const input of [start, end]) {
    input.min = "0";
    input.max = "1";
  }
  const stages = Object.fromEntries(["first_pass", "highres", "detailer", "upscale"].map((id) => [id,
    control(slgDetails, `slg.stage_scope.${id}`, `moss.stage.${id}`, checkbox(bank.slg.stage_scope[id])),
  ]));

  const promptMode = control(section, "prompt.mode", "moss.prompt.mode",
    modeSelect(bank.prompt.mode, "moss.prompt", ["original", "enhance", "layout"]));
  const enhance = document.createElement("div");
  note(enhance, "moss.prompt.cost");
  const promptDetails = details(enhance, "moss.prompt.advanced");
  const promptInputs = {};
  for (const [name, step] of [
    ["max_length", "1"], ["temperature", "0.01"], ["top_k", "1"],
    ["top_p", "0.01"], ["min_p", "0.01"], ["repetition_penalty", "0.01"],
  ]) {
    promptInputs[name] = control(promptDetails, `prompt.${name}`, `moss.prompt.${name}`,
      numberInput(bank.prompt[name], step));
  }
  for (const [name, min, max] of [
    ["max_length", 1, 32768], ["temperature", 0.01, 2], ["top_k", 0, 1000],
    ["top_p", 0, 1], ["min_p", 0, 1], ["repetition_penalty", 0, 5],
  ]) {
    promptInputs[name].min = String(min);
    promptInputs[name].max = String(max);
  }
  const seed = control(promptDetails, "prompt.seed", "moss.prompt.seed", textInput(bank.prompt.seed));
  seed.inputMode = "numeric";
  const layout = document.createElement("div");
  note(layout, "moss.prompt.layoutHint");
  const layoutInput = document.createElement("textarea");
  layoutInput.value = bank.prompt.layout_json;
  layoutInput.rows = 7;
  layoutInput.spellcheck = false;
  layoutInput.placeholder = '{"summary":{"caption":"A poster"},"items":[{"label":"text","caption":"Title at the top","text":"HELLO","bbox":[-400,-300,-250,300]}],"bbox_coord_space":"abs_centralized","bbox_format":"yxyx"}';
  control(layout, "prompt.layout_json", "moss.prompt.layoutJson", layoutInput, "moss.prompt.layoutHint");
  section.append(enhance, layout);

  const refresh = () => {
    slgHint.hidden = slgMode.value === "off";
    slgDetails.hidden = slgMode.value === "off";
    enhance.hidden = promptMode.value !== "enhance";
    layout.hidden = promptMode.value !== "layout";
  };
  slgMode.addEventListener("change", refresh);
  promptMode.addEventListener("change", refresh);
  refresh();
  const numberValue = (input, previous) => input.value === "" || input.value === String(previous)
    ? previous : Number(input.value);

  return {
    element: section,
    apply(next) {
      const selected = mergeDefaults(bank, next.model_settings?.moss_image || {});
      Object.assign(selected.slg, {
        mode: slgMode.value, layers: layers.value, scale: numberValue(scale, bank.slg.scale),
        start_percent: numberValue(start, bank.slg.start_percent), end_percent: numberValue(end, bank.slg.end_percent),
        stage_scope: { ...selected.slg.stage_scope, ...Object.fromEntries(
          Object.entries(stages).map(([id, input]) => [id, input.checked]),
        ) },
      });
      Object.assign(selected.prompt, {
        mode: promptMode.value, layout_json: layoutInput.value,
        ...Object.fromEntries(Object.entries(promptInputs).map(([name, input]) => [
          name, numberValue(input, bank.prompt[name]),
        ])),
        seed: seed.value === String(bank.prompt.seed) ? bank.prompt.seed : normalizeSeed(seed.value, bank.prompt.seed),
      });
      next.model_settings = { ...next.model_settings, moss_image: selected };
    },
  };
}
