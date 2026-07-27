from __future__ import annotations

import unittest

from easyuse_anima.aio.generation_lifecycle import (
    EphemeralModelRegistry,
    ModelVariantResolver,
    ModelVariantRuntime,
    PreviewCollector,
    PreviewRuntime,
    StageModelPatchPlan,
    StageModelVariantResolver,
    StageModelVariantRuntime,
)


class AIOGenerationLifecycleTests(unittest.TestCase):
    def test_registry_closes_four_slots_in_order_once_and_deduplicates_identity(self):
        base_model = object()
        sample_model = object()
        shared_model = object()
        lora_model = object()
        calls: list[tuple[object, object | None]] = []
        registry = EphemeralModelRegistry(
            base_model=base_model,
            cleanup_model=lambda model, base: calls.append((model, base)),
            base_sample_model=sample_model,
            mod_guidance_model=shared_model,
            model=shared_model,
            model_with_lora=lora_model,
        )

        registry.close()
        registry.close()

        self.assertEqual(
            calls,
            [
                (sample_model, base_model),
                (shared_model, base_model),
                (lora_model, base_model),
            ],
        )

    def test_registry_skips_none_and_propagates_cleanup_failure_once(self):
        base_model = object()
        sample_model = object()
        calls: list[object] = []

        def cleanup(model, _base):
            calls.append(model)
            raise RuntimeError("cleanup failed")

        registry = EphemeralModelRegistry(
            base_model=base_model,
            cleanup_model=cleanup,
            base_sample_model=sample_model,
            mod_guidance_model=None,
            model=object(),
            model_with_lora=None,
        )

        with self.assertRaisesRegex(RuntimeError, "cleanup failed"):
            registry.close()
        registry.close()
        self.assertEqual(calls, [sample_model])

    def test_resolver_preserves_lazy_standalone_and_backend_flag_selection(self):
        base_model = object()
        model = object()
        standalone_model = object()
        lora_model = object()
        calls: list[tuple[object, ...]] = []

        def apply_standalone(*args):
            calls.append(args)
            return standalone_model

        registry = EphemeralModelRegistry(
            base_model=base_model,
            cleanup_model=lambda *_args: None,
            model=model,
            model_with_lora=lora_model,
        )
        resolver = ModelVariantResolver(
            runtime=ModelVariantRuntime(
                apply_standalone_mod_guidance=apply_standalone,
                apply_comfy_sampler_patches=lambda *_args: self.fail(
                    "backend selection must not apply Comfy patches"
                ),
            ),
            registry=registry,
            model=model,
            clip="clip",
            positive="positive",
            negative="negative",
            quality_tags="quality",
            quality_negative="quality-negative",
            profile="profile",
            use_mod_guidance=True,
            can_apply_standalone_mod_guidance=True,
        )

        self.assertEqual(
            resolver.for_backend("spectrum_mod_guidance_advanced"),
            (model, True),
        )
        self.assertEqual(resolver.for_backend("other"), (standalone_model, False))
        self.assertEqual(
            resolver.for_backend("spectrum_mod_guidance_advanced"),
            (standalone_model, False),
        )
        self.assertIs(resolver.standalone_model(), standalone_model)
        self.assertEqual(
            calls,
            [
                (
                    model,
                    "clip",
                    "positive",
                    "negative",
                    "quality",
                    "quality-negative",
                    "profile",
                ),
            ],
        )
        self.assertIs(registry.mod_guidance_model, standalone_model)

    def test_resolver_disabled_standalone_reuses_model_without_helper_call(self):
        model = object()
        registry = EphemeralModelRegistry(
            base_model=object(),
            cleanup_model=lambda *_args: None,
            model=model,
        )
        resolver = ModelVariantResolver(
            runtime=ModelVariantRuntime(
                apply_standalone_mod_guidance=lambda *_args: self.fail(
                    "disabled standalone Mod Guidance must remain lazy"
                ),
                apply_comfy_sampler_patches=lambda *_args: self.fail(
                    "non-Comfy backend must not apply Comfy patches"
                ),
            ),
            registry=registry,
            model=model,
            clip=object(),
            positive=object(),
            negative=object(),
            quality_tags="",
            quality_negative="",
            profile="off",
            use_mod_guidance=False,
            can_apply_standalone_mod_guidance=False,
        )

        self.assertEqual(resolver.for_backend("other"), (model, False))
        self.assertIs(resolver.mod_guidance_model, model)

    def test_first_pass_comfy_patch_updates_cleanup_slot_after_selection(self):
        model = object()
        sample_model = object()
        sampler = {"steps": 28}
        calls: list[tuple[object, object, object, dict[str, object]]] = []

        def apply_comfy(source_model, clip, positive, settings):
            calls.append((source_model, clip, positive, settings))
            return sample_model

        registry = EphemeralModelRegistry(
            base_model=object(),
            cleanup_model=lambda *_args: None,
            model=model,
        )
        resolver = ModelVariantResolver(
            runtime=ModelVariantRuntime(
                apply_standalone_mod_guidance=lambda source, *_args: source,
                apply_comfy_sampler_patches=apply_comfy,
            ),
            registry=registry,
            model=model,
            clip="clip",
            positive="positive",
            negative="negative",
            quality_tags="",
            quality_negative="",
            profile="off",
            use_mod_guidance=False,
            can_apply_standalone_mod_guidance=False,
        )

        self.assertEqual(
            resolver.prepare_first_pass("comfy_ksampler", sampler),
            (sample_model, False),
        )
        self.assertEqual(calls, [(model, "clip", "positive", sampler)])
        self.assertIs(registry.base_sample_model, sample_model)

    def test_stage_resolver_reuses_signature_isolates_variants_and_cleans_once(self):
        base_model = object()
        lora_model = object()
        dave_model = object()
        clean_model = object()
        cleanup_calls: list[object] = []
        apply_calls: list[tuple[object, str]] = []
        signatures = {
            "first_pass": ("dave", ("aura_flow", "dave")),
            "highres": ("dave", ("aura_flow", "dave")),
            "detailer": ("clean", ("aura_flow",)),
            "upscale": ("clean", ("aura_flow",)),
        }

        def build_plan(_settings, stage_id):
            signature, patch_ids = signatures[stage_id]
            return StageModelPatchPlan(signature, patch_ids, signature)

        def apply_plan(model, plan):
            apply_calls.append((model, plan.signature))
            return dave_model if plan.signature == "dave" else clean_model

        registry = EphemeralModelRegistry(
            base_model=base_model,
            cleanup_model=lambda model, _base: cleanup_calls.append(model),
            model_with_lora=lora_model,
        )
        resolver = StageModelVariantResolver(
            runtime=StageModelVariantRuntime(build_plan, apply_plan),
            registry=registry,
            model_with_lora=lora_model,
            settings={},
        )

        self.assertIs(resolver.resolve("first_pass"), dave_model)
        self.assertIs(resolver.resolve("highres"), dave_model)
        self.assertIs(resolver.resolve("detailer"), clean_model)
        self.assertIs(resolver.resolve("upscale"), clean_model)
        self.assertEqual(
            apply_calls,
            [(lora_model, "dave"), (lora_model, "clean")],
        )
        self.assertEqual(resolver.patch_ids("highres"), ("aura_flow", "dave"))
        self.assertEqual(resolver.patch_ids("save"), ())

        registry.close()
        registry.close()
        self.assertEqual(cleanup_calls, [dave_model, clean_model, lora_model])

    def test_stage_resolver_fails_closed_after_limit_or_registry_disposal(self):
        lora_model = object()
        applied: list[str] = []

        def build_plan(_settings, stage_id):
            return StageModelPatchPlan(stage_id, (stage_id,), stage_id)

        def apply_plan(_model, plan):
            applied.append(plan.signature)
            return object()

        registry = EphemeralModelRegistry(
            base_model=object(),
            cleanup_model=lambda *_args: None,
            model_with_lora=lora_model,
        )
        resolver = StageModelVariantResolver(
            runtime=StageModelVariantRuntime(build_plan, apply_plan),
            registry=registry,
            model_with_lora=lora_model,
            settings={},
            max_variants=1,
        )
        resolver.resolve("first_pass")
        with self.assertRaisesRegex(RuntimeError, "variant limit exceeded"):
            resolver.resolve("highres")
        self.assertEqual(applied, ["first_pass"])

        registry.close()
        with self.assertRaisesRegex(RuntimeError, "registry is already closed"):
            resolver.resolve("first_pass")
        self.assertEqual(applied, ["first_pass"])

    def test_stage_resolver_apply_failure_leaves_registry_cleanup_bounded(self):
        base_model = object()
        lora_model = object()
        cleanup_calls: list[object] = []
        registry = EphemeralModelRegistry(
            base_model=base_model,
            cleanup_model=lambda model, _base: cleanup_calls.append(model),
            model_with_lora=lora_model,
        )
        resolver = StageModelVariantResolver(
            runtime=StageModelVariantRuntime(
                lambda _settings, _stage: StageModelPatchPlan(
                    "broken",
                    ("dave",),
                    None,
                ),
                lambda _model, _plan: (_ for _ in ()).throw(
                    RuntimeError("patch failed")
                ),
            ),
            registry=registry,
            model_with_lora=lora_model,
            settings={},
        )

        with self.assertRaisesRegex(RuntimeError, "patch failed"):
            resolver.resolve("first_pass")
        registry.close()
        self.assertEqual(cleanup_calls, [lora_model])

    def test_preview_collector_preserves_save_append_send_and_empty_noop(self):
        previews: list[dict[str, object]] = []
        trace: list[str] = []
        images = [{"filename": "first.webp", "stage": "first_pass"}]

        def save(image, stage, **kwargs):
            trace.append("save")
            self.assertEqual((image, stage), ("image", "first_pass"))
            self.assertEqual(kwargs, {
                "workflow_prompt": {"workflow": True},
                "extra_pnginfo": {"pnginfo": True},
            })
            return images

        def send(node_id, run_id, stage, sent_images):
            trace.append("send")
            self.assertEqual((node_id, run_id, stage), ("node-1", "run-1", "first_pass"))
            self.assertIs(sent_images, images)
            self.assertEqual(previews, images)

        collector = PreviewCollector(
            runtime=PreviewRuntime(
                save_temp_preview=save,
                send_preview_event=send,
            ),
            previews=previews,
            node_id="node-1",
            run_id="run-1",
            workflow_prompt={"workflow": True},
            extra_pnginfo={"pnginfo": True},
        )

        collector.add("first_pass", "image")
        self.assertEqual(trace, ["save", "send"])
        self.assertEqual(previews, images)

        empty_collector = PreviewCollector(
            runtime=PreviewRuntime(
                save_temp_preview=lambda *_args, **_kwargs: [],
                send_preview_event=lambda *_args: self.fail(
                    "empty preview must not send an event"
                ),
            ),
            previews=previews,
            node_id="node-1",
            run_id="run-1",
            workflow_prompt={"workflow": True},
            extra_pnginfo={"pnginfo": True},
        )
        empty_collector.add("highres", "image")
        self.assertEqual(previews, images)

    def test_preview_collector_propagates_save_before_append_and_send_after_append(self):
        previews: list[dict[str, object]] = []
        collector = PreviewCollector(
            runtime=PreviewRuntime(
                save_temp_preview=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                    RuntimeError("save failed")
                ),
                send_preview_event=lambda *_args: None,
            ),
            previews=previews,
            node_id="node",
            run_id="run",
            workflow_prompt=None,
            extra_pnginfo=None,
        )

        with self.assertRaisesRegex(RuntimeError, "save failed"):
            collector.add("first_pass", "image")
        self.assertEqual(previews, [])

        images = [{"filename": "preview.webp"}]
        send_failure_collector = PreviewCollector(
            runtime=PreviewRuntime(
                save_temp_preview=lambda *_args, **_kwargs: images,
                send_preview_event=lambda *_args: (_ for _ in ()).throw(
                    RuntimeError("send failed")
                ),
            ),
            previews=previews,
            node_id="node",
            run_id="run",
            workflow_prompt=None,
            extra_pnginfo=None,
        )
        with self.assertRaisesRegex(RuntimeError, "send failed"):
            send_failure_collector.add("first_pass", "image")
        self.assertEqual(previews, images)


if __name__ == "__main__":
    unittest.main()
