"""Structured logging context helpers."""

from collections.abc import Mapping

import structlog

LogContextValue = str | int | float | bool | None


def bind_log_context(
    **values: LogContextValue,
) -> None:
    """
    Bind values to the current execution context.

    Bound values are automatically included in subsequent structured
    log events within the same context.
    """

    structlog.contextvars.bind_contextvars(**values)


def bind_log_context_mapping(
    values: Mapping[str, LogContextValue],
) -> None:
    """Bind a mapping of values to the current logging context."""

    structlog.contextvars.bind_contextvars(**values)


def unbind_log_context(*keys: str) -> None:
    """Remove selected keys from the current logging context."""

    structlog.contextvars.unbind_contextvars(*keys)


def clear_log_context() -> None:
    """Clear all values from the current logging context."""

    structlog.contextvars.clear_contextvars()
