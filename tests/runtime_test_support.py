from __future__ import annotations

import threading
from contextlib import contextmanager
from unittest.mock import patch


_RUNTIME_TEST_LOCK = threading.RLock()


def build_runtime_services(
    runtime_module,
    *,
    comfy,
    seed_reservations,
    config,
    clock,
    translation,
    autocomplete,
    wildcard_snapshots,
    aio_first_pass_cache,
    cleanup_plan=None,
):
    """Build one independent runtime value without installing it globally."""

    values = {
        "comfy": comfy,
        "seed_reservations": seed_reservations,
        "config": config,
        "clock": clock,
        "translation": translation,
        "autocomplete": autocomplete,
        "wildcard_snapshots": wildcard_snapshots,
        "aio_first_pass_cache": aio_first_pass_cache,
    }
    if cleanup_plan is not None:
        values["_cleanup_plan"] = cleanup_plan
    return runtime_module.RuntimeServices(**values)


def enter_test_context(test_case, manager):
    """Enter a context and bind its exact exit to unittest cleanup."""

    value = manager.__enter__()
    test_case.addCleanup(manager.__exit__, None, None, None)
    return value


@contextmanager
def isolated_installed_runtime(runtime_module, runtime=None):
    """Temporarily replace one process runtime and restore its prior identity."""

    with _RUNTIME_TEST_LOCK:
        with patch.object(runtime_module, "_RUNTIME_SERVICES", runtime):
            yield runtime


@contextmanager
def isolated_translation_facade(translation_module, translation):
    """Temporarily replace the call-time facade under the runtime fixture lock."""

    with _RUNTIME_TEST_LOCK:
        with patch.object(
            translation_module,
            "_DEFAULT_TRANSLATION_SERVICE",
            translation,
        ):
            yield translation


@contextmanager
def isolated_translation_route_executor(bootstrap_module, executor):
    """Temporarily replace the bootstrap-owned route executor for order tests."""

    with _RUNTIME_TEST_LOCK:
        with patch.object(
            bootstrap_module,
            "_TRANSLATION_ROUTE_EXECUTOR",
            executor,
        ):
            yield executor


@contextmanager
def isolated_bootstrap_runtime(
    bootstrap_module,
    runtime_module,
    translation_module,
):
    """Isolate terminal bootstrap state without adding a production reset seam."""

    translation = translation_module.PromptTranslationService()
    with _RUNTIME_TEST_LOCK:
        with (
            patch.object(bootstrap_module, "_WILDCARDS_INITIALIZED", False),
            patch.object(bootstrap_module, "_DEFAULT_RUNTIME", None),
            patch.object(
                bootstrap_module,
                "_TRANSLATION_ROUTE_EXECUTOR",
                None,
            ),
            patch.object(bootstrap_module, "_ATEXIT_REGISTERED", False),
            patch.object(bootstrap_module, "_SHUTDOWN", False),
            patch.object(runtime_module, "_RUNTIME_SERVICES", None),
            patch.object(bootstrap_module.atexit, "register"),
            patch.object(
                translation_module,
                "_DEFAULT_TRANSLATION_SERVICE",
                translation,
            ),
        ):
            yield translation
