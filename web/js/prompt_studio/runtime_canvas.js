function markNodeDirty(app, node) {
  node?.setDirtyCanvas?.(true, true);
  app.graph?.setDirtyCanvas?.(true, true);
}

function refreshNodeSize(app, node, options = {}) {
  const update = () => {
    const size = node.computeSize();
    const width = Math.max(size[0], node.size?.[0] || size[0]);
    const height = Math.max(size[1], 80);
    if (
      Math.abs(width - (node.size?.[0] || 0)) > 1
      || Math.abs(height - (node.size?.[1] || 0)) > 1
    ) {
      node.setSize?.([width, height]);
    }
    app.graph.setDirtyCanvas(true, true);
  };
  if (options.immediate) {
    update();
  } else {
    requestAnimationFrame(update);
  }
}

function markCanvasDirty(app) {
  app.graph?.setDirtyCanvas(true, true);
  app.canvas?.setDirty?.(true, true);
}

function markGraphDirty(app) {
  app.graph?.setDirtyCanvas?.(true, true);
}

export {
  markCanvasDirty,
  markGraphDirty,
  markNodeDirty,
  refreshNodeSize,
};
