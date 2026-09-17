"""Profile persistence model."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base
from ..types import UTCDateTime


class ProfileModel(Base):
    """SQLAlchemy representation of a persistent social profile."""

    __tablename__ = "profiles"

    __table_args__ = (
        UniqueConstraint(
            "platform",
            "external_id",
            name="uq_profiles_platform_external_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )

    platform: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    external_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
    )
