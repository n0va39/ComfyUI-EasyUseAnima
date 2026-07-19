// @ts-check

// @ts-expect-error ComfyUI provides this host module at runtime.
import { app } from "../../../scripts/app.js";
import { easyuseAnimaFetchJson, easyuseAnimaGetSettings, easyuseAnimaPostJson } from "./easyuse_anima_api.js";
import {
  easyuseAnimaLocaleText,
  easyuseAnimaText,
} from "./easyuse_anima_i18n.js";
import {
  INTERNAL_KEYS,
  LONG_TEXT_FIELD_GROUPS,
  normalizeValue,
} from "./settings/definition_data.js";
import { createEasyUseAnimaSettings } from "./settings/definitions.js";
import { createPromptStudioColorEditorButtonFactory } from "./settings/color_editor.js";
import { createLongTextEditorButtonFactory } from "./settings/long_text_editor.js";
import { createResolutionEditors } from "./settings/resolution_editors.js";
import { createSettingsRuntime } from "./settings/runtime.js";
import { createWildcardExtraPathsEditorFactory } from "./settings/wildcard_path_editor.js";

/**
 * @typedef {Window & typeof globalThis & {
 *   __easyuseAnimaSettings?: Record<string, unknown>
 * }} EasyUseAnimaSettingsWindow
 */

/** @type {EasyUseAnimaSettingsWindow} */
const settingsWindow = window;


const TEXT = {
  en: {
    autocomplete: "Autocomplete",
    autocompleteCsv: "Autocomplete CSV",
    autocompleteLimit: "Autocomplete suggestions",
    autocompleteMode: "Autocomplete mode",
    autocompleteModeTip: "Controls where EasyUse Anima autocomplete is active.",
    autocompleteCommitKey: "Autocomplete commit key",
    autocompleteCommitKeyTip: "Choose whether Enter and Tab commit suggestions, or only Tab commits. Shift+Enter always inserts a line break.",
    autocompleteAppendSeparator: "Append comma after autocomplete",
    autocompleteAppendSeparatorTip: "After committing a suggestion, add ', ' and place the caret after it for the next tag.",
    autocompleteNoCommaAfterPeriod: "Do not comma-correct after period",
    autocompleteNoCommaAfterPeriodTip: "When autocomplete follows a sentence period, keep the period boundary instead of inserting ', '.",
    autocompleteDetectNaturalSentences: "Detect natural text by periods",
    autocompleteDetectNaturalSentencesTip: "Treat text after a sentence period as the autocomplete target so the preceding natural sentence is preserved.",
    autocompletePreviewCompletion: "Inline autocomplete preview",
    autocompletePreviewCompletionTip:
      "Show only the remaining text that the selected suggestion would insert at the caret, like an IDE or PowerShell ghost completion. It does not commit the suggestion.",
    autocompletePreviewClosingBrackets: "Preview closing brackets",
    autocompletePreviewClosingBracketsTip:
      "When typing an opening prompt bracket, insert the closing bracket at the caret like an editor pair. Autocomplete previews may show closing brackets, but suggestions do not force-close multi-item groups.",
    autocompleteCsvTip: "Select which bundled CSV powers autocomplete and tag highlighting. The merged Danbooru+e621 source may have category merge issues.",
    autocompleteLimitTip: "",
    highlightBehavior: "Highlight behavior",
    highlightColor: "Highlight color",
    highlightColorEditor: "Manage highlight colors",
    highlightColorEditorTip: "Open a tabbed editor for Prompt Studio highlight colors.",
    highlightColorTabTags: "Tags",
    highlightColorTabSyntax: "Syntax",
    reset: "Reset",
    close: "Close",
    loraDisplay: "LoRA display",
    loraDisplayTip: "Choose whether LoRA preset rows show only filenames or full relative paths.",
    loraMenuMode: "LoRA menu mode",
    loraMenuModeTip: "Tree groups LoRAs by folder. List keeps a flat menu and can be used as a fallback if another extension corrupts tree labels.",
    loraStrength: "LoRA strength",
    loraStrengthButtonStep: "Button step",
    loraStrengthButtonStepTip:
      "Amount changed by one click on the LoRA preset strength +/- buttons. 0.05 matches the previous behavior.",
    loraStrengthDragStep: "Drag step",
    loraStrengthDragStepTip:
      "Amount changed each time the LoRA preset strength drag passes the drag distance below.",
    loraStrengthDragPixels: "Drag distance",
    loraStrengthDragPixelsTip:
      "Horizontal pixels required for one drag step. Higher values make strength dragging less sensitive.",
    metadataFilter: "Metadata Prompt Filter",
    metadataFilterTip: "Remove these tags only from Anima Prompt Builder metadata_prompt.",
    promptStudio: "PromptStudio",
    promptTranslation: "Prompt translation",
    promptTranslationProvider: "Translation method",
    promptTranslationProviderTip:
      "Default is OFF. When Google Translate is selected, the text inside each %{...} marker is sent to Google's external translation service.",
    promptTranslationProviderGoogle: "Google Translate",
    promptTranslationProviderOff: "No translation, unwrap only",
    promptTranslationSource: "Source language",
    promptTranslationSourceTip: "Language code sent to the translator. Use auto for automatic detection.",
    promptTranslationTarget: "Target language",
    promptTranslationTargetTip: "Language code used for translated prompt text. English is en.",
    editPromptStudioLongText: "Edit PromptStudio long text",
    editPromptStudioLongTextTip:
      "Open a multiline editor for Metadata Prompt Filter. Values are stored in EasyUse Anima's user data folder.",
    editNaiaLongText: "Edit NAIA long text",
    editNaiaLongTextTip:
      "Open a multiline editor for NAIA Pre prompt, Post prompt, and Auto hide. Values are stored in EasyUse Anima's user data folder.",
    openEditor: "Open editor",
    save: "Save",
    cancel: "Cancel",
    saved: "Saved",
    saveFailed: "Save failed",
    naiaGeneralAutoToggle: "Auto toggle General fields above NAIA",
    naiaGeneralAutoToggleTip:
      "In Anima Prompt Studio Advanced, when the positive NAIA Prompt field is ON, this disables only positive General fields placed above that NAIA field. When the NAIA field is OFF, those General fields are enabled again. Fields below NAIA and negative fields are not changed.",
    wildcard: "Wildcard",
    wildcardExtraPaths: "Additional wildcard paths",
    wildcardExtraPathsTip:
      "Optional paths to existing wildcard folders. Add one folder per item. Relative paths are resolved from the ComfyUI root. EasyUse Anima's user wildcard folder is always searched last.",
    wildcardExtraPathPlaceholder: "Wildcard folder path",
    addWildcardPath: "Add path",
    removeWildcardPath: "Remove",
    naiaEndpoint: "Connection",
    naiaAllowRemoteApi: "Allow remote API",
    naiaAllowRemoteApiTip:
      "OFF keeps NAIA API calls localhost-only. Turn ON only for a trusted remote NAIA endpoint.",
    naiaPromptEngineering: "Prompt Engineering",
    naiaDesktopPromptEngineeringTip:
      "ON: ComfyUI does not send Prompt Engineering override values and NAIA 2.0 uses its own desktop settings. OFF: ComfyUI sends the values below as overrides for this request.",
    naiaResolution: "Resolution",
    naiaResolutionMode: "Resolution mode",
    naiaResolutionModeTip:
      "Controls how Anima Prompt Studio Advanced resolves NAIA width and height when the NAIA resolution bucket is selected.",
    naiaResolutionModeOriginalScale: "Original scale",
    naiaResolutionModeBucketFit: "Bucket fit",
    naiaResolutionBucket: "Fit bucket",
    naiaResolutionBucketTip:
      "In Bucket fit mode, choose the saved resolution bucket. The nearest aspect ratio in that bucket is used.",
    naiaResolutionScale: "Resolution scale",
    naiaResolutionScaleTip:
      "Used in Original scale mode. Multiplies the NAIA width and height when Anima Prompt Studio Advanced uses the NAIA resolution bucket. Decimal values such as 1.5 are supported. The final size is snapped to multiples of 32.",
    naiaResolutionMaxLongEdge: "Max long edge",
    naiaResolutionMaxLongEdgeTip:
      "Used in Original scale mode. Caps the longer side after applying the NAIA resolution scale. 0 disables the cap. The final size stays on multiples of 32.",
    preprocessingOptions: "Preprocessing options",
    prePrompt: "Pre prompt",
    postPrompt: "Post prompt",
    autoHide: "Auto hide",
    promptMetadata: "Prompt metadata",
    fontOverride: "Manual Prompt Studio font",
    fontOverrideTip:
      "Leave this OFF by default. Turn it ON only when the input text and highlight overlay render with different fonts.",
    promptFontFamily: "Prompt font family",
    promptFontFamilyTip: "Used only when Manual Prompt Studio font is ON. Leave empty to use the system UI font.",
    promptFontSize: "Prompt font size",
    promptFontSizeTip: "Used only when Manual Prompt Studio font is ON. Controls Prompt Studio text area font size in pixels.",
    trainedTagTooltip: "Tag hover tooltip",
    trainedTagTooltipTip:
      "Show autocomplete metadata tooltips when hovering learned Prompt Studio tags.",
    showTypoIndicators: "Show typo indicators",
    underlineWeightSyntax: "Underline weight syntax",
    underlineWeightSyntaxTip:
      "Underline weighted prompt syntax such as (tag:1.2) and Artist Mix groups like [[artist_a, artist_b:0.7]].",
    italicizeComments: "Italicize comment lines",
    useDesktopNaia: "Use NAIA desktop Prompt Engineering settings",
  },
  ko: {
    autocomplete: "자동완성",
    autocompleteCsv: "자동완성 CSV",
    autocompleteLimit: "자동완성 추천 수",
    autocompleteMode: "자동완성 적용 범위",
    autocompleteModeTip: "EasyUse Anima 자동완성이 동작할 위치를 정합니다.",
    autocompleteCommitKey: "자동완성 적용 키",
    autocompleteCommitKeyTip: "Enter와 Tab 모두 자동완성을 적용할지, Tab만 적용할지 선택합니다. Shift+Enter는 항상 줄바꿈입니다.",
    autocompleteAppendSeparator: "자동완성 뒤 쉼표 추가",
    autocompleteAppendSeparatorTip: "자동완성 적용 후 ', '를 붙이고 다음 태그를 바로 입력할 수 있게 커서를 이동합니다.",
    autocompleteNoCommaAfterPeriod: "온점 뒤 쉼표 보정 안 함",
    autocompleteNoCommaAfterPeriodTip: "자동완성이 온점 뒤에서 동작할 때 ', '를 강제로 넣지 않고 문장 경계를 유지합니다.",
    autocompleteDetectNaturalSentences: "온점 단위 자연어 자동 감지",
    autocompleteDetectNaturalSentencesTip: "온점 뒤 텍스트만 자동완성 대상으로 보고 앞 자연어 문장을 보존합니다.",
    autocompletePreviewCompletion: "자동완성 인라인 미리보기",
    autocompletePreviewCompletionTip:
      "선택된 후보를 적용하면 커서 위치에 추가될 나머지 글자만 IDE나 PowerShell의 ghost completion처럼 표시합니다. 후보를 자동 적용하지는 않습니다.",
    autocompletePreviewClosingBrackets: "닫는 괄호 미리입력",
    autocompletePreviewClosingBracketsTip:
      "여는 프롬프트 괄호를 입력하면 IDE처럼 닫는 괄호를 커서 오른쪽에 넣습니다. 자동완성 미리보기에는 닫는 괄호가 보일 수 있지만, 여러 항목을 넣는 그룹을 후보 적용만으로 강제 종료하지는 않습니다.",
    autocompleteCsvTip: "자동완성과 태그 하이라이트에 사용할 번들 CSV를 선택합니다. Danbooru+e621 병합 소스는 카테고리 병합 오류 가능성이 있습니다.",
    autocompleteLimitTip: "",
    highlightBehavior: "하이라이트 동작",
    highlightColor: "하이라이트 색상",
    highlightColorEditor: "하이라이트 색상 관리",
    highlightColorEditorTip: "Prompt Studio 하이라이트 색상을 탭 편집기로 엽니다.",
    highlightColorTabTags: "태그",
    highlightColorTabSyntax: "문법",
    reset: "초기화",
    close: "닫기",
    loraDisplay: "LoRA 표시",
    loraDisplayTip: "LoRA 프리셋 행에 파일명만 표시할지 상대 경로를 표시할지 선택합니다.",
    loraMenuMode: "LoRA 메뉴 방식",
    loraMenuModeTip: "tree는 폴더별 트리로 묶습니다. list는 평면 메뉴로 유지하며 다른 확장이 트리 이름을 오염시킬 때 우회용으로 사용할 수 있습니다.",
    loraStrength: "LoRA 강도",
    loraStrengthButtonStep: "버튼 증감값",
    loraStrengthButtonStepTip:
      "LoRA 프리셋 강도 +/- 버튼을 한 번 누를 때 바뀌는 값입니다. 0.05는 이전 동작과 같습니다.",
    loraStrengthDragStep: "드래그 증감값",
    loraStrengthDragStepTip:
      "LoRA 프리셋 강도 드래그가 아래 이동 거리만큼 누적될 때마다 바뀌는 값입니다.",
    loraStrengthDragPixels: "드래그 이동 거리",
    loraStrengthDragPixelsTip:
      "강도 드래그가 한 단계 변하는 데 필요한 가로 픽셀 수입니다. 높을수록 덜 민감합니다.",
    metadataFilter: "Metadata Prompt 필터",
    metadataFilterTip: "Anima Prompt Builder metadata_prompt에서만 지정 태그를 제거합니다.",
    promptStudio: "PromptStudio",
    promptTranslation: "프롬프트 번역",
    promptTranslationProvider: "번역 방식",
    promptTranslationProviderTip:
      "기본값은 OFF입니다. Google 번역을 선택하면 각 %{...} 마커 안의 텍스트가 Google 외부 번역 서비스로 전송됩니다.",
    promptTranslationProviderGoogle: "Google 번역",
    promptTranslationProviderOff: "번역 안 함, 구문만 제거",
    promptTranslationSource: "원본 언어",
    promptTranslationSourceTip: "번역기에 전달할 언어 코드입니다. 자동 감지는 auto를 사용합니다.",
    promptTranslationTarget: "대상 언어",
    promptTranslationTargetTip: "번역된 프롬프트에 사용할 언어 코드입니다. 영어는 en입니다.",
    editPromptStudioLongText: "PromptStudio 긴 텍스트 편집",
    editPromptStudioLongTextTip:
      "Metadata Prompt 필터를 여러 줄로 편집합니다. 값은 EasyUse Anima 사용자 데이터 폴더에 저장됩니다.",
    editNaiaLongText: "NAIA 긴 텍스트 편집",
    editNaiaLongTextTip:
      "NAIA Pre prompt, Post prompt, Auto hide를 여러 줄로 편집합니다. 값은 EasyUse Anima 사용자 데이터 폴더에 저장됩니다.",
    openEditor: "편집 열기",
    save: "저장",
    cancel: "취소",
    saved: "저장됨",
    saveFailed: "저장 실패",
    naiaGeneralAutoToggle: "NAIA 위쪽 General 자동 토글",
    naiaGeneralAutoToggleTip:
      "Anima Prompt Studio Advanced에서 긍정 프롬프트의 NAIA Prompt 필드가 켜지면, 그 NAIA 필드보다 위에 있는 긍정 General 필드만 자동으로 OFF합니다. NAIA 필드가 꺼지면 해당 General 필드를 다시 ON합니다. NAIA 아래 필드와 네거티브 필드는 건드리지 않습니다.",
    wildcard: "와일드카드",
    wildcardExtraPaths: "추가 와일드카드 경로",
    wildcardExtraPathsTip:
      "기존 와일드카드 폴더가 있으면 항목별로 하나씩 추가합니다. 상대 경로는 ComfyUI 루트 기준이며 EasyUse Anima 사용자 와일드카드 폴더는 항상 마지막에 검색합니다.",
    wildcardExtraPathPlaceholder: "와일드카드 폴더 경로",
    addWildcardPath: "경로 추가",
    removeWildcardPath: "삭제",
    naiaEndpoint: "연결",
    naiaAllowRemoteApi: "원격 API 허용",
    naiaAllowRemoteApiTip:
      "OFF이면 NAIA API 호출은 localhost로만 제한됩니다. 신뢰하는 원격 NAIA endpoint를 쓸 때만 켜세요.",
    naiaPromptEngineering: "Prompt Engineering",
    naiaDesktopPromptEngineeringTip:
      "ON: ComfyUI의 Prompt Engineering override 값을 보내지 않고 NAIA 2.0 프로그램의 자체 설정을 사용합니다. OFF: 아래 ComfyUI 설정값을 이번 요청의 override로 NAIA에 보냅니다.",
    naiaResolution: "해상도",
    naiaResolutionMode: "해상도 적용 방식",
    naiaResolutionModeTip:
      "Anima Prompt Studio Advanced에서 NAIA 해상도 버킷을 사용할 때 NAIA width/height를 적용하는 방식입니다.",
    naiaResolutionModeOriginalScale: "원본 배율",
    naiaResolutionModeBucketFit: "버켓 맞춤",
    naiaResolutionBucket: "맞춤 버켓",
    naiaResolutionBucketTip:
      "버켓 맞춤 모드에서 사용할 해상도 버켓입니다. 선택한 버켓 안에서 NAIA 화면비와 가장 가까운 해상도를 고릅니다.",
    naiaResolutionScale: "해상도 배율",
    naiaResolutionScaleTip:
      "원본 배율 모드에서 사용됩니다. Anima Prompt Studio Advanced에서 NAIA 해상도 버킷을 사용할 때 NAIA width/height에 곱할 배율입니다. 1.5 같은 소수값을 입력할 수 있습니다. 최종 크기는 32의 배수로 보정됩니다.",
    naiaResolutionMaxLongEdge: "긴변 최댓값",
    naiaResolutionMaxLongEdgeTip:
      "원본 배율 모드에서 사용됩니다. NAIA 해상도 배율을 적용한 뒤 긴 변의 최대 크기를 제한합니다. 0이면 제한하지 않습니다. 최종 크기는 32의 배수로 유지됩니다.",
    preprocessingOptions: "전처리 옵션",
    prePrompt: "Pre prompt",
    postPrompt: "Post prompt",
    autoHide: "Auto hide",
    promptMetadata: "프롬프트 메타데이터",
    fontOverride: "Prompt Studio 수동 폰트 보정",
    fontOverrideTip:
      "기본값은 OFF입니다. 입력 텍스트와 하이라이트 overlay의 폰트가 다르게 보일 때만 켜세요.",
    promptFontFamily: "프롬프트 폰트",
    promptFontFamilyTip: "수동 폰트 보정이 ON일 때만 사용됩니다. 비워두면 시스템 UI 폰트를 사용합니다.",
    promptFontSize: "프롬프트 글자 크기",
    promptFontSizeTip: "수동 폰트 보정이 ON일 때만 사용됩니다. Prompt Studio 입력창의 글자 크기(px)를 조정합니다.",
    trainedTagTooltip: "태그 hover 툴팁",
    trainedTagTooltipTip:
      "Prompt Studio의 학습 태그 위에 마우스를 올렸을 때 자동완성 메타데이터 툴팁을 표시합니다.",
    showTypoIndicators: "오타 표시",
    underlineWeightSyntax: "가중치 문법 밑줄 표시",
    underlineWeightSyntaxTip:
      "(tag:1.2) 같은 프롬프트 가중치와 [[artist_a, artist_b:0.7]] 같은 Artist Mix 그룹 문법에 밑줄을 표시합니다.",
    italicizeComments: "주석 라인 이탤릭체",
    useDesktopNaia: "NAIA 데스크톱 Prompt Engineering 설정 사용",
  },
  ja: {
    autocomplete: "自動補完",
    autocompleteCsv: "自動補完 CSV",
    autocompleteLimit: "自動補完候補数",
    autocompleteMode: "自動補完の適用範囲",
    autocompleteModeTip: "EasyUse Anima 自動補完が有効になる場所を指定します。",
    autocompleteCommitKey: "自動補完の確定キー",
    autocompleteCommitKeyTip: "Enter と Tab の両方で候補を確定するか、Tab のみで確定するかを選びます。Shift+Enter は常に改行です。",
    autocompleteAppendSeparator: "自動補完後にカンマを追加",
    autocompleteAppendSeparatorTip: "候補確定後に ', ' を追加し、次のタグを入力しやすい位置へキャレットを移動します。",
    autocompleteNoCommaAfterPeriod: "句点後はカンマ補正しない",
    autocompleteNoCommaAfterPeriodTip: "自動補完が句点の後で動作する場合、', ' を強制せず文境界を維持します。",
    autocompleteDetectNaturalSentences: "句点単位で自然文を自動検出",
    autocompleteDetectNaturalSentencesTip: "句点後のテキストだけを自動補完対象として扱い、前の自然文を保持します。",
    autocompletePreviewCompletion: "インライン自動補完プレビュー",
    autocompletePreviewCompletionTip:
      "選択中の候補を確定したときにキャレット位置へ追加される残りの文字だけを、IDE や PowerShell の ghost completion のように表示します。候補は自動確定しません。",
    autocompletePreviewClosingBrackets: "閉じ括弧を先に入力",
    autocompletePreviewClosingBracketsTip:
      "プロンプトの開き括弧を入力したとき、エディタのペア入力のように閉じ括弧をキャレット右側へ入れます。自動補完プレビューには閉じ括弧を表示できますが、候補確定だけでは複数項目グループを強制終了しません。",
    autocompleteCsvTip: "自動補完とタグハイライトに使用する同梱 CSV を選択します。Danbooru+e621 の統合ソースにはカテゴリ統合エラーの可能性があります。",
    autocompleteLimitTip: "",
    highlightBehavior: "ハイライト動作",
    highlightColor: "ハイライト色",
    highlightColorEditor: "ハイライト色を管理",
    highlightColorEditorTip: "Prompt Studio のハイライト色をタブ付きエディターで開きます。",
    highlightColorTabTags: "タグ",
    highlightColorTabSyntax: "構文",
    reset: "リセット",
    close: "閉じる",
    loraDisplay: "LoRA 表示",
    loraDisplayTip: "LoRA プリセット行にファイル名のみを表示するか、相対パスを表示するかを選びます。",
    loraMenuMode: "LoRA メニューモード",
    loraMenuModeTip: "tree は LoRA をフォルダ別ツリーにまとめます。list はフラットメニューを維持し、他の拡張がツリーラベルを壊す場合の代替として使えます。",
    loraStrength: "LoRA 強度",
    loraStrengthButtonStep: "ボタン増減値",
    loraStrengthButtonStepTip:
      "LoRA プリセット強度 +/- ボタンを 1 回押したときに変わる値です。0.05 は以前の動作と同じです。",
    loraStrengthDragStep: "ドラッグ増減値",
    loraStrengthDragStepTip:
      "LoRA プリセット強度ドラッグが下の移動距離に達するたびに変わる値です。",
    loraStrengthDragPixels: "ドラッグ移動距離",
    loraStrengthDragPixelsTip:
      "強度ドラッグが 1 段階変わるために必要な横方向ピクセル数です。大きいほど感度が低くなります。",
    metadataFilter: "Metadata Prompt フィルター",
    metadataFilterTip: "Anima Prompt Builder metadata_prompt からだけ指定タグを除去します。",
    promptStudio: "PromptStudio",
    promptTranslation: "プロンプト翻訳",
    promptTranslationProvider: "翻訳方式",
    promptTranslationProviderTip:
      "既定値は OFF です。Google 翻訳を選ぶと、各 %{...} マーカー内のテキストが Google の外部翻訳サービスへ送信されます。",
    promptTranslationProviderGoogle: "Google 翻訳",
    promptTranslationProviderOff: "翻訳しない、構文だけ外す",
    promptTranslationSource: "元言語",
    promptTranslationSourceTip: "翻訳器へ渡す言語コードです。自動検出は auto を使います。",
    promptTranslationTarget: "対象言語",
    promptTranslationTargetTip: "翻訳後のプロンプトに使う言語コードです。英語は en です。",
    editPromptStudioLongText: "PromptStudio 長文を編集",
    editPromptStudioLongTextTip:
      "Metadata Prompt フィルターを複数行で編集します。値は EasyUse Anima のユーザーデータフォルダに保存されます。",
    editNaiaLongText: "NAIA 長文を編集",
    editNaiaLongTextTip:
      "NAIA Pre prompt, Post prompt, Auto hide を複数行で編集します。値は EasyUse Anima のユーザーデータフォルダに保存されます。",
    openEditor: "エディターを開く",
    save: "保存",
    cancel: "キャンセル",
    saved: "保存済み",
    saveFailed: "保存失敗",
    naiaGeneralAutoToggle: "NAIA 上部 General 自動切替",
    naiaGeneralAutoToggleTip:
      "Anima Prompt Studio Advanced でポジティブの NAIA Prompt フィールドが ON のとき、その NAIA フィールドより上にあるポジティブ General フィールドだけを自動で OFF にします。NAIA フィールドが OFF になると該当 General フィールドを再度 ON にします。NAIA 下部フィールドとネガティブフィールドは変更しません。",
    wildcard: "ワイルドカード",
    wildcardExtraPaths: "追加ワイルドカードパス",
    wildcardExtraPathsTip:
      "既存のワイルドカードフォルダがある場合、項目ごとに 1 つずつ追加します。相対パスは ComfyUI ルート基準で解決され、EasyUse Anima のユーザーワイルドカードフォルダは常に最後に検索されます。",
    wildcardExtraPathPlaceholder: "ワイルドカードフォルダパス",
    addWildcardPath: "パス追加",
    removeWildcardPath: "削除",
    naiaEndpoint: "接続",
    naiaAllowRemoteApi: "リモート API を許可",
    naiaAllowRemoteApiTip:
      "OFF の場合、NAIA API 呼び出しは localhost のみに制限されます。信頼できるリモート NAIA endpoint を使う場合だけ ON にしてください。",
    naiaPromptEngineering: "Prompt Engineering",
    naiaDesktopPromptEngineeringTip:
      "ON: ComfyUI の Prompt Engineering override 値を送信せず、NAIA 2.0 アプリの設定を使用します。OFF: 下の ComfyUI 設定値をこのリクエストの override として NAIA に送信します。",
    naiaResolution: "解像度",
    naiaResolutionMode: "解像度適用方式",
    naiaResolutionModeTip:
      "Anima Prompt Studio Advanced で NAIA 解像度バケットを使うとき、NAIA の width/height をどの方式で解決するかを指定します。",
    naiaResolutionModeOriginalScale: "元サイズ倍率",
    naiaResolutionModeBucketFit: "バケット合わせ",
    naiaResolutionBucket: "合わせるバケット",
    naiaResolutionBucketTip:
      "バケット合わせモードで使う解像度バケットです。選択したバケット内で NAIA のアスペクト比に最も近い解像度を使います。",
    naiaResolutionScale: "解像度スケール",
    naiaResolutionScaleTip:
      "元サイズ倍率モードで使います。Anima Prompt Studio Advanced で NAIA 解像度バケットを使うとき、NAIA の width/height に掛ける倍率です。1.5 などの小数値を入力できます。最終サイズは 32 の倍数に補正されます。",
    naiaResolutionMaxLongEdge: "長辺の最大値",
    naiaResolutionMaxLongEdgeTip:
      "元サイズ倍率モードで使います。NAIA 解像度スケール適用後に長辺の最大サイズを制限します。0 で無効です。最終サイズは 32 の倍数に維持されます。",
    preprocessingOptions: "前処理オプション",
    prePrompt: "Pre prompt",
    postPrompt: "Post prompt",
    autoHide: "Auto hide",
    promptMetadata: "プロンプトメタデータ",
    fontOverride: "Prompt Studio 手動フォント補正",
    fontOverrideTip:
      "通常は OFF のままにします。入力テキストとハイライト overlay のフォント表示がずれる場合のみ ON にします。",
    promptFontFamily: "プロンプトフォント",
    promptFontFamilyTip: "Prompt Studio 手動フォント補正が ON のときだけ使用します。空欄ならシステム UI フォントを使います。",
    promptFontSize: "プロンプト文字サイズ",
    promptFontSizeTip: "Prompt Studio 手動フォント補正が ON のときだけ使用します。入力欄の文字サイズをピクセル単位で調整します。",
    trainedTagTooltip: "タグ hover ツールチップ",
    trainedTagTooltipTip:
      "Prompt Studio の学習済みタグにマウスを重ねたとき、自動補完メタデータのツールチップを表示します。",
    showTypoIndicators: "タイプミス表示",
    underlineWeightSyntax: "重み構文に下線を表示",
    underlineWeightSyntaxTip:
      "(tag:1.2) のようなプロンプト重み構文と [[artist_a, artist_b:0.7]] のような Artist Mix グループ構文に下線を表示します。",
    italicizeComments: "コメント行を斜体にする",
    useDesktopNaia: "NAIA デスクトップ Prompt Engineering 設定を使用",
  },
  zh: {
    autocomplete: "自动补全",
    autocompleteCsv: "自动补全 CSV",
    autocompleteLimit: "自动补全建议数",
    autocompleteMode: "自动补全适用范围",
    autocompleteModeTip: "控制 EasyUse Anima 自动补全在哪些位置启用。",
    autocompleteCommitKey: "自动补全确认键",
    autocompleteCommitKeyTip: "选择 Enter 和 Tab 都确认建议，或仅 Tab 确认。Shift+Enter 始终插入换行。",
    autocompleteAppendSeparator: "自动补全后追加逗号",
    autocompleteAppendSeparatorTip: "确认建议后追加 ', '，并将光标移动到便于输入下一个标签的位置。",
    autocompleteNoCommaAfterPeriod: "句号后不做逗号修正",
    autocompleteNoCommaAfterPeriodTip: "自动补全在句号后触发时，不强制插入 ', '，保留句子边界。",
    autocompleteDetectNaturalSentences: "按句号自动检测自然文本",
    autocompleteDetectNaturalSentencesTip: "只将句号后的文本视为自动补全目标，从而保留前面的自然语言句子。",
    autocompletePreviewCompletion: "内联自动补全预览",
    autocompletePreviewCompletionTip:
      "像 IDE 或 PowerShell 的 ghost completion 一样，只在光标位置显示当前候选将插入的剩余文本。不会自动确认候选。",
    autocompletePreviewClosingBrackets: "预填闭合括号",
    autocompletePreviewClosingBracketsTip:
      "输入提示词开括号时，像 IDE 一样在光标右侧插入闭合括号。自动补全预览可以显示闭合括号，但确认候选不会强制结束可包含多项的分组。",
    autocompleteCsvTip: "选择用于自动补全和标签高亮的内置 CSV。Danbooru+e621 合并来源可能存在分类合并错误。",
    autocompleteLimitTip: "",
    highlightBehavior: "高亮行为",
    highlightColor: "高亮颜色",
    highlightColorEditor: "管理高亮颜色",
    highlightColorEditorTip: "使用带标签页的编辑器打开 Prompt Studio 高亮颜色。",
    highlightColorTabTags: "标签",
    highlightColorTabSyntax: "语法",
    reset: "重置",
    close: "关闭",
    loraDisplay: "LoRA 显示",
    loraDisplayTip: "选择 LoRA 预设行只显示文件名，还是显示相对路径。",
    loraMenuMode: "LoRA 菜单模式",
    loraMenuModeTip: "tree 会按文件夹分组 LoRA。list 会保持平铺菜单，可在其他扩展破坏树标签时作为备用。",
    loraStrength: "LoRA 强度",
    loraStrengthButtonStep: "按钮步进",
    loraStrengthButtonStepTip:
      "每次点击 LoRA 预设强度 +/- 按钮时变化的数值。0.05 与之前行为一致。",
    loraStrengthDragStep: "拖动步进",
    loraStrengthDragStepTip:
      "LoRA 预设强度拖动累计到下方距离时，每一步变化的数值。",
    loraStrengthDragPixels: "拖动距离",
    loraStrengthDragPixelsTip:
      "强度拖动变化一步所需的水平像素数。数值越高越不敏感。",
    metadataFilter: "Metadata Prompt 过滤器",
    metadataFilterTip: "只从 Anima Prompt Builder metadata_prompt 中移除指定标签。",
    promptStudio: "PromptStudio",
    promptTranslation: "提示词翻译",
    promptTranslationProvider: "翻译方式",
    promptTranslationProviderTip:
      "默认值为 OFF。选择 Google 翻译后，每个 %{...} 标记内的文本都会发送到 Google 外部翻译服务。",
    promptTranslationProviderGoogle: "Google 翻译",
    promptTranslationProviderOff: "不翻译，仅去除语法",
    promptTranslationSource: "源语言",
    promptTranslationSourceTip: "传给翻译器的语言代码。自动检测使用 auto。",
    promptTranslationTarget: "目标语言",
    promptTranslationTargetTip: "翻译后提示词使用的语言代码。英语为 en。",
    editPromptStudioLongText: "编辑 PromptStudio 长文本",
    editPromptStudioLongTextTip:
      "以多行方式编辑 Metadata Prompt 过滤器。值会保存在 EasyUse Anima 用户数据文件夹中。",
    editNaiaLongText: "编辑 NAIA 长文本",
    editNaiaLongTextTip:
      "以多行方式编辑 NAIA Pre prompt、Post prompt 和 Auto hide。值会保存在 EasyUse Anima 用户数据文件夹中。",
    openEditor: "打开编辑器",
    save: "保存",
    cancel: "取消",
    saved: "已保存",
    saveFailed: "保存失败",
    naiaGeneralAutoToggle: "NAIA 上方 General 自动切换",
    naiaGeneralAutoToggleTip:
      "在 Anima Prompt Studio Advanced 中，当正向 NAIA Prompt 字段为 ON 时，只会自动关闭位于该 NAIA 字段上方的正向 General 字段。NAIA 字段为 OFF 时会重新启用这些 General 字段。不会更改 NAIA 下方字段和负向字段。",
    wildcard: "通配符",
    wildcardExtraPaths: "附加通配符路径",
    wildcardExtraPathsTip:
      "如有现有通配符文件夹，可按项目逐个添加。相对路径会从 ComfyUI 根目录解析。EasyUse Anima 用户通配符文件夹始终最后搜索。",
    wildcardExtraPathPlaceholder: "通配符文件夹路径",
    addWildcardPath: "添加路径",
    removeWildcardPath: "移除",
    naiaEndpoint: "连接",
    naiaAllowRemoteApi: "允许远程 API",
    naiaAllowRemoteApiTip:
      "OFF 时 NAIA API 调用仅限 localhost。只有使用可信远程 NAIA endpoint 时才开启。",
    naiaPromptEngineering: "Prompt Engineering",
    naiaDesktopPromptEngineeringTip:
      "ON：ComfyUI 不发送 Prompt Engineering override 值，NAIA 2.0 使用自己的桌面设置。OFF：将下方 ComfyUI 设置值作为本次请求的 override 发送给 NAIA。",
    naiaResolution: "分辨率",
    naiaResolutionMode: "分辨率应用方式",
    naiaResolutionModeTip:
      "Anima Prompt Studio Advanced 使用 NAIA 分辨率桶时，控制如何解析 NAIA width/height。",
    naiaResolutionModeOriginalScale: "原始倍率",
    naiaResolutionModeBucketFit: "桶匹配",
    naiaResolutionBucket: "匹配桶",
    naiaResolutionBucketTip:
      "在桶匹配模式下使用的分辨率桶。会在所选桶内使用与 NAIA 宽高比最接近的分辨率。",
    naiaResolutionScale: "分辨率倍率",
    naiaResolutionScaleTip:
      "原始倍率模式使用。Anima Prompt Studio Advanced 使用 NAIA 分辨率桶时，乘到 NAIA width/height 上的倍率。支持 1.5 等小数值。最终尺寸会对齐为 32 的倍数。",
    naiaResolutionMaxLongEdge: "长边最大值",
    naiaResolutionMaxLongEdgeTip:
      "原始倍率模式使用。应用 NAIA 分辨率倍率后限制长边最大尺寸。0 表示不限制。最终尺寸保持为 32 的倍数。",
    preprocessingOptions: "预处理选项",
    prePrompt: "Pre prompt",
    postPrompt: "Post prompt",
    autoHide: "Auto hide",
    promptMetadata: "提示词元数据",
    fontOverride: "Prompt Studio 手动字体修正",
    fontOverrideTip:
      "默认保持关闭。仅在输入文本和高亮 overlay 的字体显示不一致时开启。",
    promptFontFamily: "提示词字体",
    promptFontFamilyTip: "仅在 Prompt Studio 手动字体修正开启时使用。留空时使用系统 UI 字体。",
    promptFontSize: "提示词字体大小",
    promptFontSizeTip: "仅在 Prompt Studio 手动字体修正开启时使用。以像素为单位调整输入框字体大小。",
    trainedTagTooltip: "标签 hover 提示",
    trainedTagTooltipTip:
      "鼠标悬停在 Prompt Studio 已学习标签上时显示自动补全元数据提示。",
    showTypoIndicators: "显示错字标记",
    underlineWeightSyntax: "为权重语法显示下划线",
    underlineWeightSyntaxTip:
      "为 (tag:1.2) 等提示词权重语法和 [[artist_a, artist_b:0.7]] 等 Artist Mix 分组语法显示下划线。",
    italicizeComments: "注释行使用斜体",
    useDesktopNaia: "使用 NAIA 桌面 Prompt Engineering 设置",
  },
};

function t(key) {
  return easyuseAnimaText(TEXT, key);
}

function label(item) {
  return easyuseAnimaLocaleText(item);
}

function tip(item) {
  return easyuseAnimaLocaleText(item?.tip);
}

const {
  updateInternalSetting,
  readInternalSetting,
  loadLongTextSettings,
  saveLongTextSettings,
  loadInitialSettings,
} = createSettingsRuntime({
  getSettingsState: () => settingsWindow.__easyuseAnimaSettings,
  setSettingsState: (value) => {
    settingsWindow.__easyuseAnimaSettings = value;
  },
  notifySettingsUpdated: (detail) => {
    window.dispatchEvent(
      new CustomEvent("easyuse-anima-settings-updated", { detail }),
    );
  },
  internalKeys: INTERNAL_KEYS,
  normalizeValue,
  fetchInitialSettings: easyuseAnimaGetSettings,
  fetchJson: easyuseAnimaFetchJson,
  postJson: easyuseAnimaPostJson,
});

const createLongTextEditorButton = createLongTextEditorButtonFactory({
  document,
  fieldGroups: LONG_TEXT_FIELD_GROUPS,
  text: t,
  loadSettings: loadLongTextSettings,
  saveSettings: saveLongTextSettings,
  schedule: setTimeout,
});

const {
  createNaiaResolutionModeEditor,
  createNaiaResolutionScaleEditor,
} = createResolutionEditors({
  document,
  text: t,
  readInternalSetting,
  updateInternalSetting,
});

const createWildcardExtraPathsEditor = createWildcardExtraPathsEditorFactory({
  document,
  text: t,
  readInternalSetting,
  updateInternalSetting,
});

const createPromptStudioColorEditorButton =
  createPromptStudioColorEditorButtonFactory({
    document,
    text: t,
    label,
    tip,
    readInternalSetting,
    updateInternalSetting,
  });

const EASYUSE_ANIMA_SETTINGS = createEasyUseAnimaSettings({
  text: t,
  localeLabel: label,
  updateInternalSetting,
  createLongTextEditorButton,
  createPromptStudioColorEditorButton,
  createWildcardExtraPathsEditor,
  createNaiaResolutionModeEditor,
  createNaiaResolutionScaleEditor,
});

function addSettingsFallback() {
  const addSetting = app?.ui?.settings?.addSetting;
  if (typeof addSetting !== "function") {
    return;
  }
  const lookup = app.ui.settings.settingsLookup || {};
  for (const item of EASYUSE_ANIMA_SETTINGS) {
    if (!lookup[item.id]) {
      addSetting.call(app.ui.settings, item);
    }
  }
}

app.registerExtension({
  name: "easyuse-anima.settings",
  settings: EASYUSE_ANIMA_SETTINGS,
  async setup() {
    settingsWindow.__easyuseAnimaSettings = await loadInitialSettings();
    addSettingsFallback();
  },
});
