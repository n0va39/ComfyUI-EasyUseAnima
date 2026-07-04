// @ts-check

function ensureAdvancedStyle() {
  if (document.getElementById("easyuse-anima-advanced-style")) {
    return;
  }
  const style = document.createElement("style");
  style.id = "easyuse-anima-advanced-style";
  style.textContent = `
    .easyuse-anima-advanced-editor {
      box-sizing: border-box;
      width: 100%;
      min-width: 0;
      overflow-x: hidden;
      overflow-y: auto;
      overscroll-behavior: contain;
      color: var(--fg-color, #ddd);
      font: 12px sans-serif;
      user-select: none;
    }
    .easyuse-anima-advanced-panes {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .easyuse-anima-advanced-editor.is-narrow .easyuse-anima-advanced-panes {
      flex-direction: column;
    }
    .easyuse-anima-advanced-controlbar {
      display: flex;
      flex-wrap: wrap;
      align-items: flex-start;
      gap: 5px;
      margin-bottom: 7px;
    }
    .easyuse-anima-advanced-controlgroup {
      min-width: 160px;
      flex: 1 1 180px;
      display: grid;
      grid-template-columns: auto minmax(0, 1fr);
      align-items: center;
      gap: 7px;
      border: 1px solid rgba(148, 163, 184, 0.24);
      background: rgba(15, 23, 42, 0.34);
      padding: 5px;
      box-sizing: border-box;
    }
    .easyuse-anima-advanced-controlgroup.is-active {
      border-color: rgba(96, 165, 250, 0.45);
      background: rgba(30, 64, 112, 0.28);
    }
    .easyuse-anima-advanced-controlgroup-header {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      min-width: 86px;
      height: 24px;
      padding: 0 9px;
      border: 1px solid rgba(148, 163, 184, 0.32);
      background: rgba(30, 41, 59, 0.82);
      color: rgba(226, 232, 240, 0.88);
      font: 11px sans-serif;
      line-height: 1;
      cursor: pointer;
    }
    .easyuse-anima-advanced-controlgroup.is-active .easyuse-anima-advanced-controlgroup-header {
      color: #fff;
      font-weight: 700;
    }
    .easyuse-anima-advanced-controlgroup-summary {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      color: rgba(148, 163, 184, 0.9);
      font-weight: 400;
    }
    .easyuse-anima-advanced-inline-summary {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      color: rgba(203, 213, 225, 0.78);
      font: 11px sans-serif;
    }
    .easyuse-anima-advanced-controlgroup-row {
      display: grid;
      grid-template-columns: minmax(48px, 0.35fr) minmax(0, 0.65fr);
      align-items: center;
      gap: 6px;
    }
    .easyuse-anima-advanced-controlgroup-label {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      color: rgba(203, 213, 225, 0.76);
      font: 10px sans-serif;
    }
    .easyuse-anima-advanced-controlgroup-row select,
    .easyuse-anima-advanced-controlgroup-row input {
      box-sizing: border-box;
      min-width: 0;
      width: 100%;
      height: 24px;
      border: 1px solid rgba(148, 163, 184, 0.34);
      background: rgba(15, 23, 42, 0.88);
      color: rgba(226, 232, 240, 0.9);
      font: 10px sans-serif;
      padding: 2px 6px;
      outline: none;
    }
    .easyuse-anima-advanced-controlgroup-row select:focus,
    .easyuse-anima-advanced-controlgroup-row input:focus {
      border-color: rgba(96, 165, 250, 0.76);
    }
    .easyuse-anima-advanced-toggle {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 34px;
      height: 21px;
      padding: 0 7px;
      border: 1px solid rgba(148, 163, 184, 0.36);
      background: rgba(30, 41, 59, 0.78);
      color: rgba(226, 232, 240, 0.72);
      font: 10px sans-serif;
      line-height: 1;
      cursor: pointer;
    }
    .easyuse-anima-advanced-toggle.is-on {
      border-color: rgba(96, 165, 250, 0.78);
      background: rgba(37, 99, 235, 0.68);
      color: #fff;
      font-weight: 700;
    }
    .easyuse-anima-advanced-toggle.is-linked {
      opacity: 0.55;
      cursor: default;
    }
    .easyuse-anima-advanced-resolutionbar {
      display: grid;
      grid-template-columns: auto minmax(0, 1fr);
      align-items: center;
      gap: 8px;
      margin: 0 0 10px;
    }
    .easyuse-anima-advanced-wildcardbar {
      display: grid;
      grid-template-columns: auto minmax(0, 1fr);
      align-items: center;
      gap: 8px;
      margin: 0 0 10px;
    }
    .easyuse-anima-advanced-popup-button {
      min-width: 112px;
      height: 27px;
      border: 1px solid rgba(148, 163, 184, 0.34);
      background: rgba(30, 41, 59, 0.82);
      color: rgba(226, 232, 240, 0.9);
      font: 11px sans-serif;
      padding: 2px 9px;
      cursor: pointer;
    }
    .easyuse-anima-advanced-popup-button:hover,
    .easyuse-anima-advanced-controlgroup-header:hover {
      border-color: rgba(96, 165, 250, 0.72);
    }
    .easyuse-anima-advanced-wildcardbar select,
    .easyuse-anima-advanced-wildcardbar input {
      box-sizing: border-box;
      min-width: 0;
      width: 100%;
      height: 27px;
      border: 1px solid rgba(148, 163, 184, 0.34);
      background: rgba(15, 23, 42, 0.88);
      color: rgba(226, 232, 240, 0.9);
      font: 11px sans-serif;
      padding: 2px 8px;
      outline: none;
    }
    .easyuse-anima-advanced-wildcardbar select:focus,
    .easyuse-anima-advanced-wildcardbar input:focus {
      border-color: rgba(96, 165, 250, 0.76);
    }
    .easyuse-anima-advanced-resolutionbar select,
    .easyuse-anima-advanced-resolutionbar input {
      box-sizing: border-box;
      min-width: 0;
      width: 100%;
      height: 27px;
      border: 1px solid rgba(148, 163, 184, 0.34);
      background: rgba(15, 23, 42, 0.88);
      color: rgba(226, 232, 240, 0.9);
      font: 11px sans-serif;
      padding: 2px 8px;
      outline: none;
    }
    .easyuse-anima-advanced-resolutionbar select:focus,
    .easyuse-anima-advanced-resolutionbar input:focus {
      border-color: rgba(96, 165, 250, 0.76);
    }
    .easyuse-anima-advanced-resolution-custom {
      display: grid;
      grid-template-columns: minmax(72px, 1fr) auto minmax(72px, 1fr);
      gap: 6px;
      align-items: center;
    }
    .easyuse-anima-advanced-resolution-custom span {
      color: rgba(203, 213, 225, 0.72);
      font: 12px sans-serif;
    }
    .easyuse-anima-advanced-popup-backdrop {
      position: fixed;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 100000;
      background: rgba(5, 7, 10, 0.55);
    }
    .easyuse-anima-advanced-popup {
      width: min(560px, calc(100vw - 44px));
      max-height: min(620px, calc(100vh - 44px));
      display: flex;
      flex-direction: column;
      overflow: hidden;
      color: rgba(226, 232, 240, 0.95);
      background: #171b20;
      border: 1px solid rgba(148, 163, 184, 0.42);
      box-shadow: 0 18px 56px rgba(0, 0, 0, 0.45);
      border-radius: 8px;
      font: 13px sans-serif;
    }
    .easyuse-anima-advanced-popup header {
      display: flex;
      justify-content: space-between;
      gap: 14px;
      padding: 15px 17px 12px;
      border-bottom: 1px solid rgba(148, 163, 184, 0.2);
    }
    .easyuse-anima-advanced-popup h2 {
      margin: 0 0 6px;
      font-size: 18px;
    }
    .easyuse-anima-advanced-popup p {
      margin: 0;
      color: rgba(203, 213, 225, 0.68);
      line-height: 1.35;
    }
    .easyuse-anima-advanced-popup-close {
      align-self: flex-start;
      min-width: 64px;
      min-height: 34px;
      border: 1px solid rgba(148, 163, 184, 0.34);
      background: rgba(30, 41, 59, 0.88);
      color: rgba(226, 232, 240, 0.92);
      cursor: pointer;
    }
    .easyuse-anima-advanced-popup-body {
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 9px;
      padding: 14px 17px 17px;
      overflow: auto;
    }
    .easyuse-anima-advanced-popup-body .easyuse-anima-advanced-controlgroup-row {
      grid-template-columns: minmax(126px, 0.35fr) minmax(0, 0.65fr) auto;
      min-height: 28px;
    }
    .easyuse-anima-advanced-help {
      width: 22px;
      height: 22px;
      padding: 0;
      border-radius: 50%;
      border: 1px solid rgba(148, 163, 184, 0.34);
      background: rgba(30, 41, 59, 0.82);
      color: rgba(203, 213, 225, 0.88);
      font: 700 12px sans-serif;
      line-height: 1;
      cursor: pointer;
    }
    .easyuse-anima-advanced-help:hover {
      border-color: rgba(96, 165, 250, 0.72);
      color: #fff;
    }
    .easyuse-anima-advanced-help-popover {
      position: fixed;
      z-index: 100002;
      max-width: min(320px, calc(100vw - 32px));
      padding: 9px 10px;
      border: 1px solid rgba(148, 163, 184, 0.38);
      border-radius: 6px;
      background: #10151b;
      color: rgba(226, 232, 240, 0.94);
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.42);
      font: 12px/1.45 sans-serif;
      white-space: normal;
    }
    .easyuse-anima-advanced-popup-note {
      padding: 8px 9px;
      border: 1px solid rgba(74, 222, 128, 0.18);
      background: rgba(34, 197, 94, 0.08);
      color: rgba(203, 213, 225, 0.82);
      line-height: 1.35;
    }
    .easyuse-anima-advanced-pane {
      min-width: 0;
      border: 1px solid rgba(148, 163, 184, 0.28);
      background: rgba(15, 23, 42, 0.28);
      padding: 6px;
      box-sizing: border-box;
    }
    .easyuse-anima-advanced-pane-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      margin-bottom: 6px;
      color: rgba(226, 232, 240, 0.82);
      font-weight: 700;
    }
    .easyuse-anima-advanced-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      justify-content: flex-end;
    }
    .easyuse-anima-advanced-actions button,
    .easyuse-anima-field-tools button {
      border: 1px solid rgba(148, 163, 184, 0.34);
      background: rgba(30, 41, 59, 0.8);
      color: rgba(226, 232, 240, 0.9);
      font: 11px sans-serif;
      min-height: 20px;
      padding: 1px 6px;
      cursor: pointer;
    }
    .easyuse-anima-advanced-actions button:disabled,
    .easyuse-anima-field-tools button:disabled {
      opacity: 0.35;
      cursor: default;
    }
    .easyuse-anima-advanced-field {
      margin: 0 0 6px;
    }
    .easyuse-anima-advanced-field.is-disabled {
      opacity: 0.58;
    }
    .easyuse-anima-field-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      min-height: 20px;
      color: rgba(203, 213, 225, 0.86);
    }
    .easyuse-anima-field-label {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .easyuse-anima-field-tools {
      display: flex;
      gap: 3px;
      flex: 0 0 auto;
    }
    .easyuse-anima-field-tools button.easyuse-anima-naia-fill {
      min-width: 78px;
      font-weight: 700;
    }
    .easyuse-anima-field-tools button.easyuse-anima-trigger-pin {
      min-width: 58px;
      font-weight: 700;
    }
    .easyuse-anima-field-tools button.is-on {
      border-color: rgba(96, 165, 250, 0.78);
      background: rgba(37, 99, 235, 0.58);
      color: #fff;
    }
    .easyuse-anima-advanced-field textarea {
      box-sizing: border-box;
      width: 100%;
      min-height: 46px;
      resize: vertical;
      overflow: hidden;
      border: 1px solid rgba(148, 163, 184, 0.28);
      background: rgba(10, 10, 12, 0.78);
      color: var(--input-text, #ddd);
      padding: 6px;
      font-family: var(--easyuse-anima-prompt-studio-font-family, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif);
      font-size: var(--easyuse-anima-prompt-studio-font-size, 1rem);
      line-height: 1.35;
      outline: none;
    }
    .easyuse-anima-advanced-field textarea:focus {
      border-color: rgba(96, 165, 250, 0.7);
    }
    .easyuse-anima-advanced-field textarea.is-linked {
      opacity: 0.72;
      border-style: dashed;
      cursor: default;
    }
    .easyuse-anima-advanced-field.is-naia textarea {
      border-style: dashed;
      background: rgba(15, 23, 42, 0.74);
      cursor: default;
    }
    .easyuse-anima-advanced-field.is-trigger textarea {
      border-style: dashed;
      background: rgba(12, 20, 34, 0.78);
      cursor: default;
    }
    .easyuse-anima-empty-pane {
      padding: 10px 4px;
      color: rgba(148, 163, 184, 0.72);
      font-size: 11px;
    }
  `;
  document.head.append(style);
}

function ensureExtendSlotStyle() {
  if (document.getElementById("easyuse-anima-extend-slot-style")) {
    return;
  }
  const style = document.createElement("style");
  style.id = "easyuse-anima-extend-slot-style";
  style.textContent = `
    .easyuse-anima-extend-slots {
      box-sizing: border-box;
      width: 100%;
      padding-bottom: 4px;
      color: var(--fg-color, #ddd);
      font: 11px sans-serif;
      user-select: none;
    }
    .easyuse-anima-extend-slot-row {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 5px;
      width: 100%;
    }
    .easyuse-anima-extend-slot-hide-row {
      display: flex;
      flex-wrap: wrap;
      margin-top: 5px;
    }
    .easyuse-anima-extend-slot-row button {
      box-sizing: border-box;
      min-width: 0;
      height: 24px;
      border: 1px solid rgba(148, 163, 184, 0.38);
      border-radius: 4px;
      background: rgba(17, 24, 39, 0.7);
      color: var(--fg-color, #ddd);
      font: 11px sans-serif;
      cursor: pointer;
    }
    .easyuse-anima-extend-slot-row button:hover:not(:disabled) {
      border-color: rgba(96, 165, 250, 0.74);
      background: rgba(30, 64, 175, 0.5);
    }
    .easyuse-anima-extend-slot-row button:disabled {
      opacity: 0.42;
      cursor: default;
    }
    .easyuse-anima-extend-slot-hide-row button {
      flex: 0 1 auto;
      height: 21px;
      padding: 0 6px;
      font-size: 10px;
    }
  `;
  document.head.append(style);
}

export {
  ensureAdvancedStyle,
  ensureExtendSlotStyle,
};
