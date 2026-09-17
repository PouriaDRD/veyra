"""Tests for structured logging context."""

import structlog

from veyra.logging import (
    bind_log_context,
    clear_log_context,
    unbind_log_context,
)


def test_log_context_can_be_bound_and_cleared() -> None:
    clear_log_context()

    bind_log_context(
        search_id="search-123",
        profile_id="profile-456",
    )

    context = structlog.contextvars.get_contextvars()

    assert context["search_id"] == "search-123"
    assert context["profile_id"] == "profile-456"

    unbind_log_context("profile_id")

    context = structlog.contextvars.get_contextvars()

    assert "profile_id" not in context
    assert context["search_id"] == "search-123"

    clear_log_context()

    assert structlog.contextvars.get_contextvars() == {}
