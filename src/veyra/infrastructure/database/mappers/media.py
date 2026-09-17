"""Media persistence mapping."""

from pathlib import Path

from veyra.domain.media import MediaAsset, MediaKind

from ..models import MediaAssetModel


def media_asset_to_model(
    asset: MediaAsset,
) -> MediaAssetModel:
    """Map a MediaAsset entity to its ORM representation."""

    return MediaAssetModel(
        id=asset.id,
        sha256=asset.sha256,
        kind=asset.kind.value,
        mime_type=asset.mime_type,
        extension=asset.extension,
        byte_size=asset.byte_size,
        storage_path=str(asset.storage_path),
        original_url=asset.original_url,
        width=asset.width,
        height=asset.height,
        downloaded_at=asset.downloaded_at,
    )


def media_asset_to_domain(
    model: MediaAssetModel,
) -> MediaAsset:
    """Reconstruct a MediaAsset from its ORM representation."""

    return MediaAsset(
        id=model.id,
        sha256=model.sha256,
        kind=MediaKind(model.kind),
        mime_type=model.mime_type,
        extension=model.extension,
        byte_size=model.byte_size,
        storage_path=Path(model.storage_path),
        original_url=model.original_url,
        width=model.width,
        height=model.height,
        downloaded_at=model.downloaded_at,
    )
