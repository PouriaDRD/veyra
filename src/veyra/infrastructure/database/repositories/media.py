"""SQLAlchemy MediaAsset repository."""

from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from veyra.domain.media import MediaAsset

from ..mappers import media_asset_to_domain, media_asset_to_model
from ..models import MediaAssetModel


class SqlAlchemyMediaAssetRepository:
    """SQLAlchemy implementation of the MediaAsset repository."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    def add(
        self,
        asset: MediaAsset,
    ) -> None:
        """Persist a media asset."""

        self._session.add(
            media_asset_to_model(asset),
        )

    def get_by_id(
        self,
        asset_id: UUID,
    ) -> MediaAsset | None:
        """Return a media asset by identifier."""

        model = self._session.get(
            MediaAssetModel,
            asset_id,
        )

        if model is None:
            return None

        return media_asset_to_domain(model)

    def get_by_sha256(
        self,
        sha256: str,
    ) -> MediaAsset | None:
        """Return a media asset by SHA-256 digest."""

        normalized_sha256 = sha256.strip().lower()

        model = self._session.scalar(
            select(MediaAssetModel).where(
                MediaAssetModel.sha256 == normalized_sha256,
            )
        )

        if model is None:
            return None

        return media_asset_to_domain(model)

    def get_by_storage_path(
        self,
        storage_path: str,
    ) -> MediaAsset | None:
        """Return a media asset by local storage path."""

        normalized_path = str(
            Path(storage_path),
        )

        model = self._session.scalar(
            select(MediaAssetModel).where(
                MediaAssetModel.storage_path == normalized_path,
            )
        )

        if model is None:
            return None

        return media_asset_to_domain(model)
