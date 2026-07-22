# pyright: strict
from __future__ import annotations

from dataclasses import dataclass

from .generation_values import (
    ObjectState,
    expect_bool,
    expect_int,
    expect_object,
    expect_object_list,
    expect_str,
    expect_string_list,
    required,
)


@dataclass(frozen=True, slots=True)
class AIOGenerationCivitaiHashFetcherConfig:
    state: ObjectState
    enabled: bool
    username: str
    model_name: str
    version: str

    @classmethod
    def from_value(cls, value: object, key: str) -> AIOGenerationCivitaiHashFetcherConfig:
        source = expect_object(value, key)
        known = ("enabled", "username", "model_name", "version")
        return cls(
            state=ObjectState.from_source(source, known),
            enabled=expect_bool(required(source, "enabled"), f"{key}.enabled"),
            username=expect_str(required(source, "username"), f"{key}.username"),
            model_name=expect_str(required(source, "model_name"), f"{key}.model_name"),
            version=expect_str(required(source, "version"), f"{key}.version"),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "enabled": self.enabled, "username": self.username,
            "model_name": self.model_name, "version": self.version,
        })


@dataclass(frozen=True, slots=True)
class AIOGenerationImageSaverConfig:
    state: ObjectState
    filename: str
    path: str
    extension: str
    lossless_webp: bool
    quality_jpeg_or_webp: int
    optimize_png: bool
    counter: int
    clip_skip: int
    time_format: str
    save_workflow_as_json: bool
    embed_workflow: bool
    save_prompt_metadata: bool
    additional_hashes: str
    additional_hash_bundles: tuple[str, ...]
    civitai_hash_fetchers: tuple[AIOGenerationCivitaiHashFetcherConfig, ...]
    download_civitai_data: bool
    easy_remix: bool
    custom: str

    @classmethod
    def from_value(cls, value: object, key: str) -> AIOGenerationImageSaverConfig:
        source = expect_object(value, key)
        known = (
            "filename", "path", "extension", "lossless_webp", "quality_jpeg_or_webp",
            "optimize_png", "counter", "clip_skip", "time_format", "save_workflow_as_json",
            "embed_workflow", "save_prompt_metadata", "additional_hashes",
            "additional_hash_bundles", "civitai_hash_fetchers", "download_civitai_data",
            "easy_remix", "custom",
        )
        fetcher_sources = expect_object_list(
            required(source, "civitai_hash_fetchers"), f"{key}.civitai_hash_fetchers"
        )
        return cls(
            state=ObjectState.from_source(source, known),
            filename=expect_str(required(source, "filename"), f"{key}.filename"),
            path=expect_str(required(source, "path"), f"{key}.path"),
            extension=expect_str(required(source, "extension"), f"{key}.extension"),
            lossless_webp=expect_bool(required(source, "lossless_webp"), f"{key}.lossless_webp"),
            quality_jpeg_or_webp=expect_int(
                required(source, "quality_jpeg_or_webp"), f"{key}.quality_jpeg_or_webp"
            ),
            optimize_png=expect_bool(required(source, "optimize_png"), f"{key}.optimize_png"),
            counter=expect_int(required(source, "counter"), f"{key}.counter"),
            clip_skip=expect_int(required(source, "clip_skip"), f"{key}.clip_skip"),
            time_format=expect_str(required(source, "time_format"), f"{key}.time_format"),
            save_workflow_as_json=expect_bool(
                required(source, "save_workflow_as_json"), f"{key}.save_workflow_as_json"
            ),
            embed_workflow=expect_bool(required(source, "embed_workflow"), f"{key}.embed_workflow"),
            save_prompt_metadata=expect_bool(
                required(source, "save_prompt_metadata"), f"{key}.save_prompt_metadata"
            ),
            additional_hashes=expect_str(required(source, "additional_hashes"), f"{key}.additional_hashes"),
            additional_hash_bundles=expect_string_list(
                required(source, "additional_hash_bundles"), f"{key}.additional_hash_bundles"
            ),
            civitai_hash_fetchers=tuple(
                AIOGenerationCivitaiHashFetcherConfig.from_value(
                    fetcher, f"{key}.civitai_hash_fetchers[{index}]"
                )
                for index, fetcher in enumerate(fetcher_sources)
            ),
            download_civitai_data=expect_bool(
                required(source, "download_civitai_data"), f"{key}.download_civitai_data"
            ),
            easy_remix=expect_bool(required(source, "easy_remix"), f"{key}.easy_remix"),
            custom=expect_str(required(source, "custom"), f"{key}.custom"),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "filename": self.filename, "path": self.path, "extension": self.extension,
            "lossless_webp": self.lossless_webp,
            "quality_jpeg_or_webp": self.quality_jpeg_or_webp,
            "optimize_png": self.optimize_png, "counter": self.counter,
            "clip_skip": self.clip_skip, "time_format": self.time_format,
            "save_workflow_as_json": self.save_workflow_as_json,
            "embed_workflow": self.embed_workflow,
            "save_prompt_metadata": self.save_prompt_metadata,
            "additional_hashes": self.additional_hashes,
            "additional_hash_bundles": list(self.additional_hash_bundles),
            "civitai_hash_fetchers": [fetcher.to_dict() for fetcher in self.civitai_hash_fetchers],
            "download_civitai_data": self.download_civitai_data,
            "easy_remix": self.easy_remix, "custom": self.custom,
        })


@dataclass(frozen=True, slots=True)
class AIOGenerationSaveConfig:
    state: ObjectState
    enabled: bool
    backend: str
    image_saver: AIOGenerationImageSaverConfig

    @classmethod
    def from_value(cls, value: object) -> AIOGenerationSaveConfig:
        key = "save"
        source = expect_object(value, key)
        known = ("enabled", "backend", "image_saver")
        return cls(
            state=ObjectState.from_source(source, known),
            enabled=expect_bool(required(source, "enabled"), f"{key}.enabled"),
            backend=expect_str(required(source, "backend"), f"{key}.backend"),
            image_saver=AIOGenerationImageSaverConfig.from_value(
                required(source, "image_saver"), f"{key}.image_saver"
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "enabled": self.enabled, "backend": self.backend,
            "image_saver": self.image_saver.to_dict(),
        })


@dataclass(frozen=True, slots=True)
class AIOGenerationPreviewConfig:
    state: ObjectState
    intermediate_images: bool
    compare_previous: bool
    image_feed: bool
    feed_count: int

    @classmethod
    def from_value(cls, value: object) -> AIOGenerationPreviewConfig:
        key = "preview"
        source = expect_object(value, key)
        known = ("intermediate_images", "compare_previous", "image_feed", "feed_count")
        return cls(
            state=ObjectState.from_source(source, known),
            intermediate_images=expect_bool(
                required(source, "intermediate_images"), f"{key}.intermediate_images"
            ),
            compare_previous=expect_bool(
                required(source, "compare_previous"), f"{key}.compare_previous"
            ),
            image_feed=expect_bool(required(source, "image_feed"), f"{key}.image_feed"),
            feed_count=expect_int(required(source, "feed_count"), f"{key}.feed_count"),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "intermediate_images": self.intermediate_images,
            "compare_previous": self.compare_previous,
            "image_feed": self.image_feed, "feed_count": self.feed_count,
        })
__all__ = ()
