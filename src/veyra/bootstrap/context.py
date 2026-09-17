"""Application bootstrap context."""

from dataclasses import dataclass

from sqlalchemy import Engine
from structlog.stdlib import BoundLogger

from veyra.config import Settings
from veyra.infrastructure.database import SessionFactory


@dataclass(frozen=True, slots=True)
class ApplicationContext:
    """
    Runtime dependencies shared by Veyra entrypoints.

    The context acts as the composition root result and keeps bootstrap
    concerns outside business and domain code.
    """

    settings: Settings
    logger: BoundLogger
    database_engine: Engine
    session_factory: SessionFactory
