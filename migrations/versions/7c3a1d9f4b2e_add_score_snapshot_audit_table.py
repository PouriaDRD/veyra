"""add score snapshot audit table

Revision ID: 7c3a1d9f4b2e
Revises: 2bce51d82c6c
Create Date: 2026-09-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7c3a1d9f4b2e"
down_revision: str | Sequence[str] | None = "2bce51d82c6c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply the migration."""

    op.create_table(
        "score_snapshots",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "candidate_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "profile_snapshot_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "score",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "normalized_value",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "total_effective_weight",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "algorithm_version",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "contributions_json",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "normalized_value >= 0 AND normalized_value <= 1",
            name="ck_score_snapshots_normalized_value_range",
        ),
        sa.CheckConstraint(
            "score >= 0 AND score <= 10",
            name="ck_score_snapshots_score_range",
        ),
        sa.CheckConstraint(
            "total_effective_weight > 0",
            name="ck_score_snapshots_effective_weight_positive",
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["search_candidates.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["profile_snapshot_id"],
            ["profile_snapshots.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "id",
        ),
    )

    op.create_index(
        op.f("ix_score_snapshots_algorithm_version"),
        "score_snapshots",
        ["algorithm_version"],
        unique=False,
    )
    op.create_index(
        op.f("ix_score_snapshots_candidate_id"),
        "score_snapshots",
        ["candidate_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_score_snapshots_created_at"),
        "score_snapshots",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_score_snapshots_profile_snapshot_id"),
        "score_snapshots",
        ["profile_snapshot_id"],
        unique=False,
    )


def downgrade() -> None:
    """Revert the migration."""

    op.drop_index(
        op.f("ix_score_snapshots_profile_snapshot_id"),
        table_name="score_snapshots",
    )
    op.drop_index(
        op.f("ix_score_snapshots_created_at"),
        table_name="score_snapshots",
    )
    op.drop_index(
        op.f("ix_score_snapshots_candidate_id"),
        table_name="score_snapshots",
    )
    op.drop_index(
        op.f("ix_score_snapshots_algorithm_version"),
        table_name="score_snapshots",
    )
    op.drop_table(
        "score_snapshots",
    )
