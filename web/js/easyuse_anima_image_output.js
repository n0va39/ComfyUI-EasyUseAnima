// @ts-check
// @ts-expect-error ComfyUI provides this host module at runtime.
import { app } from "../../../scripts/app.js";
import { migrateImageOutputWorkflow } from "./image_output/workflow_migration.js";

app.registerExtension({
  name: "EasyUseAnima.ImageOutput",
  beforeConfigureGraph: migrateImageOutputWorkflow,
});
