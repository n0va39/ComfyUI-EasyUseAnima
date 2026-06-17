from __future__ import annotations

import json

try:
    from .anima_prompt import AnimaDexDB, AnimaDexImportClient
    from .anima_prompt.knowledge import PACKAGE_DATA_DIR
    from .settings import resolve_animadex_site, resolve_animadex_token
except ImportError:  # allows simple local import tests outside ComfyUI's package loader
    from anima_prompt import AnimaDexDB, AnimaDexImportClient
    from anima_prompt.knowledge import PACKAGE_DATA_DIR
    from settings import resolve_animadex_site, resolve_animadex_token


def dataset_paths() -> dict[str, str]:
    data_dir = PACKAGE_DATA_DIR
    return {
        "data_dir": str(data_dir),
        "characters_csv": str(data_dir / "import" / "characters.csv"),
        "artists_csv": str(data_dir / "import" / "artists.csv"),
        "character_index": str(data_dir / "index" / "character_index.jsonl"),
        "artist_index": str(data_dir / "index" / "artist_index.jsonl"),
    }


def download_animadex_dataset(
    *,
    force_refresh: bool = False,
    full_manifest: bool = False,
    site_override: str = "",
) -> tuple[str, str, str, str]:
    data_dir = PACKAGE_DATA_DIR
    import_dir = data_dir / "import"
    index_dir = data_dir / "index"
    character_index = index_dir / "character_index.jsonl"
    artist_index = index_dir / "artist_index.jsonl"

    if not force_refresh and character_index.is_file() and artist_index.is_file():
        report = {
            "status": "cached",
            **dataset_paths(),
        }
        return (
            "cached",
            json.dumps(report, ensure_ascii=False, indent=2),
            str(character_index),
            str(artist_index),
        )

    token_value = resolve_animadex_token()
    if not token_value:
        raise RuntimeError(
            "[EasyUse Anima] AnimaDex export token is required for first dataset download. "
            "Set it in ComfyUI Settings, token_file, or ANIMADEX_IMPORT_TOKEN."
        )

    import_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)

    client = AnimaDexImportClient(
        site=resolve_animadex_site(site_override),
        token=token_value,
    )
    result = client.download_required_csvs(data_dir=data_dir, full=full_manifest)
    db = AnimaDexDB.from_csvs(
        characters_csv=result.characters_csv,
        artists_csv=result.artists_csv,
    )
    character_index, artist_index = db.write_jsonl(index_dir)
    report = {
        "status": "downloaded",
        **dataset_paths(),
        "characters": len(db.characters),
        "artists": len(db.artists),
    }
    return (
        "downloaded",
        json.dumps(report, ensure_ascii=False, indent=2),
        str(character_index),
        str(artist_index),
    )
