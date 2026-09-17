"""SQLAlchemy ProfileSnapshot repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from veyra.domain.snapshots import ProfileSnapshot

from ..mappers import snapshot_to_domain, snapshot_to_model
from ..models import ProfileSnapshotModel


class SqlAlchemySnapshotRepository:
    """SQLAlchemy implementation of the snapshot repository."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    def add(
        self,
        snapshot: ProfileSnapshot,
    ) -> None:
        """
        Persist a snapshot.

        Pending parent entities are flushed first so foreign-key ordering
        remains deterministic even without ORM relationships.
        """

        self._session.flush()

        self._session.add(
            snapshot_to_model(snapshot),
        )

    def get_by_id(
        self,
        snapshot_id: UUID,
    ) -> ProfileSnapshot | None:
        """Return a snapshot by identifier."""

        model = self._session.get(
            ProfileSnapshotModel,
            snapshot_id,
        )

        if model is None:
            return None

        return snapshot_to_domain(model)

    def list_for_profile(
        self,
        profile_id: UUID,
        *,
        limit: int | None = None,
    ) -> list[ProfileSnapshot]:
        """Return profile snapshots ordered newest first."""

        if limit is not None and limit <= 0:
            raise ValueError(
                "limit must be greater than zero.",
            )

        statement = (
            select(ProfileSnapshotModel)
            .where(
                ProfileSnapshotModel.profile_id == profile_id,
            )
            .order_by(
                ProfileSnapshotModel.captured_at.desc(),
            )
        )

        if limit is not None:
            statement = statement.limit(limit)

        models = self._session.scalars(
            statement,
        ).all()

        return [snapshot_to_domain(model) for model in models]
