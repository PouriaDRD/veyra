"""Tests for media domain entities."""

from pathlib import Path

import pytest

from veyra.domain.media import MediaAsset, MediaKind

VALID_SHA256 = "a" * 64


def test_media_asset_normalizes_metadata() -> None:
    asset = MediaAsset(
        sha256=VALID_SHA256.upper(),
        kind=MediaKind.IMAGE,
        mime_type=" IMAGE/JPEG ",
        extension=".JPG",
        byte_size=1024,
        storage_path=Path(
            "data/media/example.jpg",
        ),
        width=512,
        height=512,
    )

    assert asset.sha256 == VALID_SHA256
    assert asset.mime_type == "image/jpeg"
    assert asset.extension == "jpg"


def test_media_asset_rejects_invalid_sha256() -> None:
    with pytest.raises(
        ValueError,
        match="sha256 must be",
    ):
        MediaAsset(
            sha256="invalid",
            kind=MediaKind.IMAGE,
            mime_type="image/jpeg",
            extension="jpg",
            byte_size=100,
            storage_path=Path("asset.jpg"),
        )


def test_media_dimensions_must_be_complete() -> None:
    with pytest.raises(
        ValueError,
        match="width and height",
    ):
        MediaAsset(
            sha256=VALID_SHA256,
            kind=MediaKind.IMAGE,
            mime_type="image/jpeg",
            extension="jpg",
            byte_size=100,
            storage_path=Path("asset.jpg"),
            width=512,
            height=None,
        )
