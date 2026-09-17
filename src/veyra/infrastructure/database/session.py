"""SQLAlchemy session factory."""

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

SessionFactory = sessionmaker[Session]


def create_session_factory(
    engine: Engine,
) -> SessionFactory:
    """Create the application's SQLAlchemy session factory."""

    return sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )
