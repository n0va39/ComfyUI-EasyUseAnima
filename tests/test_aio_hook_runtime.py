from __future__ import annotations

import unittest
from dataclasses import dataclass
from types import SimpleNamespace

from easyuse_anima.aio.generation_pipeline import GenerationState
from easyuse_anima.aio.hooks import (
    AioHookRun,
    aio_hook_change_token,
    prepare_aio_hook,
    run_aio_postprocess_hook_stage,
)
from easyuse_anima.aio.hooks.contracts import (
    AioHookDescriptor as InternalAioHookDescriptor,
)
from easyuse_anima.extensions.aio import (
    AIO_HOOK_API_VERSION,
    EASYUSE_ANIMA_AIO_HOOK_TYPE,
    AioHookContractError,
    AioHookDescriptor,
    AioHookExecutionError,
    AioHookPatch,
    AioHookPoint,
    AioHookSessionBase,
    AioStage,
    AioStagePhase,
    combine_aio_hooks,
)
from easyuse_anima.nodes.aio_hook_nodes import EasyUseAnimaAIOHookCombine

POSTPROCESS_POINTS = frozenset({
    AioHookPoint(AioStage.POSTPROCESS, AioStagePhase.BEFORE),
    AioHookPoint(AioStage.POSTPROCESS, AioStagePhase.AFTER),
})


@dataclass(frozen=True)
class _Image:
    name: str
    shape: tuple[int, ...] = (1, 32, 32, 3)


class _Config:
    mode = "txt2img"

    def to_dict(self):
        return {"mode": self.mode, "sampler": {"seed": 17}}


class _Stage:
    name = "postprocess"

    def __init__(self, log, error=None):
        self.log = log
        self.error = error

    def validate(self, request, capabilities):
        del request
        self.log.append(("validate", capabilities))

    def run(self, request, state):
        del request
        self.log.append(("stage", state.image.name))
        if self.error is not None:
            raise self.error
        state.image = _Image("core")


class _Session(AioHookSessionBase):
    def __init__(self, hook_id, log, services, patch_image=True):
        self.hook_id = hook_id
        self.log = log
        self.services = services
        self.patch_image = patch_image

    def before_stage(self, event):
        self.log.append(("before", self.hook_id, event.state.image.name))
        return AioHookPatch(metadata={"before": self.hook_id})

    def after_stage(self, event):
        self.log.append(("after", self.hook_id, event.state.image.name))
        self.services.emit_preview(
            event.stage,
            event.state.image,
            f"{self.hook_id}/preview",
        )
        return AioHookPatch(
            image=(
                _Image(f"{self.hook_id}-after")
                if self.patch_image
                else event.state.image
            ),
            metadata={"after": self.hook_id},
        )

    def close(self):
        self.log.append(("close", self.hook_id))


class _Definition:
    def __init__(
        self,
        hook_id,
        log,
        *,
        fingerprint=1,
        points=POSTPROCESS_POINTS,
        api_version=AIO_HOOK_API_VERSION,
        patch_image=True,
    ):
        self.hook_id = hook_id
        self.log = log
        self.fingerprint = fingerprint
        self.points = points
        self.api_version = api_version
        self.patch_image = patch_image

    def describe(self):
        return AioHookDescriptor(
            hook_id=self.hook_id,
            hook_version="1.0.0",
            points=self.points,
            api_version=self.api_version,
            fingerprint=self.fingerprint,
        )

    def create_session(self, context):
        self.log.append(("create", self.hook_id, context.request.node_id))
        context.services.register_cleanup(
            lambda: self.log.append(("cleanup", self.hook_id))
        )
        return _Session(
            self.hook_id,
            self.log,
            context.services,
            patch_image=self.patch_image,
        )


def _request():
    return SimpleNamespace(
        config=_Config(),
        workflow=SimpleNamespace(unique_id=23),
    )


class AioHookRuntimeTests(unittest.TestCase):
    def test_public_contract_and_combine_node_preserve_socket_order(self):
        self.assertIs(AioHookDescriptor, InternalAioHookDescriptor)
        log = []
        first = _Definition("example.first", log)
        second = _Definition("example.second", log)
        chain = combine_aio_hooks(first, None, combine_aio_hooks(second))

        self.assertEqual(AIO_HOOK_API_VERSION, 1)
        self.assertEqual(EASYUSE_ANIMA_AIO_HOOK_TYPE, "EASYUSE_ANIMA_AIO_HOOK")
        self.assertEqual(list(AioStage), [AioStage.POSTPROCESS])
        self.assertEqual(chain.definitions, (first, second))
        input_types = EasyUseAnimaAIOHookCombine.INPUT_TYPES()
        self.assertEqual(list(input_types["required"]), ["hook_a", "hook_b"])
        self.assertEqual(list(input_types["optional"]), ["hook_c", "hook_d"])
        self.assertEqual(
            EasyUseAnimaAIOHookCombine.RETURN_TYPES,
            (EASYUSE_ANIMA_AIO_HOOK_TYPE,),
        )
        self.assertEqual(
            EasyUseAnimaAIOHookCombine().combine(first, second)[0].definitions,
            (first, second),
        )

    def test_chain_uses_middleware_order_and_namespaced_metadata(self):
        log = []
        previews = []
        state = GenerationState(None, _Image("input"), 32, 32)
        state.extensions["existing"] = {"preserved": True}
        hook = combine_aio_hooks(
            _Definition("example.first", log),
            _Definition("example.second", log),
        )

        run_aio_postprocess_hook_stage(
            prepare_aio_hook(hook),
            _request(),
            state,
            "run-id",
            lambda label, image: previews.append((label, image.name)),
            _Stage(log),
        )

        self.assertEqual(
            log,
            [
                ("create", "example.first", "23"),
                ("create", "example.second", "23"),
                ("validate", {}),
                ("before", "example.first", "input"),
                ("before", "example.second", "input"),
                ("stage", "input"),
                ("after", "example.second", "core"),
                ("after", "example.first", "example.second-after"),
                ("close", "example.second"),
                ("close", "example.first"),
                ("cleanup", "example.second"),
                ("cleanup", "example.first"),
            ],
        )
        self.assertEqual(state.image.name, "example.first-after")
        self.assertEqual(
            previews,
            [
                ("hook_postprocess_example.second_example.second_preview", "core"),
                (
                    "hook_postprocess_example.first_example.first_preview",
                    "example.second-after",
                ),
            ],
        )
        self.assertEqual(
            state.extensions["hook_data"]["example.first#0"],
            {"before": "example.first", "after": "example.first"},
        )
        self.assertEqual(
            [item["hook_id"] for item in state.extensions["hooks"]],
            ["example.first", "example.second"],
        )
        self.assertEqual(state.extensions["existing"], {"preserved": True})

    def test_stage_error_preserves_original_and_cleans_up_in_reverse(self):
        log = []
        state = GenerationState(None, _Image("input"), 32, 32)
        prepared = prepare_aio_hook(combine_aio_hooks(
            _Definition("example.first", log),
            _Definition("example.second", log),
        ))

        with self.assertRaisesRegex(ValueError, "core failed"):
            run_aio_postprocess_hook_stage(
                prepared,
                _request(),
                state,
                "run-id",
                None,
                _Stage(log, ValueError("core failed")),
            )

        self.assertEqual(
            log[-4:],
            [
                ("close", "example.second"),
                ("close", "example.first"),
                ("cleanup", "example.second"),
                ("cleanup", "example.first"),
            ],
        )

    def test_contract_validation_is_fail_closed_before_session_creation(self):
        log = []
        with self.assertRaisesRegex(AioHookContractError, "points must not be empty"):
            prepare_aio_hook(_Definition("example.empty", log, points=frozenset()))
        with self.assertRaisesRegex(AioHookContractError, "AioHookPoint"):
            prepare_aio_hook(_Definition("example.bad-point", log, points={"bad"}))
        with self.assertRaisesRegex(AioHookContractError, "hook_id"):
            prepare_aio_hook(_Definition("example/bad", log))
        with self.assertRaisesRegex(AioHookContractError, "supports v1"):
            prepare_aio_hook(_Definition("example.v2", log, api_version=2))
        duplicate = _Definition("example.duplicate", log)
        with self.assertRaisesRegex(AioHookContractError, "more than once"):
            prepare_aio_hook(combine_aio_hooks(duplicate, duplicate))
        self.assertEqual(log, [])

    def test_fingerprint_is_copied_canonical_and_none_disables_cache(self):
        fingerprint = {"nested": [1], "strength": 0.5}
        definition = _Definition("example.stable", [], fingerprint=fingerprint)
        prepared = prepare_aio_hook(definition)
        fingerprint["nested"].append(2)

        self.assertEqual(prepared[0].fingerprint, {"nested": [1], "strength": 0.5})
        stable, token = aio_hook_change_token(
            _Definition(
                "example.canonical",
                [],
                fingerprint={"z": 1, "a": {"b": 2}},
            )
        )
        unstable, unstable_token = aio_hook_change_token(
            _Definition("example.unstable", [], fingerprint=None)
        )
        self.assertTrue(stable)
        self.assertEqual(token[0]["fingerprint"], {"z": 1, "a": {"b": 2}})
        self.assertEqual(
            token[0]["points"],
            [
                {"stage": "postprocess", "phase": "after"},
                {"stage": "postprocess", "phase": "before"},
            ],
        )
        self.assertFalse(unstable)
        self.assertIsNone(unstable_token)

    def test_shape_change_is_rejected_and_cleanup_runs(self):
        class InvalidSession(_Session):
            def after_stage(self, event):
                del event
                return AioHookPatch(image=_Image("wrong", (1, 16, 16, 3)))

        class InvalidDefinition(_Definition):
            def create_session(self, context):
                context.services.register_cleanup(
                    lambda: self.log.append(("cleanup", self.hook_id))
                )
                return InvalidSession(self.hook_id, self.log, context.services)

        log = []
        state = GenerationState(None, _Image("input"), 32, 32)
        with self.assertRaisesRegex(AioHookContractError, "must preserve shape"):
            with AioHookRun(
                prepare_aio_hook(InvalidDefinition("example.invalid", log)),
                _request(),
                state,
                "run-id",
                None,
            ) as hook_run:
                hook_run.run_stage(_Stage(log), _request(), state, {})
        self.assertEqual(
            log[-2:],
            [("close", "example.invalid"), ("cleanup", "example.invalid")],
        )

    def test_duplicate_metadata_key_is_rejected(self):
        class DuplicateSession(AioHookSessionBase):
            def before_stage(self, event):
                del event
                return AioHookPatch(metadata={"same": 1})

            def after_stage(self, event):
                del event
                return AioHookPatch(metadata={"same": 2})

        class DuplicateDefinition(_Definition):
            def create_session(self, context):
                del context
                return DuplicateSession()

        state = GenerationState(None, _Image("input"), 32, 32)
        with self.assertRaisesRegex(AioHookContractError, "repeated metadata keys: same"):
            run_aio_postprocess_hook_stage(
                prepare_aio_hook(DuplicateDefinition("example.duplicate-key", [])),
                _request(),
                state,
                "run-id",
                None,
                _Stage([]),
            )

    def test_partial_session_creation_failure_cleans_every_registered_resource(self):
        class FailingDefinition(_Definition):
            def create_session(self, context):
                self.log.append(("create", self.hook_id, context.request.node_id))
                context.services.register_cleanup(
                    lambda: self.log.append(("cleanup", self.hook_id))
                )
                raise ValueError("creation failed")

        log = []
        state = GenerationState(None, _Image("input"), 32, 32)
        prepared = prepare_aio_hook(combine_aio_hooks(
            _Definition("example.first", log),
            FailingDefinition("example.failing", log),
        ))
        with self.assertRaisesRegex(AioHookExecutionError, "session creation"):
            with AioHookRun(prepared, _request(), state, "run-id", None):
                self.fail("session creation must fail")
        self.assertEqual(
            log[-3:],
            [
                ("close", "example.first"),
                ("cleanup", "example.failing"),
                ("cleanup", "example.first"),
            ],
        )

    def test_interrupt_is_not_wrapped_but_cleanup_still_runs(self):
        class InterruptSession(_Session):
            def after_stage(self, event):
                del event
                raise KeyboardInterrupt()

        class InterruptDefinition(_Definition):
            def create_session(self, context):
                context.services.register_cleanup(
                    lambda: self.log.append(("cleanup", self.hook_id))
                )
                return InterruptSession(self.hook_id, self.log, context.services)

        log = []
        state = GenerationState(None, _Image("input"), 32, 32)
        with self.assertRaises(KeyboardInterrupt):
            run_aio_postprocess_hook_stage(
                prepare_aio_hook(InterruptDefinition("example.interrupt", log)),
                _request(),
                state,
                "run-id",
                None,
                _Stage(log),
            )
        self.assertEqual(
            log[-2:],
            [("close", "example.interrupt"), ("cleanup", "example.interrupt")],
        )

    def test_empty_hook_preserves_existing_metadata_and_extension_absence(self):
        log = []
        state = GenerationState(
            None,
            _Image("input"),
            32,
            32,
            metadata={"core": {"value": 1}},
        )
        run_aio_postprocess_hook_stage(
            prepare_aio_hook(None),
            _request(),
            state,
            "run-id",
            None,
            _Stage(log),
        )
        self.assertEqual(state.metadata, {"core": {"value": 1}})
        self.assertEqual(state.extensions, {})
        self.assertEqual(state.image.name, "core")


if __name__ == "__main__":
    unittest.main()
