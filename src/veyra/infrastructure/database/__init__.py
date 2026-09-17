"""Veyra database infrastructure."""

from .base import Base
from .engine import (
    SQLITE_PRAGMAS,
    build_sqlite_url,
    create_database_engine,
)
from .health import DatabaseHealth, check_database_health
from .models import (
    MediaAssetModel,
    ProfileModel,
    ProfileSnapshotModel,
    SearchCandidateModel,
    SearchModel,
)
from .session import SessionFactory, create_session_factory
from .unit_of_work import SqlAlchemyUnitOfWork

__all__ = [
    "SQLITE_PRAGMAS",
    "Base",
    "DatabaseHealth",
    "MediaAssetModel",
    "ProfileModel",
    "ProfileSnapshotModel",
    "SearchCandidateModel",
    "SearchModel",
    "SessionFactory",
    "SqlAlchemyUnitOfWork",
    "build_sqlite_url",
    "check_database_health",
    "create_database_engine",
    "create_session_factory",
]
