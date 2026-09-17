"""Scoring audit persistence models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base
from ..types import UTCDateTime


class ScoreSnapshotModel(Base):
    """SQLAlchemy representation of one immutable scoring audit snapshot."""

    __tablename__ = "score_snapshots"

    __table_args__ = (
        CheckConstraint(
            "score >= 0 AND score <= 10",
            name="ck_score_snapshots_score_range",
        ),
        CheckConstraint(
            "normalized_value >= 0 AND normalized_value <= 1",
            name="ck_score_snapshots_normalized_value_range",
        ),
        CheckConstraint(
            "total_effective_weight > 0",
            name="ck_score_snapshots_effective_weight_positive",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )

    candidate_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "search_candidates.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    profile_snapshot_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "profile_snapshots.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    normalized_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    total_effective_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    algorithm_version: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    contributions_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        index=True,
    )
