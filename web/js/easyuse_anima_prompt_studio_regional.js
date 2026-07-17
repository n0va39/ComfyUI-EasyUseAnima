// @ts-check

// @ts-expect-error ComfyUI provides this host module at runtime.
import { app } from "../../../scripts/app.js";
import {
  createPromptStudioActionButton,
  ensurePromptStudioVariantStyle,
  installPromptStudioRegionalAdapter,
  promptStudioFieldIndexLabel,
  promptStudioFieldLabel,
  promptStudioText,
  refreshPromptStudioHighlights,
  registerPromptStudioTextarea,
  requestPromptStudioOverlaySync,
  schedulePromptStudioFieldHighlight,
  updatePromptStudioFieldHighlight,
} from "./prompt_studio/regional/editor_adapter.js";
import {
  createRegionalExtensionRuntime,
} from "./prompt_studio/regional/extension.js";
import {
  createRegionalFieldEditor,
} from "./prompt_studio/regional/field_editor.js";
import {
  createRegionalLayout,
} from "./prompt_studio/regional/layout.js";
import {
  createRegionalMaskEditor,
} from "./prompt_studio/regional/mask_editor.js";
import {
  createRegionalRuntime,
} from "./prompt_studio/regional/runtime.js";

const runtime = createRegionalRuntime(app, {
  fieldLabel: promptStudioFieldLabel,
});
const layout = createRegionalLayout(app, runtime, {
  refreshPromptStudioHighlights,
  requestPromptStudioOverlaySync,
});

let fieldEditor;
const maskEditor = createRegionalMaskEditor(app, runtime, layout, {
  createButton: createPromptStudioActionButton,
  collectRegionalEditorFields: (node) => fieldEditor.collectRegionalEditorFields(node),
  renderRegionalEditor: (node) => fieldEditor.renderRegionalEditor(node),
});
fieldEditor = createRegionalFieldEditor(runtime, layout, maskEditor, {
  createPromptStudioActionButton,
  promptStudioFieldIndexLabel,
  promptStudioFieldLabel,
  promptStudioText,
  registerPromptStudioTextarea,
  schedulePromptStudioFieldHighlight,
  updatePromptStudioFieldHighlight,
});

app.registerExtension({
  name: "easyuse-anima.prompt-studio-regional",
  ...createRegionalExtensionRuntime(app, runtime, layout, fieldEditor, {
    ensureRegionalStyle: ensurePromptStudioVariantStyle,
    installRegionalAdapter: installPromptStudioRegionalAdapter,
  }),
});
