// @ts-check

import {
  PROMPT_STUDIO_SETTINGS,
} from "./settings.js";
import {
  ensureTrainedTagTooltipStyle,
} from "./style.js";

let promptStudioTagTooltip = null;
let promptStudioTagTooltipMoveFrame = 0;
let promptStudioTagTooltipPendingMove = null;
let promptStudioTagTooltipLastTarget = null;

function ensureTrainedTagTooltip() {
  ensureTrainedTagTooltipStyle();
  if (promptStudioTagTooltip?.isConnected) {
    return promptStudioTagTooltip;
  }
  promptStudioTagTooltip = document.createElement("div");
  promptStudioTagTooltip.className = "easyuse-anima-trained-tag-tooltip hidden";
  document.body.append(promptStudioTagTooltip);
  return promptStudioTagTooltip;
}

function hideTrainedTagTooltip() {
  promptStudioTagTooltipPendingMove = null;
  promptStudioTagTooltipLastTarget = null;
  if (promptStudioTagTooltip) {
    promptStudioTagTooltip.classList.add("hidden");
  }
}

function visibleAutocompletePopupExists() {
  return !!document.querySelector(".easyuse-anima-autocomplete:not(.hidden)");
}

function trainedTagTooltipTargetAt(overlay, clientX, clientY) {
  if (!overlay?.isConnected) {
    return null;
  }
  const targets = overlay.querySelectorAll("[data-easyuse-anima-trained-tag-tooltip='true']");
  for (const target of targets) {
    for (const rect of target.getClientRects()) {
      if (
        clientX >= rect.left - 1
        && clientX <= rect.right + 1
        && clientY >= rect.top - 1
        && clientY <= rect.bottom + 1
      ) {
        return target;
      }
    }
  }
  return null;
}

function positionTrainedTagTooltip(tooltip, event) {
  const margin = 8;
  const offset = 14;
  const rect = tooltip.getBoundingClientRect();
  const left = Math.min(
    Math.max(margin, event.clientX + offset),
    Math.max(margin, window.innerWidth - rect.width - margin),
  );
  const below = event.clientY + offset;
  const top = below + rect.height + margin <= window.innerHeight
    ? below
    : Math.max(margin, event.clientY - rect.height - offset);
  tooltip.style.left = `${left}px`;
  tooltip.style.top = `${top}px`;
}

function showTrainedTagTooltip(target, event) {
  const tooltip = ensureTrainedTagTooltip();
  if (
    promptStudioTagTooltipLastTarget === target
    && !tooltip.classList.contains("hidden")
  ) {
    positionTrainedTagTooltip(tooltip, event);
    return;
  }
  promptStudioTagTooltipLastTarget = target;
  const tag = target.dataset.easyuseAnimaTooltipTag || "";
  const meta = target.dataset.easyuseAnimaTooltipMeta || "";
  const description = target.dataset.easyuseAnimaTooltipDescription || "";
  tooltip.replaceChildren();

  const top = document.createElement("div");
  const tagEl = document.createElement("span");
  tagEl.className = "easyuse-anima-autocomplete-tag";
  tagEl.textContent = tag;
  top.append(tagEl);
  if (meta) {
    const metaEl = document.createElement("span");
    metaEl.className = "easyuse-anima-autocomplete-meta";
    metaEl.textContent = meta;
    top.append(metaEl);
  }
  tooltip.append(top);
  if (description) {
    const desc = document.createElement("div");
    desc.className = "easyuse-anima-autocomplete-desc";
    desc.textContent = description;
    tooltip.append(desc);
  }

  tooltip.classList.remove("hidden");
  positionTrainedTagTooltip(tooltip, event);
}

function updateTrainedTagTooltipMove(input, clientX, clientY) {
  if (visibleAutocompletePopupExists()) {
    hideTrainedTagTooltip();
    return;
  }
  const target = trainedTagTooltipTargetAt(input?.__easyuseAnimaHighlightOverlay, clientX, clientY);
  if (!target) {
    hideTrainedTagTooltip();
    return;
  }
  showTrainedTagTooltip(target, { clientX, clientY });
}

function handleTrainedTagTooltipMove(input, event) {
  if (!PROMPT_STUDIO_SETTINGS.trainedTagTooltip) {
    hideTrainedTagTooltip();
    return;
  }
  promptStudioTagTooltipPendingMove = {
    input,
    clientX: event.clientX,
    clientY: event.clientY,
  };
  if (promptStudioTagTooltipMoveFrame) {
    return;
  }
  promptStudioTagTooltipMoveFrame = requestAnimationFrame(() => {
    promptStudioTagTooltipMoveFrame = 0;
    const move = promptStudioTagTooltipPendingMove;
    promptStudioTagTooltipPendingMove = null;
    if (!move) {
      return;
    }
    updateTrainedTagTooltipMove(move.input, move.clientX, move.clientY);
  });
}

function installTrainedTagTooltipListeners(input) {
  if (input.__easyuseAnimaTrainedTagTooltipInstalled) {
    return;
  }
  input.addEventListener("mousemove", (event) => handleTrainedTagTooltipMove(input, event));
  input.addEventListener("mouseleave", hideTrainedTagTooltip);
  input.addEventListener("scroll", hideTrainedTagTooltip);
  input.addEventListener("input", hideTrainedTagTooltip);
  input.addEventListener("blur", hideTrainedTagTooltip);
  input.__easyuseAnimaTrainedTagTooltipInstalled = true;
}

export {
  hideTrainedTagTooltip,
  installTrainedTagTooltipListeners,
};
