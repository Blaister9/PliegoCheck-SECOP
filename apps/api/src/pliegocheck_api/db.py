"""Sesion y metadata SQLAlchemy de la API."""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from pliegocheck_api.config import get_settings


class Base(DeclarativeBase):
    """Base declarativa compartida por modelos y Alembic."""


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True)


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def get_session() -> Generator[Session, None, None]:
    session = get_sessionmaker()()
    try:
        yield session
    finally:
        session.close()
