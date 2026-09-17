"""Search persistence mapping."""

from veyra.domain.profiles import SocialPlatform
from veyra.domain.searches import (
    CandidateStatus,
    Search,
    SearchCandidate,
    SearchStatus,
)

from ..models import SearchCandidateModel, SearchModel


def search_to_model(
    search: Search,
) -> SearchModel:
    """Map a Search entity to its ORM representation."""

    return SearchModel(
        id=search.id,
        platform=search.platform.value,
        status=search.status.value,
        created_at=search.created_at,
        updated_at=search.updated_at,
        started_at=search.started_at,
        completed_at=search.completed_at,
        failure_reason=search.failure_reason,
    )


def search_to_domain(
    model: SearchModel,
) -> Search:
    """Reconstruct a Search entity from its ORM representation."""

    return Search(
        id=model.id,
        platform=SocialPlatform(model.platform),
        status=SearchStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
        started_at=model.started_at,
        completed_at=model.completed_at,
        failure_reason=model.failure_reason,
    )


def candidate_to_model(
    candidate: SearchCandidate,
) -> SearchCandidateModel:
    """Map a SearchCandidate to its ORM representation."""

    return SearchCandidateModel(
        id=candidate.id,
        search_id=candidate.search_id,
        profile_id=candidate.profile_id,
        discovery_source=candidate.discovery_source,
        status=candidate.status.value,
        discovered_at=candidate.discovered_at,
        snapshot_id=candidate.snapshot_id,
        score=candidate.score,
        exclusion_reason=candidate.exclusion_reason,
    )


def candidate_to_domain(
    model: SearchCandidateModel,
) -> SearchCandidate:
    """Reconstruct a SearchCandidate from its ORM representation."""

    return SearchCandidate(
        id=model.id,
        search_id=model.search_id,
        profile_id=model.profile_id,
        discovery_source=model.discovery_source,
        status=CandidateStatus(model.status),
        discovered_at=model.discovered_at,
        snapshot_id=model.snapshot_id,
        score=model.score,
        exclusion_reason=model.exclusion_reason,
    )
