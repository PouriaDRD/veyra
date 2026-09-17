"""SQLAlchemy scoring audit repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from veyra.domain.scoring import ScoreSnapshot

from ..mappers import (
    score_snapshot_to_domain,
    score_snapshot_to_model,
)
from ..models import ScoreSnapshotModel


class SqlAlchemyScoreSnapshotRepository:
    """Append-only persistence for score audit snapshots."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    def add(
        self,
        snapshot: ScoreSnapshot,
    ) -> None:
        """Persist one immutable score snapshot."""

        self._session.flush()
        self._session.add(
            score_snapshot_to_model(
                snapshot,
            ),
        )

    def get_by_id(
        self,
        snapshot_id: UUID,
    ) -> ScoreSnapshot | None:
        """Return one score snapshot by identifier."""

        model = self._session.get(
            ScoreSnapshotModel,
            snapshot_id,
        )

        if model is None:
            return None

        return score_snapshot_to_domain(
            model,
        )

    def list_for_candidate(
        self,
        candidate_id: UUID,
    ) -> list[ScoreSnapshot]:
        """Return score history for one candidate, newest first."""

        models = self._session.scalars(
            select(ScoreSnapshotModel)
            .where(
                ScoreSnapshotModel.candidate_id == candidate_id,
            )
            .order_by(
                ScoreSnapshotModel.created_at.desc(),
                ScoreSnapshotModel.id.desc(),
            )
        ).all()

        return [
            score_snapshot_to_domain(
                model,
            )
            for model in models
        ]
