// @ts-check

const dependencyControlState = new WeakMap();

/**
 * Keep a dependency-gated primary control interactive so an explicit user
 * attempt can be explained, while visually marking it as unavailable.
 * Dependent detail controls should still use their native disabled state.
 *
 * @param {any} control
 * @param {boolean} missing
 * @param {string} message
 */
export function aioMarkMissingDependencyControl(control, missing, message = "") {
  if (!control) {
    return;
  }
  const row = control.parentElement || null;
  if (!dependencyControlState.has(control)) {
    dependencyControlState.set(control, {
      controlTitle: control.title || "",
      rowTitle: row?.title || "",
    });
  }
  const original = dependencyControlState.get(control);
  control.disabled = false;
  if (typeof control.setAttribute === "function") {
    control.setAttribute("aria-disabled", missing ? "true" : "false");
  }
  row?.classList?.toggle("easyuse-anima-aio-unsupported", missing);
  control.title = missing ? message : original.controlTitle;
  if (row) {
    row.title = missing ? message : original.rowTitle;
  }
}
