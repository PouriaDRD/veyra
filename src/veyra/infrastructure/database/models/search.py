"""Search persistence models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base
from ..types import UTCDateTime


class SearchModel(Base):
    """SQLAlchemy representation of one Veyra search execution."""

    __tablename__ = "searches"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )

    platform: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime(),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime(),
        nullable=True,
    )

    failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


class SearchCandidateModel(Base):
    """SQLAlchemy representation of a profile within one search."""

    __tablename__ = "search_candidates"

    __table_args__ = (
        UniqueConstraint(
            "search_id",
            "profile_id",
            name="uq_search_candidates_search_profile",
        ),
        CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 10)",
            name="ck_search_candidates_score_range",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )

    search_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "searches.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
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

    discovery_source: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    discovered_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
    )

    snapshot_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "profile_snapshots.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    exclusion_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
