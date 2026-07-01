import { app } from "../../../scripts/app.js";
import {
  easyuseAnimaLocaleText,
  easyuseAnimaText,
} from "./easyuse_anima_i18n.js";

const ROOT_CATEGORY = "EASY USE ANIMA";

const PROMPT_STUDIO_COLORS = {
  quality: {
    en: "Quality",
    ko: "품질",
    ja: "品質",
    zh: "质量",
    color: "#facc15",
    tip: {
      en: "ANIMA quality/meta tags such as masterpiece, best quality, highres, and aesthetic. Not a Danbooru category number.",
      ko: "masterpiece, best quality, highres, aesthetic 같은 ANIMA 품질/메타 태그입니다. Danbooru 카테고리 번호는 없습니다.",
      ja: "masterpiece, best quality, highres, aesthetic などの ANIMA 品質/メタタグです。Danbooru カテゴリ番号ではありません。",
      zh: "masterpiece、best quality、highres、aesthetic 等 ANIMA 质量/元标签。不是 Danbooru 分类编号。",
    },
  },
  safety: {
    en: "Rating",
    ko: "등급",
    ja: "レーティング",
    zh: "分级",
    color: "#38bdf8",
    tip: {
      en: "Rating-style tags such as safe, sensitive, nsfw, explicit, or rating_*.",
      ko: "safe, sensitive, nsfw, explicit, rating_* 같은 등급 계열 태그입니다.",
      ja: "safe, sensitive, nsfw, explicit, rating_* などのレーティング系タグです。",
      zh: "safe、sensitive、nsfw、explicit、rating_* 等分级类标签。",
    },
  },
  year: {
    en: "Year",
    ko: "연도",
    ja: "年代",
    zh: "年份",
    color: "#2dd4bf",
    tip: {
      en: "Year bucket tags such as newest, recent, mid, early, oldest, or year n.",
      ko: "newest, recent, mid, early, oldest, year n 같은 연도 버킷 태그입니다.",
      ja: "newest, recent, mid, early, oldest, year n などの年代バケットタグです。",
      zh: "newest、recent、mid、early、oldest、year n 等年份桶标签。",
    },
  },
  count: {
    en: "Count",
    ko: "인원수",
    ja: "人数",
    zh: "人数",
    color: "#60a5fa",
    tip: {
      en: "Person-count tags such as 1girl, 2boys, or multiple girls. These are usually Danbooru category 0 but are highlighted separately.",
      ko: "1girl, 2boys, multiple girls 같은 인원수 태그입니다. 보통 Danbooru category 0이지만 별도 색상으로 표시합니다.",
      ja: "1girl, 2boys, multiple girls などの人数タグです。通常は Danbooru category 0 ですが、別色で表示します。",
      zh: "1girl、2boys、multiple girls 等人数标签。通常属于 Danbooru category 0，但会单独高亮。",
    },
  },
  character: {
    en: "Character",
    ko: "캐릭터",
    ja: "キャラクター",
    zh: "角色",
    color: "#f472b6",
    tip: {
      en: "Danbooru category 4: character tags.",
      ko: "Danbooru category 4: 캐릭터 태그입니다.",
      ja: "Danbooru category 4: キャラクタータグです。",
      zh: "Danbooru category 4：角色标签。",
    },
  },
  artist: {
    en: "Artist",
    ko: "작가",
    ja: "作者",
    zh: "作者",
    color: "#a78bfa",
    tip: {
      en: "Danbooru category 1: artist tags. EasyUse Anima also treats @artist prompt tokens as artist tags.",
      ko: "Danbooru category 1: 작가 태그입니다. EasyUse Anima는 @작가 형식의 프롬프트 토큰도 작가 태그로 취급합니다.",
      ja: "Danbooru category 1: 作者タグです。EasyUse Anima は @artist 形式のプロンプトトークンも作者タグとして扱います。",
      zh: "Danbooru category 1：作者标签。EasyUse Anima 也会将 @artist 形式的提示词 token 视为作者标签。",
    },
  },
  copyright: {
    en: "Copyright",
    ko: "작품",
    ja: "作品",
    zh: "作品",
    color: "#fb923c",
    tip: {
      en: "Danbooru category 3: copyright/work tags.",
      ko: "Danbooru category 3: 작품명/저작권 태그입니다.",
      ja: "Danbooru category 3: 作品名/著作権タグです。",
      zh: "Danbooru category 3：作品名/版权标签。",
    },
  },
  general: {
    en: "Trained tag",
    ko: "학습 태그",
    ja: "学習タグ",
    zh: "训练标签",
    color: "#4ade80",
    tip: {
      en: "Danbooru category 0: general tags that are present in the selected autocomplete CSV.",
      ko: "Danbooru category 0: 선택한 자동완성 CSV에 있는 일반 태그입니다.",
      ja: "Danbooru category 0: 選択中の自動補完 CSV に含まれる一般タグです。",
      zh: "Danbooru category 0：所选自动补全 CSV 中存在的通用标签。",
    },
  },
  meta: {
    en: "Meta",
    ko: "메타",
    ja: "メタ",
    zh: "元数据",
    color: "#94a3b8",
    tip: {
      en: "Danbooru category 5: meta tags.",
      ko: "Danbooru category 5: 메타 태그입니다.",
      ja: "Danbooru category 5: メタタグです。",
      zh: "Danbooru category 5：元数据标签。",
    },
  },
  natural: {
    en: "Natural language",
    ko: "자연어",
    ja: "自然文",
    zh: "自然语言",
    color: "#cbd5e1",
    tip: {
      en: "Natural-language prompt text, not a Danbooru tag category.",
      ko: "자연어 프롬프트 문장입니다. Danbooru 태그 카테고리가 아닙니다.",
      ja: "自然文のプロンプトです。Danbooru タグカテゴリではありません。",
      zh: "自然语言提示词文本，不是 Danbooru 标签分类。",
    },
  },
  wildcard: {
    en: "Wildcard",
    ko: "와일드카드",
    ja: "ワイルドカード",
    zh: "通配符",
    color: "#c084fc",
    tip: {
      en: "Wildcard syntax such as __name__, 3#__name__, and {a|b|c}.",
      ko: "__name__, 3#__name__, {a|b|c} 같은 와일드카드 문법입니다.",
      ja: "__name__, 3#__name__, {a|b|c} などのワイルドカード構文です。",
      zh: "__name__、3#__name__、{a|b|c} 等通配符语法。",
    },
  },
  comment: {
    en: "Comment",
    ko: "주석",
    ja: "コメント",
    zh: "注释",
    color: "#9ca3af",
    tip: {
      en: "Line-start # comments. These are displayed in Prompt Studio but removed from queued prompt tokens.",
      ko: "줄 시작 # 주석입니다. Prompt Studio에는 표시되지만 큐 실행 프롬프트 토큰에서는 제거됩니다.",
      ja: "行頭 # コメントです。Prompt Studio には表示されますが、キュー実行時のプロンプトトークンからは除去されます。",
      zh: "行首 # 注释。会显示在 Prompt Studio 中，但会从队列执行的提示词 token 中移除。",
    },
  },
  artist_unknown: {
    en: "Unregistered artist",
    ko: "미등록 작가",
    ja: "未登録作者",
    zh: "未注册作者",
    color: "#f87171",
    tip: {
      en: "An @artist token that is not found in the artist index.",
      ko: "@작가 형식이지만 작가 인덱스에서 찾지 못한 토큰입니다.",
      ja: "@artist 形式ですが作者インデックスに見つからないトークンです。",
      zh: "@artist 形式但未在作者索引中找到的 token。",
    },
  },
  unknown: {
    en: "Unknown",
    ko: "미확인",
    ja: "不明",
    zh: "未知",
    color: "#cbd5e1",
    tip: {
      en: "A tag that was not found in the selected autocomplete CSV or built-in meta rules.",
      ko: "선택한 자동완성 CSV와 내장 메타 규칙에서 찾지 못한 태그입니다.",
      ja: "選択中の自動補完 CSV と組み込みメタルールで見つからなかったタグです。",
      zh: "未在所选自动补全 CSV 或内置元规则中找到的标签。",
    },
  },
};

const NAIA_PREPROCESSING_OPTIONS = [
  ["remove_author", { en: "Remove author", ko: "작가 제거", ja: "作者を削除", zh: "移除作者" }],
  ["remove_work_title", { en: "Remove work title", ko: "작품명 제거", ja: "作品名を削除", zh: "移除作品名" }],
  ["remove_character_name", { en: "Remove character name", ko: "캐릭터명 제거", ja: "キャラクター名を削除", zh: "移除角色名" }],
  ["remove_character_features", { en: "Remove character features", ko: "캐릭터 특징 제거", ja: "キャラクター特徴を削除", zh: "移除角色特征" }],
  ["remove_clothes", { en: "Remove clothes", ko: "의상 제거", ja: "衣装を削除", zh: "移除服装" }],
  ["remove_color", { en: "Remove color", ko: "색상 제거", ja: "色を削除", zh: "移除颜色" }],
  ["remove_location_and_background_color", { en: "Remove location/background color", ko: "장소/배경색 제거", ja: "場所/背景色を削除", zh: "移除地点/背景色" }],
  ["remove_expression", { en: "Remove expression", ko: "표정 제거", ja: "表情を削除", zh: "移除表情" }],
  ["remove_pose_action", { en: "Remove pose/action", ko: "포즈/동작 제거", ja: "ポーズ/動作を削除", zh: "移除姿势/动作" }],
  ["remove_meta_tags", { en: "Remove meta tags", ko: "메타 태그 제거", ja: "メタタグを削除", zh: "移除元数据标签" }],
  ["remove_object_tags", { en: "Remove object tags", ko: "오브젝트 태그 제거", ja: "オブジェクトタグを削除", zh: "移除物体标签" }],
  ["remove_noise_tags", { en: "Remove noise tags", ko: "노이즈 태그 제거", ja: "ノイズタグを削除", zh: "移除噪声标签" }],
  ["e621_auto_boost", { en: "e621 auto boost", ko: "e621 자동 강화", ja: "e621 自動強化", zh: "e621 自动增强" }],
  ["danbooru_auto_weight", { en: "Danbooru auto weight", ko: "Danbooru 자동 가중치", ja: "Danbooru 自動重み付け", zh: "Danbooru 自动加权" }],
  ["tag_implication_compression", { en: "Tag implication compression", ko: "태그 함의 압축", ja: "タグ含意圧縮", zh: "标签含义压缩" }],
];

const NAIA_RESOLUTION_MODE_SCALE = "scale";
const NAIA_RESOLUTION_MODE_BUCKET = "bucket";
const NAIA_RESOLUTION_BUCKET_OPTIONS = ["512", "768", "896", "1024", "1280", "1536"];

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
    autocompleteCsvTip: "Select which bundled Korean Danbooru CSV powers autocomplete and tag highlighting.",
    autocompleteLimitTip: "",
    highlightBehavior: "Highlight behavior",
    highlightColor: "Highlight color",
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
    showTypoIndicators: "Show typo indicators",
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
    autocompleteCsvTip: "자동완성과 태그 하이라이트에 사용할 한국어 Danbooru CSV를 선택합니다.",
    autocompleteLimitTip: "",
    highlightBehavior: "하이라이트 동작",
    highlightColor: "하이라이트 색상",
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
    showTypoIndicators: "오타 표시",
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
    autocompleteCsvTip: "自動補完とタグハイライトに使用する同梱 Korean Danbooru CSV を選択します。",
    autocompleteLimitTip: "",
    highlightBehavior: "ハイライト動作",
    highlightColor: "ハイライト色",
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
    showTypoIndicators: "タイプミス表示",
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
    autocompleteCsvTip: "选择用于自动补全和标签高亮的内置 Korean Danbooru CSV。",
    autocompleteLimitTip: "",
    highlightBehavior: "高亮行为",
    highlightColor: "高亮颜色",
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
    showTypoIndicators: "显示错字标记",
    italicizeComments: "注释行使用斜体",
    useDesktopNaia: "使用 NAIA 桌面 Prompt Engineering 设置",
  },
};

const INTERNAL_KEYS = {
  "EasyUseAnima.Prompt.MetadataFilter": "prompt.metadata_filter_words",
  "EasyUseAnima.Prompt.AutocompleteMode": "autocomplete.mode",
  "EasyUseAnima.Prompt.AutocompleteSource": "autocomplete.source",
  "EasyUseAnima.Prompt.AutocompleteLimit": "autocomplete.limit",
  "EasyUseAnima.Prompt.AutocompleteCommitKey": "autocomplete.commit_key",
  "EasyUseAnima.Prompt.AutocompleteAppendSeparator": "autocomplete.append_separator",
  "EasyUseAnima.Prompt.AutocompleteNoCommaAfterPeriod": "autocomplete.no_comma_after_period",
  "EasyUseAnima.Prompt.AutocompleteDetectNaturalSentences": "autocomplete.detect_natural_sentences",
  "EasyUseAnima.Prompt.TypoIndicator": "prompt_studio.typo_indicator",
  "EasyUseAnima.Prompt.CommentItalic": "prompt_studio.comment_italic",
  "EasyUseAnima.Prompt.NaiaGeneralAutoToggle": "prompt_studio.naia_general_above_auto_toggle",
  "EasyUseAnima.Wildcard.ExtraPaths": "wildcard.extra_paths",
  "EasyUseAnima.LoraPreset.NameDisplay": "lora_preset.name_display",
  "EasyUseAnima.LoraPreset.MenuMode": "lora_preset.menu_mode",
  "EasyUseAnima.LoraPreset.StrengthButtonStep": "lora_preset.strength_button_step",
  "EasyUseAnima.LoraPreset.StrengthDragStep": "lora_preset.strength_drag_step",
  "EasyUseAnima.LoraPreset.StrengthDragPixels": "lora_preset.strength_drag_pixels",
  "EasyUseAnima.NAIA.Host": "naia.host",
  "EasyUseAnima.NAIA.Port": "naia.port",
  "EasyUseAnima.NAIA.UseDesktopPromptEngineering": "naia.use_naia_settings",
  "EasyUseAnima.NAIA.ResolutionMode": "naia.resolution_mode",
  "EasyUseAnima.NAIA.ResolutionBucket": "naia.resolution_bucket",
  "EasyUseAnima.NAIA.ResolutionScale": "naia.resolution_scale",
  "EasyUseAnima.NAIA.ResolutionMaxLongEdge": "naia.resolution_max_long_edge",
  "EasyUseAnima.NAIA.pre_prompt": "naia.pre_prompt",
  "EasyUseAnima.NAIA.post_prompt": "naia.post_prompt",
  "EasyUseAnima.NAIA.auto_hide": "naia.auto_hide",
};

const LONG_TEXT_FIELDS = [
  {
    key: "prompt.metadata_filter_words",
    labelKey: "metadataFilter",
    tipKey: "metadataFilterTip",
  },
  {
    key: "naia.pre_prompt",
    labelKey: "prePrompt",
  },
  {
    key: "naia.post_prompt",
    labelKey: "postPrompt",
  },
  {
    key: "naia.auto_hide",
    labelKey: "autoHide",
  },
];

const LONG_TEXT_FIELD_GROUPS = {
  promptStudio: {
    settingId: "EasyUseAnima.PromptStudio.EditLongText",
    section: "PromptStudio",
    nameKey: "editPromptStudioLongText",
    tipKey: "editPromptStudioLongTextTip",
    fields: LONG_TEXT_FIELDS.filter((field) => field.key === "prompt.metadata_filter_words"),
  },
  naia: {
    settingId: "EasyUseAnima.NAIA.EditLongText",
    section: "NAIA",
    nameKey: "editNaiaLongText",
    tipKey: "editNaiaLongTextTip",
    fields: LONG_TEXT_FIELDS.filter((field) => field.key !== "prompt.metadata_filter_words"),
  },
};

let activeLongTextEditor = null;

for (const [key] of NAIA_PREPROCESSING_OPTIONS) {
  INTERNAL_KEYS[`EasyUseAnima.NAIA.${key}`] = `naia.${key}`;
}

function t(key) {
  return easyuseAnimaText(TEXT, key);
}

function label(item) {
  return easyuseAnimaLocaleText(item);
}

function tip(item) {
  return easyuseAnimaLocaleText(item?.tip);
}

function parseColors(value) {
  try {
    const parsed = JSON.parse(value || "{}");
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function normalizeValue(type, value) {
  if (type === "boolean") {
    return value ? "true" : "false";
  }
  return String(value ?? "");
}

function updateInternalSetting(id, value, type = "text") {
  const internalKey = INTERNAL_KEYS[id];
  if (!internalKey) {
    return;
  }
  window.__easyuseAnimaSettings ||= {};
  window.__easyuseAnimaSettings[internalKey] = normalizeValue(type, value);
  window.dispatchEvent(
    new CustomEvent("easyuse-anima-settings-updated", {
      detail: { ...window.__easyuseAnimaSettings },
    }),
  );
}

function updateColorSetting(colorKey, value) {
  window.__easyuseAnimaSettings ||= {};
  const colors = parseColors(window.__easyuseAnimaSettings["prompt_studio.colors"]);
  colors[colorKey] = String(value || PROMPT_STUDIO_COLORS[colorKey]?.color || "#ffffff");
  window.__easyuseAnimaSettings["prompt_studio.colors"] = JSON.stringify(colors);
  window.dispatchEvent(
    new CustomEvent("easyuse-anima-settings-updated", {
      detail: { ...window.__easyuseAnimaSettings },
    }),
  );
}

async function loadLongTextSettings() {
  const response = await fetch("/easyuse_anima/long_text_settings");
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || `HTTP ${response.status}`);
  }
  const values = data.values || {};
  window.__easyuseAnimaSettings ||= {};
  Object.assign(window.__easyuseAnimaSettings, data.settings || {}, values);
  return { ...window.__easyuseAnimaSettings };
}

async function saveLongTextSettings(values) {
  const response = await fetch("/easyuse_anima/long_text_settings/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ values }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || `HTTP ${response.status}`);
  }
  window.__easyuseAnimaSettings ||= {};
  Object.assign(window.__easyuseAnimaSettings, data.settings || {}, data.values || {});
  window.dispatchEvent(
    new CustomEvent("easyuse-anima-settings-updated", {
      detail: { ...window.__easyuseAnimaSettings },
    }),
  );
  return data;
}

function createLongTextEditorButton(groupKey) {
  const group = LONG_TEXT_FIELD_GROUPS[groupKey];
  const container = document.createElement("div");
  container.style.cssText = "display: flex; align-items: center; gap: 10px; min-width: 0;";

  const button = document.createElement("button");
  button.type = "button";
  button.textContent = t("openEditor");
  button.style.cssText = "padding: 6px 12px; cursor: pointer;";
  button.onclick = () => openLongTextEditor(groupKey);

  const hint = document.createElement("span");
  hint.textContent = t(group.tipKey);
  hint.style.cssText = "opacity: 0.68; font-size: 0.9em; line-height: 1.35;";

  container.append(button, hint);
  return container;
}

function parseWildcardExtraPathItems(value) {
  return String(value ?? "")
    .split(/\r?\n/)
    .map((item) => item.trim().replace(/^"|"$/g, ""))
    .filter(Boolean);
}

function serializeWildcardExtraPathItems(items) {
  return items
    .map((item) => String(item ?? "").trim())
    .filter(Boolean)
    .join("\n");
}

function wildcardExtraPathsSettingValue(value) {
  if (
    window.__easyuseAnimaSettings
    && Object.prototype.hasOwnProperty.call(window.__easyuseAnimaSettings, "wildcard.extra_paths")
  ) {
    return window.__easyuseAnimaSettings["wildcard.extra_paths"];
  }
  return value ?? "";
}

function createWildcardExtraPathsEditor(name, setter, value) {
  const settingId = "EasyUseAnima.Wildcard.ExtraPaths";
  let items = parseWildcardExtraPathItems(wildcardExtraPathsSettingValue(value));
  if (!items.length) {
    items = [""];
  }

  const row = document.createElement("tr");

  const labelCell = document.createElement("td");
  const labelEl = document.createElement("label");
  labelEl.textContent = name;
  labelEl.title = t("wildcardExtraPathsTip");
  labelCell.append(labelEl);

  const controlCell = document.createElement("td");
  const wrapper = document.createElement("div");
  wrapper.style.cssText = "display: flex; flex-direction: column; gap: 6px; min-width: 260px;";

  const list = document.createElement("div");
  list.style.cssText = "display: flex; flex-direction: column; gap: 6px;";

  let persistedValue = serializeWildcardExtraPathItems(items);

  const syncInternal = () => {
    const serialized = serializeWildcardExtraPathItems(items);
    updateInternalSetting(settingId, serialized, "text");
  };

  const persist = () => {
    const serialized = serializeWildcardExtraPathItems(items);
    updateInternalSetting(settingId, serialized, "text");
    if (serialized === persistedValue) {
      return;
    }
    persistedValue = serialized;
    setter?.(serialized);
  };

  const render = () => {
    list.replaceChildren();
    if (!items.length) {
      items = [""];
    }

    items.forEach((item, index) => {
      const itemRow = document.createElement("div");
      itemRow.style.cssText = "display: flex; align-items: center; gap: 6px; min-width: 0;";

      const input = document.createElement("input");
      input.type = "text";
      input.value = item;
      input.placeholder = t("wildcardExtraPathPlaceholder");
      input.spellcheck = false;
      input.style.cssText = "box-sizing: border-box; flex: 1 1 auto; min-width: 120px; padding: 4px 6px;";
      input.addEventListener("input", () => {
        items[index] = input.value;
        syncInternal();
      });
      input.addEventListener("change", persist);
      input.addEventListener("blur", persist);
      input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
          event.preventDefault();
          input.blur();
        }
      });

      const removeButton = document.createElement("button");
      removeButton.type = "button";
      removeButton.textContent = "x";
      removeButton.title = t("removeWildcardPath");
      removeButton.style.cssText = "width: 28px; min-width: 28px; height: 28px; padding: 0; cursor: pointer;";
      removeButton.addEventListener("click", () => {
        if (items.length <= 1) {
          items[0] = "";
        } else {
          items.splice(index, 1);
        }
        persist();
        render();
      });

      itemRow.append(input, removeButton);
      list.append(itemRow);
    });
  };

  const addButton = document.createElement("button");
  addButton.type = "button";
  addButton.textContent = "+";
  addButton.title = t("addWildcardPath");
  addButton.style.cssText = "align-self: flex-start; min-width: 32px; height: 28px; padding: 0 10px; cursor: pointer;";
  addButton.addEventListener("click", () => {
    items.push("");
    render();
    list.lastElementChild?.querySelector("input")?.focus();
  });

  render();
  wrapper.append(list, addButton);
  controlCell.append(wrapper);
  row.append(labelCell, controlCell);
  return row;
}

function normalizeNaiaResolutionModeValue(value) {
  const raw = String(value ?? "").trim().toLowerCase();
  if (raw === NAIA_RESOLUTION_MODE_BUCKET || raw === "bucket_fit") {
    return NAIA_RESOLUTION_MODE_BUCKET;
  }
  return NAIA_RESOLUTION_MODE_SCALE;
}

function naiaResolutionModeSettingValue(value) {
  if (
    window.__easyuseAnimaSettings
    && Object.prototype.hasOwnProperty.call(window.__easyuseAnimaSettings, "naia.resolution_mode")
  ) {
    return window.__easyuseAnimaSettings["naia.resolution_mode"];
  }
  return value ?? NAIA_RESOLUTION_MODE_SCALE;
}

function createNaiaResolutionModeEditor(name, setter, value) {
  const settingId = "EasyUseAnima.NAIA.ResolutionMode";
  let persistedValue = normalizeNaiaResolutionModeValue(naiaResolutionModeSettingValue(value));

  const row = document.createElement("tr");

  const labelCell = document.createElement("td");
  const labelEl = document.createElement("label");
  labelEl.textContent = name;
  labelEl.title = t("naiaResolutionModeTip");
  labelCell.append(labelEl);

  const controlCell = document.createElement("td");
  const select = document.createElement("select");
  select.setAttribute("aria-label", name);
  select.style.cssText = "box-sizing: border-box; min-width: 150px; padding: 4px 6px;";
  for (const [mode, labelKey] of [
    [NAIA_RESOLUTION_MODE_SCALE, "naiaResolutionModeOriginalScale"],
    [NAIA_RESOLUTION_MODE_BUCKET, "naiaResolutionModeBucketFit"],
  ]) {
    const option = document.createElement("option");
    option.value = mode;
    option.textContent = t(labelKey);
    option.selected = mode === persistedValue;
    select.append(option);
  }

  const persist = () => {
    const nextValue = normalizeNaiaResolutionModeValue(select.value);
    select.value = nextValue;
    updateInternalSetting(settingId, nextValue, "text");
    if (nextValue === persistedValue) {
      return;
    }
    persistedValue = nextValue;
    setter?.(nextValue);
  };

  select.addEventListener("change", persist);
  controlCell.append(select);
  row.append(labelCell, controlCell);
  updateInternalSetting(settingId, persistedValue, "text");
  return row;
}

function naiaResolutionScaleSettingValue(value) {
  if (
    window.__easyuseAnimaSettings
    && Object.prototype.hasOwnProperty.call(window.__easyuseAnimaSettings, "naia.resolution_scale")
  ) {
    return window.__easyuseAnimaSettings["naia.resolution_scale"];
  }
  return value ?? "1.0";
}

function normalizeNaiaResolutionScaleValue(value) {
  const parsed = Number.parseFloat(String(value ?? "").replace(",", "."));
  const clamped = Number.isFinite(parsed)
    ? Math.min(4.0, Math.max(0.25, parsed))
    : 1.0;
  const rounded = Math.round(clamped * 1000) / 1000;
  return Number.isInteger(rounded) ? `${rounded}.0` : String(rounded);
}

function createNaiaResolutionScaleEditor(name, setter, value) {
  const settingId = "EasyUseAnima.NAIA.ResolutionScale";
  let persistedValue = normalizeNaiaResolutionScaleValue(naiaResolutionScaleSettingValue(value));

  const row = document.createElement("tr");

  const labelCell = document.createElement("td");
  const labelEl = document.createElement("label");
  labelEl.textContent = name;
  labelEl.title = t("naiaResolutionScaleTip");
  labelCell.append(labelEl);

  const controlCell = document.createElement("td");
  const input = document.createElement("input");
  input.type = "text";
  input.inputMode = "decimal";
  input.value = persistedValue;
  input.placeholder = "1.5";
  input.spellcheck = false;
  input.style.cssText = "box-sizing: border-box; width: 92px; padding: 4px 6px;";

  const syncRaw = () => {
    updateInternalSetting(settingId, input.value.replace(",", "."), "text");
  };
  const persist = () => {
    const normalized = normalizeNaiaResolutionScaleValue(input.value);
    input.value = normalized;
    updateInternalSetting(settingId, normalized, "text");
    if (normalized === persistedValue) {
      return;
    }
    persistedValue = normalized;
    setter?.(normalized);
  };

  input.addEventListener("input", syncRaw);
  input.addEventListener("change", persist);
  input.addEventListener("blur", persist);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      input.blur();
    }
  });

  controlCell.append(input);
  row.append(labelCell, controlCell);
  updateInternalSetting(settingId, persistedValue, "text");
  return row;
}

function closeLongTextEditor() {
  if (!activeLongTextEditor) {
    return;
  }
  const { overlay, keyHandler } = activeLongTextEditor;
  document.removeEventListener("keydown", keyHandler, true);
  overlay.remove();
  activeLongTextEditor = null;
}

function openLongTextEditor(groupKey) {
  const group = LONG_TEXT_FIELD_GROUPS[groupKey];
  if (!group) {
    return;
  }
  closeLongTextEditor();

  const overlay = document.createElement("div");
  overlay.className = "easyuse-anima-long-text-overlay";
  overlay.style.cssText =
    "position: fixed; inset: 0; z-index: 2147483000; display: flex; align-items: center; justify-content: center; padding: 24px; box-sizing: border-box; background: rgba(0, 0, 0, 0.52);";

  const panel = document.createElement("div");
  panel.className = "comfy-settings easyuse-anima-long-text-panel";
  panel.style.cssText =
    "box-sizing: border-box; width: min(820px, 92vw); max-height: min(780px, 86vh); overflow: hidden; display: flex; flex-direction: column; gap: 12px; padding: 18px; border-radius: 8px; background: var(--comfy-menu-bg, #202020); color: var(--fg-color, #ddd); box-shadow: 0 18px 60px rgba(0, 0, 0, 0.55);";

  const container = document.createElement("div");
  container.style.cssText =
    "box-sizing: border-box; overflow: auto; display: flex; flex-direction: column; gap: 14px; padding-right: 4px;";

  const title = document.createElement("h3");
  title.textContent = t(group.nameKey);
  title.style.margin = "0 0 2px";

  const description = document.createElement("div");
  description.textContent = t(group.tipKey);
  description.style.cssText = "opacity: 0.72; line-height: 1.45;";

  const status = document.createElement("div");
  status.style.cssText = "min-height: 1.4em; opacity: 0.76;";

  const textareas = new Map();
  for (const field of group.fields) {
    const wrapper = document.createElement("label");
    wrapper.style.cssText = "display: flex; flex-direction: column; gap: 6px;";

    const labelText = document.createElement("span");
    labelText.textContent = t(field.labelKey);
    labelText.style.fontWeight = "600";

    const textarea = document.createElement("textarea");
    textarea.spellcheck = false;
    textarea.rows = field.key === "prompt.metadata_filter_words" ? 8 : 7;
    textarea.style.cssText =
      "box-sizing: border-box; width: 100%; min-height: 130px; resize: vertical; padding: 8px; font-family: monospace; white-space: pre-wrap;";

    const help = document.createElement("span");
    help.textContent = field.tipKey ? t(field.tipKey) : "";
    help.style.cssText = "opacity: 0.62; font-size: 0.9em;";

    wrapper.append(labelText, textarea);
    if (help.textContent) {
      wrapper.append(help);
    }
    container.append(wrapper);
    textareas.set(field.key, textarea);
  }

  container.prepend(title, description);
  container.append(status);

  const setStatus = (message, color = "") => {
    status.textContent = message;
    status.style.color = color;
  };

  const actions = document.createElement("div");
  actions.style.cssText = "display: flex; justify-content: flex-end; gap: 8px; flex: 0 0 auto;";

  const cancelButton = document.createElement("button");
  cancelButton.type = "button";
  cancelButton.textContent = t("cancel");
  cancelButton.style.cssText = "padding: 6px 12px; cursor: pointer;";
  cancelButton.onclick = closeLongTextEditor;

  const saveButton = document.createElement("button");
  saveButton.type = "button";
  saveButton.textContent = t("save");
  saveButton.style.cssText = "padding: 6px 12px; cursor: pointer;";

  saveButton.onclick = async () => {
    const values = {};
    for (const [key, textarea] of textareas.entries()) {
      values[key] = textarea.value;
    }
    saveButton.disabled = true;
    setStatus("...");
    try {
      await saveLongTextSettings(values);
      setStatus(t("saved"), "#16a34a");
      setTimeout(() => {
        if (activeLongTextEditor?.overlay === overlay) {
          closeLongTextEditor();
        }
      }, 150);
    } catch (error) {
      setStatus(`${t("saveFailed")}: ${error.message || error}`, "#dc2626");
    } finally {
      saveButton.disabled = false;
    }
  };

  actions.append(cancelButton, saveButton);
  panel.append(container, actions);
  overlay.append(panel);

  overlay.addEventListener("mousedown", (event) => {
    if (event.target === overlay) {
      closeLongTextEditor();
    }
  });
  panel.addEventListener("mousedown", (event) => event.stopPropagation());

  const keyHandler = (event) => {
    if (event.key === "Escape") {
      closeLongTextEditor();
    }
  };
  document.addEventListener("keydown", keyHandler, true);
  activeLongTextEditor = { overlay, keyHandler };

  document.body.append(overlay);
  loadLongTextSettings()
    .then((settings) => {
      if (activeLongTextEditor?.overlay !== overlay) {
        return;
      }
      for (const [key, textarea] of textareas.entries()) {
        textarea.value = settings[key] || "";
      }
      textareas.values().next().value?.focus();
    })
    .catch((error) => {
      if (activeLongTextEditor?.overlay !== overlay) {
        return;
      }
      setStatus(`${t("saveFailed")}: ${error.message || error}`, "#dc2626");
    });
}

function setting({ id, section, group, name, tooltip, type, defaultValue, options, attrs, onChange }) {
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

function colorSetting(colorKey, item) {
  const id = `EasyUseAnima.Prompt.HighlightColor.${colorKey}`;
  return setting({
    id,
    section: "PromptStudio",
    group: t("highlightColor"),
    name: `${t("highlightColor")}: ${label(item)}`,
    tooltip: tip(item),
    type: "color",
    defaultValue: item.color,
    onChange: (value) => updateColorSetting(colorKey, value),
  });
}

const EASYUSE_ANIMA_SETTINGS = [
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
    defaultValue: "localsmile_kr_wiki",
    options: ["localsmile_kr_wiki", "kr_modified"],
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
    id: "EasyUseAnima.Prompt.TypoIndicator",
    section: "PromptStudio",
    group: t("highlightBehavior"),
    name: t("showTypoIndicators"),
    type: "boolean",
    defaultValue: true,
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
    id: "EasyUseAnima.Prompt.NaiaGeneralAutoToggle",
    section: "PromptStudio",
    group: t("highlightBehavior"),
    name: t("naiaGeneralAutoToggle"),
    tooltip: t("naiaGeneralAutoToggleTip"),
    type: "boolean",
    defaultValue: false,
  }),
  ...Object.entries(PROMPT_STUDIO_COLORS).map(([colorKey, item]) => colorSetting(colorKey, item)),
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

async function loadInitialSettings() {
  try {
    const response = await fetch("/easyuse_anima/settings");
    if (!response.ok) {
      return {};
    }
    return await response.json();
  } catch {
    return {};
  }
}

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
    window.__easyuseAnimaSettings = await loadInitialSettings();
    addSettingsFallback();
  },
});
