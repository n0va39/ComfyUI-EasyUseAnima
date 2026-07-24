// @ts-check

import {
  LONG_TEXT_FIELD_GROUPS,
  NAIA_PREPROCESSING_OPTIONS,
  NAIA_RESOLUTION_BUCKET_OPTIONS,
  ROOT_CATEGORY,
} from "./definition_data.js";
import { easyuseAnimaInitialAutocompleteSource } from "../easyuse_anima_i18n.js";

/**
 * @typedef {object} EasyUseAnimaSettingsDependencies
 * @property {(key: string) => string} text
 * @property {(item: any) => string} localeLabel
 * @property {(id: string, value: any, type?: string) => void} updateInternalSetting
 * @property {(groupKey: string) => HTMLElement} createLongTextEditorButton
 * @property {(...args: any[]) => HTMLElement} createPromptStudioColorEditorButton
 * @property {(...args: any[]) => HTMLElement} createWildcardExtraPathsEditor
 * @property {(...args: any[]) => HTMLElement} createNaiaResolutionModeEditor
 * @property {(...args: any[]) => HTMLElement} createNaiaResolutionScaleEditor
 */

/**
 * @typedef {object} SettingDefinitionInput
 * @property {string} id
 * @property {string} section
 * @property {string} [group]
 * @property {string} name
 * @property {string} [tooltip]
 * @property {any} type
 * @property {any} defaultValue
 * @property {any[]} [options]
 * @property {Record<string, any>} [attrs]
 * @property {(value: any) => void} [onChange]
 */

/**
 * @typedef {object} CustomSettingDefinitionInput
 * @property {string} id
 * @property {string} section
 * @property {string} name
 * @property {string} [tooltip]
 * @property {(...args: any[]) => HTMLElement} render
 */

/**
 * Build the ComfyUI settings descriptors without owning host registration or
 * browser lifecycle side effects.
 *
 * @param {EasyUseAnimaSettingsDependencies} dependencies
 * @returns {Array<Record<string, any>>}
 */
export function createEasyUseAnimaSettings(dependencies) {
  const {
    text: t,
    localeLabel: label,
    updateInternalSetting,
    createLongTextEditorButton,
    createPromptStudioColorEditorButton,
    createWildcardExtraPathsEditor,
    createNaiaResolutionModeEditor,
    createNaiaResolutionScaleEditor,
  } = dependencies;

  /**
   * @param {SettingDefinitionInput} definition
   */
  function setting({ id, section, name, tooltip, type, defaultValue, options, attrs, onChange }) {
    return {
      id,
      name,
      category: [ROOT_CATEGORY, section, name],
      type,
      defaultValue,
      ...(tooltip ? { tooltip } : {}),
      ...(options ? { options } : {}),
      ...(attrs ? { attrs } : {}),
      onChange:
        onChange ||
        ((value) => {
          updateInternalSetting(id, value, type);
      }),
    };
  }

  /**
   * @param {CustomSettingDefinitionInput} definition
   */
  function customSetting({ id, section, name, tooltip, render }) {
    return {
      id,
      name,
      category: [ROOT_CATEGORY, section, name],
      type: render,
      defaultValue: "",
      ...(tooltip ? { tooltip } : {}),
    };
  }

  return [
    customSetting({
      id: LONG_TEXT_FIELD_GROUPS.promptStudio.settingId,
      section: LONG_TEXT_FIELD_GROUPS.promptStudio.section,
      name: t(LONG_TEXT_FIELD_GROUPS.promptStudio.nameKey),
      tooltip: t(LONG_TEXT_FIELD_GROUPS.promptStudio.tipKey),
      render: () => createLongTextEditorButton("promptStudio"),
    }),
    setting({
      id: "EasyUseAnima.Prompt.AutocompleteMode",
      section: "Autocomplete",
      group: t("autocomplete"),
      name: t("autocompleteMode"),
      tooltip: t("autocompleteModeTip"),
      type: "combo",
      defaultValue: "compatible_global",
      options: ["off", "easyuse_nodes", "compatible_global"],
    }),
    setting({
      id: "EasyUseAnima.Prompt.AutocompleteSource",
      section: "Autocomplete",
      group: t("autocomplete"),
      name: t("autocompleteCsv"),
      tooltip: t("autocompleteCsvTip"),
      type: "combo",
      defaultValue: easyuseAnimaInitialAutocompleteSource,
      options: [
        "dbr_danbooru_2025_09_01",
        "dbr_e621_2025_09_01",
        "dbr_danbooru_e621_merged_2025_09_01",
        "localsmile_kr_wiki",
      ],
    }),
    setting({
      id: "EasyUseAnima.Prompt.AutocompleteLimit",
      section: "Autocomplete",
      group: t("autocomplete"),
      name: t("autocompleteLimit"),
      tooltip: t("autocompleteLimitTip"),
      type: "number",
      defaultValue: 20,
      attrs: { min: 1, max: 100, step: 1 },
    }),
    setting({
      id: "EasyUseAnima.Prompt.AutocompleteCommitKey",
      section: "Autocomplete",
      group: t("autocomplete"),
      name: t("autocompleteCommitKey"),
      tooltip: t("autocompleteCommitKeyTip"),
      type: "combo",
      defaultValue: "enter",
      options: ["enter", "tab"],
    }),
    setting({
      id: "EasyUseAnima.Prompt.AutocompleteAppendSeparator",
      section: "Autocomplete",
      group: t("autocomplete"),
      name: t("autocompleteAppendSeparator"),
      tooltip: t("autocompleteAppendSeparatorTip"),
      type: "boolean",
      defaultValue: false,
    }),
    setting({
      id: "EasyUseAnima.Prompt.AutocompleteNoCommaAfterPeriod",
      section: "Autocomplete",
      group: t("autocomplete"),
      name: t("autocompleteNoCommaAfterPeriod"),
      tooltip: t("autocompleteNoCommaAfterPeriodTip"),
      type: "boolean",
      defaultValue: true,
    }),
    setting({
      id: "EasyUseAnima.Prompt.AutocompleteDetectNaturalSentences",
      section: "Autocomplete",
      group: t("autocomplete"),
      name: t("autocompleteDetectNaturalSentences"),
      tooltip: t("autocompleteDetectNaturalSentencesTip"),
      type: "boolean",
      defaultValue: true,
    }),
    setting({
      id: "EasyUseAnima.Prompt.AutocompletePreviewCompletion",
      section: "Autocomplete",
      group: t("autocomplete"),
      name: t("autocompletePreviewCompletion"),
      tooltip: t("autocompletePreviewCompletionTip"),
      type: "boolean",
      defaultValue: false,
    }),
    setting({
      id: "EasyUseAnima.Prompt.AutocompletePreviewClosingBrackets",
      section: "Autocomplete",
      group: t("autocomplete"),
      name: t("autocompletePreviewClosingBrackets"),
      tooltip: t("autocompletePreviewClosingBracketsTip"),
      type: "boolean",
      defaultValue: false,
    }),
    setting({
      id: "EasyUseAnima.Prompt.TranslationProvider",
      section: "PromptStudio",
      group: t("promptTranslation"),
      name: t("promptTranslationProvider"),
      tooltip: t("promptTranslationProviderTip"),
      type: "combo",
      defaultValue: "off",
      options: ["off", "google"],
    }),
    setting({
      id: "EasyUseAnima.Prompt.TranslationSource",
      section: "PromptStudio",
      group: t("promptTranslation"),
      name: t("promptTranslationSource"),
      tooltip: t("promptTranslationSourceTip"),
      type: "text",
      defaultValue: "auto",
    }),
    setting({
      id: "EasyUseAnima.Prompt.TranslationTarget",
      section: "PromptStudio",
      group: t("promptTranslation"),
      name: t("promptTranslationTarget"),
      tooltip: t("promptTranslationTargetTip"),
      type: "text",
      defaultValue: "en",
    }),
    setting({
      id: "EasyUseAnima.Prompt.TypoIndicator",
      section: "PromptStudio",
      group: t("highlightBehavior"),
      name: t("showTypoIndicators"),
      type: "boolean",
      defaultValue: true,
    }),
    setting({
      id: "EasyUseAnima.Prompt.WeightSyntaxUnderline",
      section: "PromptStudio",
      group: t("highlightBehavior"),
      name: t("underlineWeightSyntax"),
      tooltip: t("underlineWeightSyntaxTip"),
      type: "boolean",
      defaultValue: false,
    }),
    setting({
      id: "EasyUseAnima.Prompt.CommentItalic",
      section: "PromptStudio",
      group: t("highlightBehavior"),
      name: t("italicizeComments"),
      type: "boolean",
      defaultValue: true,
    }),
    setting({
      id: "EasyUseAnima.Prompt.TrainedTagTooltip",
      section: "PromptStudio",
      group: t("highlightBehavior"),
      name: t("trainedTagTooltip"),
      tooltip: t("trainedTagTooltipTip"),
      type: "boolean",
      defaultValue: true,
    }),
    setting({
      id: "EasyUseAnima.Prompt.FontOverride",
      section: "PromptStudio",
      group: t("highlightBehavior"),
      name: t("fontOverride"),
      tooltip: t("fontOverrideTip"),
      type: "boolean",
      defaultValue: false,
    }),
    setting({
      id: "EasyUseAnima.Prompt.FontFamily",
      section: "PromptStudio",
      group: t("highlightBehavior"),
      name: t("promptFontFamily"),
      tooltip: t("promptFontFamilyTip"),
      type: "text",
      defaultValue: "",
    }),
    setting({
      id: "EasyUseAnima.Prompt.FontSize",
      section: "PromptStudio",
      group: t("highlightBehavior"),
      name: t("promptFontSize"),
      tooltip: t("promptFontSizeTip"),
      type: "number",
      defaultValue: 12,
      attrs: { min: 8, max: 24, step: 1 },
    }),
    setting({
      id: "EasyUseAnima.Prompt.NaiaGeneralAutoToggle",
      section: "PromptStudio",
      group: t("highlightBehavior"),
      name: t("naiaGeneralAutoToggle"),
      tooltip: t("naiaGeneralAutoToggleTip"),
      type: "boolean",
      defaultValue: false,
    }),
    customSetting({
      id: "EasyUseAnima.Prompt.HighlightColors",
      section: "PromptStudio",
      name: t("highlightColorEditor"),
      tooltip: t("highlightColorEditorTip"),
      render: createPromptStudioColorEditorButton,
    }),
    customSetting({
      id: "EasyUseAnima.Wildcard.ExtraPaths",
      section: "Wildcard",
      name: t("wildcardExtraPaths"),
      tooltip: t("wildcardExtraPathsTip"),
      render: createWildcardExtraPathsEditor,
    }),
    setting({
      id: "EasyUseAnima.LoraPreset.NameDisplay",
      section: "LoraPreset",
      group: t("loraDisplay"),
      name: t("loraDisplay"),
      tooltip: t("loraDisplayTip"),
      type: "combo",
      defaultValue: "name",
      options: ["name", "path"],
    }),
    setting({
      id: "EasyUseAnima.LoraPreset.MenuMode",
      section: "LoraPreset",
      group: t("loraDisplay"),
      name: t("loraMenuMode"),
      tooltip: t("loraMenuModeTip"),
      type: "combo",
      defaultValue: "tree",
      options: ["tree", "list"],
    }),
    setting({
      id: "EasyUseAnima.LoraPreset.StrengthButtonStep",
      section: "LoraPreset",
      group: t("loraStrength"),
      name: t("loraStrengthButtonStep"),
      tooltip: t("loraStrengthButtonStepTip"),
      type: "number",
      defaultValue: 0.05,
      attrs: { min: 0.001, max: 0.5, step: 0.001 },
    }),
    setting({
      id: "EasyUseAnima.LoraPreset.StrengthDragStep",
      section: "LoraPreset",
      group: t("loraStrength"),
      name: t("loraStrengthDragStep"),
      tooltip: t("loraStrengthDragStepTip"),
      type: "number",
      defaultValue: 0.05,
      attrs: { min: 0.001, max: 0.2, step: 0.001 },
    }),
    setting({
      id: "EasyUseAnima.LoraPreset.StrengthDragPixels",
      section: "LoraPreset",
      group: t("loraStrength"),
      name: t("loraStrengthDragPixels"),
      tooltip: t("loraStrengthDragPixelsTip"),
      type: "number",
      defaultValue: 8,
      attrs: { min: 1, max: 100, step: 1 },
    }),
    setting({
      id: "EasyUseAnima.NAIA.Host",
      section: "NAIA",
      group: t("naiaEndpoint"),
      name: "Host",
      type: "text",
      defaultValue: "127.0.0.1",
    }),
    setting({
      id: "EasyUseAnima.NAIA.Port",
      section: "NAIA",
      group: t("naiaEndpoint"),
      name: "Port",
      type: "text",
      defaultValue: "7243",
    }),
    setting({
      id: "EasyUseAnima.NAIA.AllowRemoteAPI",
      section: "NAIA",
      group: t("naiaEndpoint"),
      name: t("naiaAllowRemoteApi"),
      tooltip: t("naiaAllowRemoteApiTip"),
      type: "boolean",
      defaultValue: false,
    }),
    setting({
      id: "EasyUseAnima.NAIA.UseDesktopPromptEngineering",
      section: "NAIA",
      group: t("naiaPromptEngineering"),
      name: t("useDesktopNaia"),
      tooltip: t("naiaDesktopPromptEngineeringTip"),
      type: "boolean",
      defaultValue: true,
    }),
    customSetting({
      id: "EasyUseAnima.NAIA.ResolutionMode",
      section: "NAIA",
      name: t("naiaResolutionMode"),
      tooltip: t("naiaResolutionModeTip"),
      render: createNaiaResolutionModeEditor,
    }),
    setting({
      id: "EasyUseAnima.NAIA.ResolutionBucket",
      section: "NAIA",
      group: t("naiaResolution"),
      name: t("naiaResolutionBucket"),
      tooltip: t("naiaResolutionBucketTip"),
      type: "combo",
      defaultValue: "1024",
      options: NAIA_RESOLUTION_BUCKET_OPTIONS,
    }),
    customSetting({
      id: "EasyUseAnima.NAIA.ResolutionScale",
      section: "NAIA",
      name: t("naiaResolutionScale"),
      tooltip: t("naiaResolutionScaleTip"),
      render: createNaiaResolutionScaleEditor,
    }),
    setting({
      id: "EasyUseAnima.NAIA.ResolutionMaxLongEdge",
      section: "NAIA",
      group: t("naiaResolution"),
      name: t("naiaResolutionMaxLongEdge"),
      tooltip: t("naiaResolutionMaxLongEdgeTip"),
      type: "number",
      defaultValue: 0,
      attrs: { min: 0, max: 16384, step: 32 },
    }),
    customSetting({
      id: LONG_TEXT_FIELD_GROUPS.naia.settingId,
      section: LONG_TEXT_FIELD_GROUPS.naia.section,
      name: t(LONG_TEXT_FIELD_GROUPS.naia.nameKey),
      tooltip: t(LONG_TEXT_FIELD_GROUPS.naia.tipKey),
      render: () => createLongTextEditorButton("naia"),
    }),
    ...NAIA_PREPROCESSING_OPTIONS.map(([key, item]) =>
      setting({
        id: `EasyUseAnima.NAIA.${key}`,
        section: "NAIA",
        group: t("preprocessingOptions"),
        name: label(item),
        type: "combo",
        defaultValue: "skip",
        options: ["skip", "on", "off"],
      }),
    ),
  ];
}
