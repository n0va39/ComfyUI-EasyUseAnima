// @ts-check

const TEXTAREA_FIT_TOLERANCE = 2;
const TEXTAREA_STABILIZATION_FRAMES = 2;

/**
 * Schedule a small revision-owned post-input grow pass. Height calculation,
 * persistence, and node layout remain owned by the caller.
 *
 * @param {HTMLTextAreaElement | HTMLInputElement} textarea
 * @param {() => boolean} growToContent
 * @param {{
 *   frameBudget?: number,
 *   requestFrame?: (callback: FrameRequestCallback) => number,
 *   tolerance?: number,
 * }} [options]
 */
function createTextareaGrowStabilizer(textarea, growToContent, options = {}) {
  const frameBudget = Math.max(
    1,
    Math.round(Number(options.frameBudget) || TEXTAREA_STABILIZATION_FRAMES),
  );
  const tolerance = Math.max(
    0,
    Number(options.tolerance) || TEXTAREA_FIT_TOLERANCE,
  );
  const requestFrame = options.requestFrame
    || ((callback) => globalThis.requestAnimationFrame(callback));
  let revision = 0;

  const schedule = () => {
    revision += 1;
    const ownedRevision = revision;
    let remainingFrames = frameBudget;

    const remeasure = () => {
      if (ownedRevision !== revision || textarea?.isConnected === false) {
        return;
      }
      const grew = growToContent() === true;
      textarea.style.overflowY = "hidden";
      remainingFrames -= 1;
      const fits = Number(textarea.scrollHeight) <= Number(textarea.clientHeight) + tolerance;
      if (remainingFrames > 0 && (grew || !fits)) {
        requestFrame(remeasure);
      }
    };

    requestFrame(remeasure);
    return ownedRevision;
  };

  const invalidate = () => {
    revision += 1;
  };

  return {
    invalidate,
    schedule,
  };
}

export {
  createTextareaGrowStabilizer,
  TEXTAREA_FIT_TOLERANCE,
  TEXTAREA_STABILIZATION_FRAMES,
};
