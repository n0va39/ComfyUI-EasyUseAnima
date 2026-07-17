// @ts-check

/**
 * @typedef {Object} ComfyGraphLike
 * @property {(dirtyCanvas?: boolean, dirtyBgCanvas?: boolean) => void} [setDirtyCanvas]
 * @property {Array<ComfyNodeLike>} [_nodes]
 */

/**
 * @typedef {Object} ComfyCanvasLike
 * @property {(foreground?: boolean, background?: boolean) => void} [setDirty]
 */

/**
 * @typedef {Object} ComfyAppLike
 * @property {ComfyGraphLike} graph
 * @property {ComfyCanvasLike} [canvas]
 */

/**
 * @typedef {Object} ComfyWidgetLike
 * @property {string} [name]
 * @property {unknown} [value]
 * @property {HTMLElement | null} [inputEl]
 * @property {(width?: number) => [number, number]} [computeSize]
 * @property {(value?: unknown) => unknown} [callback]
 * @property {boolean} [hidden]
 * @property {boolean} [serialize]
 * @property {{ hidden?: boolean }} [options]
 */

/**
 * @typedef {(HTMLTextAreaElement | HTMLInputElement) & {
 *   __easyuseAnimaHighlightOverlay?: HTMLElement | null,
 *   __easyuseAnimaHighlightRefresh?: (force?: boolean) => void,
 *   __easyuseAnimaExternalAutocompleteDispose?: () => void,
 *   __easyuseAnimaStudioResizable?: boolean
 * }} PromptStudioInputElement
 */

/**
 * @typedef {HTMLTextAreaElement & PromptStudioInputElement & {
 *   __easyuseAnimaNode?: unknown,
 *   __easyuseAnimaField?: unknown
 * }} PromptStudioAdvancedTextarea
 */

/**
 * @typedef {Object} PromptStudioAutocompleteTooltip
 * @property {string} [tag]
 * @property {string} [meta]
 * @property {string} [description]
 */

/**
 * @typedef {Window & typeof globalThis & {
 *   __easyuseAnimaHighlightOverlayRefreshInstalled?: boolean,
 *   __easyuseAnimaMiddlePanForwarderInstalled?: boolean,
 *   __easyuseAnimaWheelForwarderInstalled?: boolean,
 *   __easyuseAnimaPendingAutocompleteInputs?: Array<{
 *     input: Element,
 *     options: unknown,
 *     onBound?: (dispose: (() => void) | null) => void
 *   }>,
 *   easyuseAnimaAutocompleteEntryTooltip?: (entry: unknown) => PromptStudioAutocompleteTooltip | null | undefined,
 *   easyuseAnimaHookAutocompleteInput?: (input: Element, options: unknown) => (() => void) | null
 * }} PromptStudioWindow
 */

/**
 * @typedef {Object} ComfyNodeLike
 * @property {[number, number]} [size]
 * @property {Array<ComfyWidgetLike>} [widgets]
 * @property {Array<unknown>} [inputs]
 * @property {() => [number, number]} computeSize
 * @property {(size: [number, number]) => void} [setSize]
 * @property {(dirtyCanvas?: boolean, dirtyBgCanvas?: boolean) => void} [setDirtyCanvas]
 */

/**
 * @typedef {"auto" | "manual"} PromptStudioFieldHeightMode
 */

/**
 * @typedef {Object} PromptStudioField
 * @property {string} id
 * @property {string} type
 * @property {string} name
 * @property {string} value
 * @property {PromptStudioFieldHeightMode} [heightMode]
 * @property {number} [height]
 */

/**
 * @typedef {Object} PromptStudioState
 * @property {Array<PromptStudioField>} [fields]
 */

/**
 * @typedef {ComfyNodeLike & {
 *   __easyuseAnimaAdvancedHookScheduled?: boolean,
 *   __easyuseAnimaAdvancedDomWidget?: ComfyWidgetLike
 * }} AdvancedEditorNode
 */

/**
 * @typedef {Object} PromptClassificationResult
 * @property {string} text
 * @property {string} [section]
 * @property {number} [start]
 * @property {number} [end]
 */

/**
 * @typedef {Object<string, unknown>} EasyUseAnimaSettings
 */

/**
 * @typedef {Object} ApiJsonResponse
 * @property {boolean} [ok]
 * @property {unknown} [data]
 * @property {string} [error]
 */

/**
 * @typedef {Object} LayoutMeasureResult
 * @property {number} width
 * @property {number} height
 * @property {number} [minWidth]
 * @property {number} [minHeight]
 */

/**
 * @typedef {Object} ResizeFinalizeState
 * @property {number} [width]
 * @property {number} [height]
 * @property {number} [timestamp]
 */

export {};
