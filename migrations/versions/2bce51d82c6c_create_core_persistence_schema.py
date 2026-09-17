"""create core persistence schema

Revision ID: 2bce51d82c6c
Revises:
Create Date: 2026-09-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "2bce51d82c6c"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply the migration."""

    op.create_table(
        "media_assets",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "sha256",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "kind",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "mime_type",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "extension",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "byte_size",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "storage_path",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "original_url",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "width",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "height",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "downloaded_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "byte_size > 0",
            name="ck_media_assets_positive_byte_size",
        ),
        sa.CheckConstraint(
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
        sa.PrimaryKeyConstraint(
            "id",
        ),
        sa.UniqueConstraint(
            "storage_path",
        ),
    )

    op.create_index(
        op.f("ix_media_assets_downloaded_at"),
        "media_assets",
        [
            "downloaded_at",
        ],
        unique=False,
    )

    op.create_index(
        op.f("ix_media_assets_sha256"),
        "media_assets",
        [
            "sha256",
        ],
        unique=True,
    )

    op.create_table(
        "profiles",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "platform",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "external_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "username",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id",
        ),
        sa.UniqueConstraint(
            "platform",
            "external_id",
            name="uq_profiles_platform_external_id",
        ),
    )

    op.create_index(
        op.f("ix_profiles_platform"),
        "profiles",
        [
            "platform",
        ],
        unique=False,
    )

    op.create_index(
        op.f("ix_profiles_username"),
        "profiles",
        [
            "username",
        ],
        unique=False,
    )

    op.create_table(
        "searches",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "platform",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "failure_reason",
            sa.Text(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "id",
        ),
    )

    op.create_index(
        op.f("ix_searches_created_at"),
        "searches",
        [
            "created_at",
        ],
        unique=False,
    )

    op.create_index(
        op.f("ix_searches_platform"),
        "searches",
        [
            "platform",
        ],
        unique=False,
    )

    op.create_index(
        op.f("ix_searches_status"),
        "searches",
        [
            "status",
        ],
        unique=False,
    )

    op.create_table(
        "profile_snapshots",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "profile_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "username",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "display_name",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "bio",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "followers_count",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "following_count",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "posts_count",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "is_private",
            sa.Boolean(),
            nullable=True,
        ),
        sa.Column(
            "is_verified",
            sa.Boolean(),
            nullable=True,
        ),
        sa.Column(
            "profile_picture_url",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "captured_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            [
                "profile_id",
            ],
            [
                "profiles.id",
            ],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
        ),
    )

    op.create_index(
        op.f("ix_profile_snapshots_captured_at"),
        "profile_snapshots",
        [
            "captured_at",
        ],
        unique=False,
    )

    op.create_index(
        op.f("ix_profile_snapshots_profile_id"),
        "profile_snapshots",
        [
            "profile_id",
        ],
        unique=False,
    )

    op.create_table(
        "search_candidates",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "search_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "profile_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "discovery_source",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "discovered_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "snapshot_id",
            sa.Uuid(),
            nullable=True,
        ),
        sa.Column(
            "score",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "exclusion_reason",
            sa.Text(),
            nullable=True,
        ),
        sa.CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 10)",
            name="ck_search_candidates_score_range",
        ),
        sa.ForeignKeyConstraint(
            [
                "profile_id",
            ],
            [
                "profiles.id",
            ],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            [
                "search_id",
            ],
            [
                "searches.id",
            ],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            [
                "snapshot_id",
            ],
            [
                "profile_snapshots.id",
            ],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint(
            "id",
        ),
        sa.UniqueConstraint(
            "search_id",
            "profile_id",
            name="uq_search_candidates_search_profile",
        ),
    )

    op.create_index(
        op.f("ix_search_candidates_profile_id"),
        "search_candidates",
        [
            "profile_id",
        ],
        unique=False,
    )

    op.create_index(
        op.f("ix_search_candidates_search_id"),
        "search_candidates",
        [
            "search_id",
        ],
        unique=False,
    )

    op.create_index(
        op.f("ix_search_candidates_snapshot_id"),
        "search_candidates",
        [
            "snapshot_id",
        ],
        unique=False,
    )

    op.create_index(
        op.f("ix_search_candidates_status"),
        "search_candidates",
        [
            "status",
        ],
        unique=False,
    )


def downgrade() -> None:
    """Revert the migration."""

    op.drop_index(
        op.f("ix_search_candidates_status"),
        table_name="search_candidates",
    )

    op.drop_index(
        op.f("ix_search_candidates_snapshot_id"),
        table_name="search_candidates",
    )

    op.drop_index(
        op.f("ix_search_candidates_search_id"),
        table_name="search_candidates",
    )

    op.drop_index(
        op.f("ix_search_candidates_profile_id"),
        table_name="search_candidates",
    )

    op.drop_table(
        "search_candidates",
    )

    op.drop_index(
        op.f("ix_profile_snapshots_profile_id"),
        table_name="profile_snapshots",
    )

    op.drop_index(
        op.f("ix_profile_snapshots_captured_at"),
        table_name="profile_snapshots",
    )

    op.drop_table(
        "profile_snapshots",
    )

    op.drop_index(
        op.f("ix_searches_status"),
        table_name="searches",
    )

    op.drop_index(
        op.f("ix_searches_platform"),
        table_name="searches",
    )

    op.drop_index(
        op.f("ix_searches_created_at"),
        table_name="searches",
    )

    op.drop_table(
        "searches",
    )

    op.drop_index(
        op.f("ix_profiles_username"),
        table_name="profiles",
    )

    op.drop_index(
        op.f("ix_profiles_platform"),
        table_name="profiles",
    )

    op.drop_table(
        "profiles",
    )

    op.drop_index(
        op.f("ix_media_assets_sha256"),
        table_name="media_assets",
    )

    op.drop_index(
        op.f("ix_media_assets_downloaded_at"),
        table_name="media_assets",
    )

    op.drop_table(
        "media_assets",
    )
