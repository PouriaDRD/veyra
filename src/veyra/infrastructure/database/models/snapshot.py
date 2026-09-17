"""Profile snapshot persistence model."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base
from ..types import UTCDateTime


class ProfileSnapshotModel(Base):
    """SQLAlchemy representation of a historical profile snapshot."""

    __tablename__ = "profile_snapshots"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )

    profile_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "profiles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    display_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    followers_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    following_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    posts_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    is_private: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    is_verified: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    profile_picture_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    captured_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        index=True,
    )
