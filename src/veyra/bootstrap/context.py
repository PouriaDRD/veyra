"""Application bootstrap context."""

from dataclasses import dataclass

from structlog.stdlib import BoundLogger

from veyra.config import Settings


@dataclass(frozen=True, slots=True)
class ApplicationContext:
    """
    Runtime dependencies shared by Veyra entrypoints.

    The context acts as the composition root result and keeps bootstrap
    concerns outside business and domain code.
    """

    settings: Settings
    logger: BoundLogger
