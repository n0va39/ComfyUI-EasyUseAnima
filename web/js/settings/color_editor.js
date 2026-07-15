// @ts-check

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
  translation: {
    en: "Translation marker",
    ko: "번역 구문",
    ja: "翻訳構文",
    zh: "翻译语法",
    color: "#22d3ee",
    tip: {
      en: "Prompt text wrapped as %{...}. The marked sentence is translated before queued prompt processing.",
      ko: "%{...}로 감싼 프롬프트 문장입니다. 큐 실행 시 번역 후 프롬프트 처리에 사용됩니다.",
      ja: "%{...} で囲んだプロンプト文です。キュー実行時に翻訳してからプロンプト処理に使います。",
      zh: "用 %{...} 包裹的提示词句子。队列执行时会先翻译再进行提示词处理。",
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

const PROMPT_STUDIO_COLOR_GROUPS = [
  {
    id: "tags",
    labelKey: "highlightColorTabTags",
    keys: [
      "quality",
      "safety",
      "year",
      "count",
      "general",
      "character",
      "artist",
      "artist_unknown",
      "copyright",
      "meta",
      "unknown",
    ],
  },
  {
    id: "syntax",
    labelKey: "highlightColorTabSyntax",
    keys: [
      "natural",
      "translation",
      "wildcard",
      "comment",
    ],
  },
];

/**
 * @typedef {object} PromptStudioColorEditorDependencies
 * @property {Document} document
 * @property {(key: string) => string} text
 * @property {(item: any) => string} label
 * @property {(item: any) => string} tip
 * @property {(key: string, fallback: any) => any} readInternalSetting
 * @property {(id: string, value: any, type?: string) => void} updateInternalSetting
 */

/**
 * Own the Prompt Studio color-editor DOM and modal lifecycle while leaving
 * locale selection and global settings persistence with the caller.
 *
 * @param {PromptStudioColorEditorDependencies} dependencies
 */
export function createPromptStudioColorEditorButtonFactory(dependencies) {
  const {
    document,
    text: t,
    label,
    tip,
    readInternalSetting,
    updateInternalSetting,
  } = dependencies;

  let activePromptStudioColorEditor = null;

  function parseColors(value) {
    try {
      const parsed = JSON.parse(value || "{}");
      return parsed && typeof parsed === "object" ? parsed : {};
    } catch {
      return {};
    }
  }
  function promptStudioColorSettingValue(value) {
    return readInternalSetting("prompt_studio.colors", value ?? "");
  }
  
  function serializePromptStudioColors(colors) {
    const normalized = {};
    for (const [key, value] of Object.entries(colors || {})) {
      const color = String(value || "").trim();
      if (PROMPT_STUDIO_COLORS[key] && /^#[0-9a-f]{6}$/i.test(color)) {
        normalized[key] = color;
      }
    }
    return Object.keys(normalized).length ? JSON.stringify(normalized) : "";
  }
  
  function persistPromptStudioColorSettings(colors, setter) {
    const serialized = serializePromptStudioColors(colors);
    updateInternalSetting("EasyUseAnima.Prompt.HighlightColors", serialized, "text");
    setter?.(serialized);
  }
  
  function createPromptStudioColorEditorButton(_name, setter, value) {
    const container = document.createElement("div");
    container.style.cssText = "display: flex; align-items: center; gap: 10px; min-width: 0;";
  
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = t("openEditor");
    button.style.cssText = "padding: 6px 12px; cursor: pointer;";
    button.onclick = () => openPromptStudioColorEditor(setter, value);
  
    const hint = document.createElement("span");
    hint.textContent = t("highlightColorEditorTip");
    hint.style.cssText = "opacity: 0.68; font-size: 0.9em; line-height: 1.35;";
  
    container.append(button, hint);
    return container;
  }
  
  function closePromptStudioColorEditor() {
    if (!activePromptStudioColorEditor) {
      return;
    }
    const { overlay, keyHandler } = activePromptStudioColorEditor;
    document.removeEventListener("keydown", keyHandler, true);
    overlay.remove();
    activePromptStudioColorEditor = null;
  }
  
  function openPromptStudioColorEditor(setter, value) {
    closePromptStudioColorEditor();
  
    const colors = parseColors(promptStudioColorSettingValue(value));
    let activeGroupId = PROMPT_STUDIO_COLOR_GROUPS[0]?.id || "";
  
    const overlay = document.createElement("div");
    overlay.className = "easyuse-anima-prompt-color-overlay";
    overlay.style.cssText =
      "position: fixed; inset: 0; z-index: 2147483000; display: flex; align-items: center; justify-content: center; padding: 24px; box-sizing: border-box; background: rgba(0, 0, 0, 0.52);";
  
    const panel = document.createElement("div");
    panel.className = "comfy-settings easyuse-anima-prompt-color-panel";
    panel.style.cssText =
      "box-sizing: border-box; width: min(760px, 92vw); max-height: min(760px, 86vh); overflow: hidden; display: flex; flex-direction: column; gap: 12px; padding: 18px; border-radius: 8px; background: var(--comfy-menu-bg, #202020); color: var(--fg-color, #ddd); box-shadow: 0 18px 60px rgba(0, 0, 0, 0.55);";
  
    const title = document.createElement("h3");
    title.textContent = t("highlightColorEditor");
    title.style.margin = "0";
  
    const description = document.createElement("div");
    description.textContent = t("highlightColorEditorTip");
    description.style.cssText = "opacity: 0.72; line-height: 1.45;";
  
    const tabs = document.createElement("div");
    tabs.style.cssText = "display: flex; flex-wrap: wrap; gap: 6px; flex: 0 0 auto;";
  
    const content = document.createElement("div");
    content.style.cssText = "overflow: auto; display: flex; flex-direction: column; gap: 8px; padding-right: 4px;";
  
    const tabButtons = new Map();
    const render = () => {
      for (const [groupId, button] of tabButtons.entries()) {
        const active = groupId === activeGroupId;
        button.setAttribute("aria-selected", active ? "true" : "false");
        button.style.background = active ? "var(--comfy-input-bg, #303030)" : "transparent";
        button.style.borderColor = active ? "rgba(148, 163, 184, 0.8)" : "rgba(128, 128, 128, 0.4)";
      }
  
      content.replaceChildren();
      const group = PROMPT_STUDIO_COLOR_GROUPS.find((item) => item.id === activeGroupId)
        || PROMPT_STUDIO_COLOR_GROUPS[0];
      for (const colorKey of group?.keys || []) {
        const item = PROMPT_STUDIO_COLORS[colorKey];
        if (!item) {
          continue;
        }
        const row = document.createElement("div");
        row.style.cssText =
          "display: grid; grid-template-columns: minmax(150px, 1fr) 70px auto; align-items: center; gap: 10px; min-width: 0; padding: 6px 0;";
  
        const labelWrap = document.createElement("label");
        labelWrap.style.cssText = "display: flex; flex-direction: column; gap: 2px; min-width: 0;";
  
        const labelText = document.createElement("span");
        labelText.textContent = label(item);
        labelText.style.fontWeight = "600";
  
        const help = document.createElement("span");
        help.textContent = tip(item);
        help.style.cssText = "opacity: 0.62; font-size: 0.9em; line-height: 1.25;";
  
        const input = document.createElement("input");
        input.type = "color";
        input.value = /^#[0-9a-f]{6}$/i.test(String(colors[colorKey] || ""))
          ? String(colors[colorKey])
          : item.color;
        input.style.cssText = "width: 64px; height: 30px; padding: 0; cursor: pointer;";
        input.setAttribute("aria-label", label(item));
  
        const resetButton = document.createElement("button");
        resetButton.type = "button";
        resetButton.textContent = t("reset");
        resetButton.style.cssText = "padding: 5px 10px; cursor: pointer;";
  
        input.addEventListener("input", () => {
          colors[colorKey] = input.value;
          persistPromptStudioColorSettings(colors, setter);
        });
        input.addEventListener("change", () => {
          colors[colorKey] = input.value;
          persistPromptStudioColorSettings(colors, setter);
        });
        resetButton.addEventListener("click", () => {
          colors[colorKey] = item.color;
          input.value = item.color;
          persistPromptStudioColorSettings(colors, setter);
        });
  
        labelWrap.append(labelText, help);
        row.append(labelWrap, input, resetButton);
        content.append(row);
      }
    };
  
    for (const group of PROMPT_STUDIO_COLOR_GROUPS) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = t(group.labelKey);
      button.style.cssText =
        "padding: 6px 12px; border: 1px solid rgba(128, 128, 128, 0.4); border-radius: 6px; color: inherit; cursor: pointer;";
      button.setAttribute("role", "tab");
      button.onclick = () => {
        activeGroupId = group.id;
        render();
      };
      tabButtons.set(group.id, button);
      tabs.append(button);
    }
  
    const actions = document.createElement("div");
    actions.style.cssText = "display: flex; justify-content: flex-end; gap: 8px; flex: 0 0 auto;";
  
    const closeButton = document.createElement("button");
    closeButton.type = "button";
    closeButton.textContent = t("close");
    closeButton.style.cssText = "padding: 6px 12px; cursor: pointer;";
    closeButton.onclick = closePromptStudioColorEditor;
    actions.append(closeButton);
  
    panel.append(title, description, tabs, content, actions);
    overlay.append(panel);
  
    overlay.addEventListener("mousedown", (event) => {
      if (event.target === overlay) {
        closePromptStudioColorEditor();
      }
    });
    panel.addEventListener("mousedown", (event) => event.stopPropagation());
  
    const keyHandler = (event) => {
      if (event.key === "Escape") {
        closePromptStudioColorEditor();
      }
    };
    document.addEventListener("keydown", keyHandler, true);
    activePromptStudioColorEditor = { overlay, keyHandler };
  
    document.body.append(overlay);
    render();
  }
  return createPromptStudioColorEditorButton;
}
