"""Media persistence models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base
from ..types import UTCDateTime


class MediaAssetModel(Base):
    """SQLAlchemy representation of a locally persisted media asset."""

    __tablename__ = "media_assets"

    __table_args__ = (
        CheckConstraint(
            "byte_size > 0",
            name="ck_media_assets_positive_byte_size",
        ),
        CheckConstraint(
            """
            (
                width IS NULL
                AND height IS NULL
            )
            OR
            (
                width > 0
                AND height > 0
            )
            """,
            name="ck_media_assets_dimensions",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )

    sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    kind: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    mime_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    extension: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    byte_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    storage_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )

    original_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    width: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    height: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    downloaded_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        index=True,
    )
