"""Tests for Search domain behavior."""

import pytest

from veyra.domain.profiles import SocialPlatform
from veyra.domain.searches import Search, SearchStatus


def test_search_starts_created() -> None:
    search = Search(
        platform=SocialPlatform.INSTAGRAM,
    )

    assert search.status is SearchStatus.CREATED
    assert search.started_at is None
    assert search.completed_at is None


def test_search_can_complete_valid_lifecycle() -> None:
    search = Search(
        platform=SocialPlatform.INSTAGRAM,
    )

    search.transition_to(SearchStatus.DISCOVERING)
    search.transition_to(SearchStatus.SNAPSHOTTING)
    search.transition_to(SearchStatus.ANALYZING)
    search.transition_to(SearchStatus.SCORING)
    search.transition_to(SearchStatus.COMPLETED)

    assert search.status is SearchStatus.COMPLETED
    assert search.started_at is not None
    assert search.completed_at is not None


def test_search_rejects_invalid_transition() -> None:
    search = Search(
        platform=SocialPlatform.INSTAGRAM,
    )

    with pytest.raises(
        ValueError,
        match="Invalid search transition",
    ):
        search.transition_to(
            SearchStatus.COMPLETED,
        )


def test_search_can_fail() -> None:
    search = Search(
        platform=SocialPlatform.INSTAGRAM,
    )

    search.transition_to(
        SearchStatus.DISCOVERING,
    )

    search.fail(
        "Provider unavailable",
    )

    assert search.status is SearchStatus.FAILED
    assert search.failure_reason == "Provider unavailable"
    assert search.completed_at is not None


def test_failed_transition_requires_fail_method() -> None:
    search = Search(
        platform=SocialPlatform.INSTAGRAM,
    )

    with pytest.raises(
        ValueError,
        match=r"Use fail\(\)",
    ):
        search.transition_to(
            SearchStatus.FAILED,
        )


def test_completed_search_requires_completion_metadata() -> None:
    with pytest.raises(
        ValueError,
        match="completed search must have started_at",
    ):
        Search(
            platform=SocialPlatform.INSTAGRAM,
            status=SearchStatus.COMPLETED,
        )
