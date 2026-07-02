"""Fixtures de integracion de la API contra PostgreSQL real."""

import os
import shutil
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

TEST_DATABASE_URL = os.environ.get(
    "PLIEGOCHECK_TEST_DATABASE_URL",
    "postgresql+psycopg://pliegocheck:pliegocheck@localhost:56543/pliegocheck_test",
)
TEST_STORAGE_PATH = Path("var/test-documents")


def pytest_configure(config: pytest.Config) -> None:
    _ = config
    os.environ.setdefault("DATABASE_URL", TEST_DATABASE_URL)
    os.environ.setdefault("PLIEGOCHECK_STORAGE_PATH", str(TEST_STORAGE_PATH))
    os.environ.setdefault("PLIEGOCHECK_MAX_FILE_SIZE_MB", "1")
    os.environ.setdefault("PLIEGOCHECK_ALLOWED_WEB_ORIGINS", "http://localhost:3000")


@pytest.fixture(scope="session")
def migrated_engine() -> Generator[Engine, None, None]:
    engine = create_engine(TEST_DATABASE_URL, isolation_level="AUTOCOMMIT")
    with engine.connect() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    alembic_cfg = Config("apps/api/alembic.ini")
    command.upgrade(alembic_cfg, "head")
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_database_and_storage(migrated_engine: Engine) -> Generator[None, None, None]:
    with migrated_engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE TABLE import_events, process_documents, processes "
                "RESTART IDENTITY CASCADE"
            )
        )
    if TEST_STORAGE_PATH.exists():
        shutil.rmtree(TEST_STORAGE_PATH)
    TEST_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
    yield
    if TEST_STORAGE_PATH.exists():
        shutil.rmtree(TEST_STORAGE_PATH)


@pytest.fixture
def client() -> TestClient:
    from pliegocheck_api.main import app

    return TestClient(app)
