// @ts-check

function editableSeed(value, maximum) {
  const text = String(value ?? "").trim();
  if (!/^\d+$/.test(text)) {
    return null;
  }
  try {
    const parsed = BigInt(text);
    if (parsed > BigInt(maximum)) {
      return null;
    }
    return Number(parsed);
  } catch {
    return null;
  }
}

/**
 * Publish backend-accepted AiO seed state without owning queue preparation.
 *
 * The backend sends decimal strings so uint64 compatibility values are not
 * silently rounded by JSON. Values outside the editable browser domain stay
 * authoritative in the backend result/metadata and are not written into the
 * smaller number widget.
 *
 * @param {any} node
 * @param {any} message
 * @param {{maximum: number, updateSeed: (node: any, seed: number, options: {markDirty: boolean}) => any}} dependencies
 */
export function aioApplyExecutedSeedDisplay(node, message, dependencies) {
  const payload = Array.isArray(message?.easyuse_anima_aio_seed)
    ? message.easyuse_anima_aio_seed[0]
    : null;
  if (!node || !payload || typeof payload !== "object") {
    return false;
  }

  const executionSeed = editableSeed(payload.execution_seed, dependencies.maximum);
  const nextSeed = editableSeed(payload.next_seed, dependencies.maximum);
  let applied = false;
  if (executionSeed != null) {
    node.__easyuseAnimaLastExecutedSeed = executionSeed;
    applied = true;
  }
  if (nextSeed != null) {
    try {
      dependencies.updateSeed(node, nextSeed, { markDirty: false });
      applied = true;
    } catch {
      // Backend acceptance remains authoritative when a stale panel cannot
      // publish the accepted next-run value.
    }
  }
  return applied;
}
