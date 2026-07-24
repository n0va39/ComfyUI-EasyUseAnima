// @ts-check

import {
  ADVANCED_RESOLUTION_BUCKETS,
  CUSTOM_ADVANCED_RESOLUTION_BUCKET,
  NAIA_ADVANCED_RESOLUTION_BUCKET,
} from "./constants.js";
import {
  advancedResolutionLabel,
  snapResolution32,
} from "./utils.js";

const ADVANCED_RESOLUTION_ORIENTATION_REASONS = Object.freeze({
  ready: "ready",
  linked: "linked",
  naia: "naia",
  square: "square",
  missingInverse: "missing-inverse",
});

function advancedResolutionDimensions(value) {
  const match = String(value || "").match(/(\d+)\s*(?:\*|x|×)\s*(\d+)/);
  if (!match) {
    return null;
  }
  return {
    width: Number(match[1]),
    height: Number(match[2]),
  };
}

function disabledAdvancedResolutionOrientation(reason, values = {}) {
  return {
    enabled: false,
    reason,
    nextSize: null,
    nextWidth: null,
    nextHeight: null,
    ...values,
  };
}

function advancedResolutionOrientationPlan({
  bucket,
  size,
  width,
  height,
  linked = false,
  buckets = ADVANCED_RESOLUTION_BUCKETS,
}) {
  if (linked) {
    return disabledAdvancedResolutionOrientation(
      ADVANCED_RESOLUTION_ORIENTATION_REASONS.linked,
    );
  }
  if (bucket === NAIA_ADVANCED_RESOLUTION_BUCKET) {
    return disabledAdvancedResolutionOrientation(
      ADVANCED_RESOLUTION_ORIENTATION_REASONS.naia,
    );
  }
  if (bucket === CUSTOM_ADVANCED_RESOLUTION_BUCKET) {
    const currentWidth = snapResolution32(width, 1024);
    const currentHeight = snapResolution32(height, 1024);
    if (currentWidth === currentHeight) {
      return disabledAdvancedResolutionOrientation(
        ADVANCED_RESOLUTION_ORIENTATION_REASONS.square,
        { width: currentWidth, height: currentHeight },
      );
    }
    return {
      enabled: true,
      reason: ADVANCED_RESOLUTION_ORIENTATION_REASONS.ready,
      width: currentWidth,
      height: currentHeight,
      nextSize: advancedResolutionLabel(currentHeight, currentWidth),
      nextWidth: currentHeight,
      nextHeight: currentWidth,
    };
  }

  const current = advancedResolutionDimensions(size);
  if (!current) {
    return disabledAdvancedResolutionOrientation(
      ADVANCED_RESOLUTION_ORIENTATION_REASONS.missingInverse,
    );
  }
  if (current.width === current.height) {
    return disabledAdvancedResolutionOrientation(
      ADVANCED_RESOLUTION_ORIENTATION_REASONS.square,
      current,
    );
  }
  const inverse = (buckets?.[bucket] || []).find(
    ([candidateWidth, candidateHeight]) => (
      candidateWidth === current.height && candidateHeight === current.width
    ),
  );
  if (!inverse) {
    return disabledAdvancedResolutionOrientation(
      ADVANCED_RESOLUTION_ORIENTATION_REASONS.missingInverse,
      current,
    );
  }
  return {
    enabled: true,
    reason: ADVANCED_RESOLUTION_ORIENTATION_REASONS.ready,
    ...current,
    nextSize: advancedResolutionLabel(inverse[0], inverse[1]),
    nextWidth: inverse[0],
    nextHeight: inverse[1],
  };
}

function advancedResolutionOrientationTitleKey(reason) {
  if (reason === ADVANCED_RESOLUTION_ORIENTATION_REASONS.linked) {
    return "advanced.swapOrientationLinkedTitle";
  }
  if (reason === ADVANCED_RESOLUTION_ORIENTATION_REASONS.naia) {
    return "advanced.swapOrientationNaiaTitle";
  }
  if (reason === ADVANCED_RESOLUTION_ORIENTATION_REASONS.square) {
    return "advanced.swapOrientationSquareTitle";
  }
  if (reason === ADVANCED_RESOLUTION_ORIENTATION_REASONS.missingInverse) {
    return "advanced.swapOrientationUnavailableTitle";
  }
  return "advanced.swapOrientationTitle";
}

export {
  ADVANCED_RESOLUTION_ORIENTATION_REASONS,
  advancedResolutionDimensions,
  advancedResolutionOrientationPlan,
  advancedResolutionOrientationTitleKey,
};
