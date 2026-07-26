# pyright: strict
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TypeAlias, cast

from .generation_values import freeze_object, thaw_object

AIO_GENERATION_SETTINGS_SCHEMA = "easyuse_anima_aio_generation_settings"
AIO_GENERATION_SETTINGS_CURRENT_VERSION = 2
AIO_GENERATION_STAGE_IDS = (
    "first_pass",
    "highres",
    "detailer",
    "upscale",
)
AIO_MODEL_PATCH_ORDER_REVISION = 1
AIO_MODEL_PATCH_PRECEDENCE = (("kj.torch_compile", "dave"),)

AIOGenerationMigrationFunction: TypeAlias = Callable[
    [Mapping[str, object]],
    Mapping[str, object],
]


class AIOGenerationMigrationError(ValueError):
    """A pure generation-settings version contract could not be satisfied."""


def _require_positive_version(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise AIOGenerationMigrationError(f"{label} must be a positive integer")
    return value


def _copy_generation_settings(source: Mapping[str, object]) -> dict[str, object]:
    try:
        return thaw_object(freeze_object(source))
    except (TypeError, ValueError) as exc:
        raise AIOGenerationMigrationError(
            "AiO generation settings must be a JSON object"
        ) from exc


def detect_aio_generation_settings_version(source: Mapping[str, object]) -> int:
    """Return the explicitly declared supported schema version without coercion."""

    schema = source.get("schema")
    if schema != AIO_GENERATION_SETTINGS_SCHEMA:
        raise AIOGenerationMigrationError(
            "AiO generation settings schema is missing or unsupported"
        )
    return _require_positive_version(
        source.get("version"),
        "AiO generation settings version",
    )


@dataclass(frozen=True, slots=True)
class AIOGenerationMigrationStep:
    from_version: int
    to_version: int
    migrate: AIOGenerationMigrationFunction

    def __post_init__(self) -> None:
        from_version = _require_positive_version(
            self.from_version,
            "Migration from_version",
        )
        to_version = _require_positive_version(
            self.to_version,
            "Migration to_version",
        )
        if to_version != from_version + 1:
            raise AIOGenerationMigrationError(
                "AiO generation migrations must advance exactly one version"
            )
        if not callable(self.migrate):
            raise AIOGenerationMigrationError("Migration step must be callable")


@dataclass(frozen=True, slots=True)
class AIOGenerationMigrationRegistry:
    steps: tuple[AIOGenerationMigrationStep, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(cast(object, self.steps), tuple):
            raise AIOGenerationMigrationError("Migration registry steps must be a tuple")
        versions = tuple(step.from_version for step in self.steps)
        if versions != tuple(sorted(versions)):
            raise AIOGenerationMigrationError(
                "Migration registry steps must be ordered by from_version"
            )
        if len(versions) != len(set(versions)):
            raise AIOGenerationMigrationError(
                "Migration registry has duplicate from_version entries"
            )

    def step_from(self, version: int) -> AIOGenerationMigrationStep | None:
        for step in self.steps:
            if step.from_version == version:
                return step
        return None

    def with_step(
        self,
        step: AIOGenerationMigrationStep,
    ) -> AIOGenerationMigrationRegistry:
        """Return a new immutable registry containing one reviewed step."""

        return AIOGenerationMigrationRegistry(
            tuple(sorted((*self.steps, step), key=lambda item: item.from_version))
        )


def _migrate_aio_generation_settings_v1_to_v2(
    source: Mapping[str, object],
) -> Mapping[str, object]:
    """Add explicit DAVE stage scope while preserving legacy all-stage behavior."""

    migrated = _copy_generation_settings(source)
    model_patches = migrated.get("model_patches")
    if isinstance(model_patches, dict):
        model_patch_values = cast(dict[str, object], model_patches)
        dave = model_patch_values.get("dave")
        if isinstance(dave, dict) and "stage_scope" not in dave:
            dave_values = cast(dict[str, object], dave)
            dave_values["stage_scope"] = {
                stage_id: True for stage_id in AIO_GENERATION_STAGE_IDS
            }
    migrated["version"] = 2
    return migrated


AIO_GENERATION_MIGRATION_REGISTRY = (
    AIOGenerationMigrationRegistry().with_step(
        AIOGenerationMigrationStep(
            1,
            2,
            _migrate_aio_generation_settings_v1_to_v2,
        )
    )
)


def migrate_aio_generation_settings(
    source: Mapping[str, object],
    *,
    target_version: int = AIO_GENERATION_SETTINGS_CURRENT_VERSION,
    registry: AIOGenerationMigrationRegistry = AIO_GENERATION_MIGRATION_REGISTRY,
) -> dict[str, object]:
    """Deep-copy and migrate one explicit schema version without I/O or mutation."""

    target = _require_positive_version(target_version, "Migration target_version")
    current = _copy_generation_settings(source)
    version = detect_aio_generation_settings_version(current)
    if version > target:
        raise AIOGenerationMigrationError(
            f"AiO generation settings version {version} is newer than target {target}"
        )

    while version < target:
        step = registry.step_from(version)
        if step is None:
            raise AIOGenerationMigrationError(
                f"No AiO generation migration is registered for version {version}"
            )
        try:
            migrated = step.migrate(current)
        except AIOGenerationMigrationError:
            raise
        except Exception as exc:
            raise AIOGenerationMigrationError(
                f"AiO generation migration {step.from_version}->{step.to_version} failed"
            ) from exc
        if not isinstance(cast(object, migrated), Mapping):
            raise AIOGenerationMigrationError(
                f"AiO generation migration {step.from_version}->{step.to_version} "
                "must return an object"
            )
        current = _copy_generation_settings(migrated)
        migrated_version = detect_aio_generation_settings_version(current)
        if migrated_version != step.to_version:
            raise AIOGenerationMigrationError(
                f"AiO generation migration {step.from_version}->{step.to_version} "
                f"returned version {migrated_version}"
            )
        version = migrated_version

    return current


__all__ = ()
