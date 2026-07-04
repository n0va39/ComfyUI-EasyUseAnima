import { app } from "../../../scripts/app.js";
import {
  createPromptStudioExtensionRuntime,
} from "./prompt_studio/extension_runtime.js";

app.registerExtension({
  name: "easyuse-anima.prompt-studio",
  ...createPromptStudioExtensionRuntime(app),
});
