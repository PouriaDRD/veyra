"""SQLAlchemy search repositories."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from veyra.domain.searches import Search, SearchCandidate

from ..mappers import (
    candidate_to_domain,
    candidate_to_model,
    search_to_domain,
    search_to_model,
)
from ..models import SearchCandidateModel, SearchModel


class SqlAlchemySearchRepository:
    """SQLAlchemy implementation of the Search repository."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    def add(
        self,
        search: Search,
    ) -> None:
        """Persist a new search."""

        self._session.add(
            search_to_model(search),
        )

    def get_by_id(
        self,
        search_id: UUID,
    ) -> Search | None:
        """Return a search by identifier."""

        model = self._session.get(
            SearchModel,
            search_id,
        )

        if model is None:
            return None

        return search_to_domain(model)

    def update(
        self,
        search: Search,
    ) -> None:
        """Persist changes to an existing search."""

        model = self._session.get(
            SearchModel,
            search.id,
        )

        if model is None:
            raise LookupError(
                f"Search {search.id} does not exist.",
            )

        model.platform = search.platform.value
        model.status = search.status.value
        model.created_at = search.created_at
        model.updated_at = search.updated_at
        model.started_at = search.started_at
        model.completed_at = search.completed_at
        model.failure_reason = search.failure_reason


class SqlAlchemySearchCandidateRepository:
    """SQLAlchemy implementation of the candidate repository."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    def add(
        self,
        candidate: SearchCandidate,
    ) -> None:
        """
        Persist a new candidate.

        Flush pending parent entities before registering the candidate so
        search, profile, and snapshot foreign keys are always resolvable.
        """

        self._session.flush()

        self._session.add(
            candidate_to_model(candidate),
        )

    def get_by_id(
        self,
        candidate_id: UUID,
    ) -> SearchCandidate | None:
        """Return a candidate by identifier."""

        model = self._session.get(
            SearchCandidateModel,
            candidate_id,
        )

        if model is None:
            return None

        return candidate_to_domain(model)

    def get_by_search_and_profile(
        self,
        search_id: UUID,
        profile_id: UUID,
    ) -> SearchCandidate | None:
        """Return one candidate by search/profile identity."""

        model = self._session.scalar(
            select(SearchCandidateModel).where(
                SearchCandidateModel.search_id == search_id,
                SearchCandidateModel.profile_id == profile_id,
            )
        )

        if model is None:
            return None

        return candidate_to_domain(model)

    def list_for_search(
        self,
        search_id: UUID,
    ) -> list[SearchCandidate]:
        """Return candidates belonging to one search."""

        models = self._session.scalars(
            select(SearchCandidateModel)
            .where(
                SearchCandidateModel.search_id == search_id,
            )
            .order_by(
                SearchCandidateModel.discovered_at.asc(),
            )
        ).all()

        return [candidate_to_domain(model) for model in models]

    def update(
        self,
        candidate: SearchCandidate,
    ) -> None:
        """Persist changes to an existing candidate."""

        model = self._session.get(
            SearchCandidateModel,
            candidate.id,
        )

        if model is None:
            raise LookupError(
                f"SearchCandidate {candidate.id} does not exist.",
            )

        model.search_id = candidate.search_id
        model.profile_id = candidate.profile_id
        model.discovery_source = candidate.discovery_source
        model.status = candidate.status.value
        model.discovered_at = candidate.discovered_at
        model.snapshot_id = candidate.snapshot_id
        model.score = candidate.score
        model.exclusion_reason = candidate.exclusion_reason
