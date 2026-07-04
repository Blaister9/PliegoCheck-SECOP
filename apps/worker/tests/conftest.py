"""Fixtures del worker contra PostgreSQL real."""

import os
import shutil
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

TEST_DATABASE_URL = os.environ.get(
    "PLIEGOCHECK_TEST_DATABASE_URL",
    "postgresql+psycopg://pliegocheck:pliegocheck@localhost:56543/pliegocheck_test",
)
TEST_STORAGE_PATH = Path("var/test-documents")


def pytest_configure(config: pytest.Config) -> None:
    _ = config
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["PLIEGOCHECK_STORAGE_PATH"] = str(TEST_STORAGE_PATH)
    os.environ["PLIEGOCHECK_MAX_FILE_SIZE_MB"] = "1"
    os.environ["PLIEGOCHECK_ALLOWED_WEB_ORIGINS"] = "http://localhost:3000"
    os.environ["PLIEGOCHECK_EXTRACTION_MAX_SECONDS"] = "10"
    os.environ["PLIEGOCHECK_EXTRACTION_MAX_CHARACTERS"] = "50000"
    os.environ["PLIEGOCHECK_EXTRACTION_MAX_PAGES"] = "20"
    os.environ["PLIEGOCHECK_EXTRACTION_MAX_SHEETS"] = "10"
    os.environ["PLIEGOCHECK_EXTRACTION_MAX_ROWS_PER_SHEET"] = "1000"
    os.environ["PLIEGOCHECK_EXTRACTION_MAX_ZIP_ENTRIES"] = "500"
    os.environ["PLIEGOCHECK_EXTRACTION_MAX_UNCOMPRESSED_MB"] = "50"
    os.environ["PLIEGOCHECK_EXTRACTION_MAX_COMPRESSION_RATIO"] = "100"
    os.environ["PLIEGOCHECK_WORKER_MAX_ATTEMPTS"] = "3"
    os.environ["PLIEGOCHECK_EXTRACTION_SYNC"] = "1"
    os.environ["PLIEGOCHECK_AI_ENABLED"] = "false"
    os.environ["OPENAI_API_KEY"] = ""
    os.environ["OPENAI_NORMALIZATION_MODEL"] = "gpt-5.5-pro"
    os.environ["OPENAI_NORMALIZATION_REASONING_EFFORT"] = "high"
    os.environ["OPENAI_NORMALIZATION_BACKGROUND"] = "true"
    os.environ["OPENAI_NORMALIZATION_MAX_OUTPUT_TOKENS"] = "16000"
    os.environ["OPENAI_NORMALIZATION_TIMEOUT_SECONDS"] = "60"
    os.environ["OPENAI_NORMALIZATION_POLL_INTERVAL_SECONDS"] = "1"
    os.environ["OPENAI_NORMALIZATION_MAX_CALLS_PER_RUN"] = "20"
    os.environ["OPENAI_NORMALIZATION_MAX_SEGMENTS_PER_BATCH"] = "5"
    os.environ["OPENAI_NORMALIZATION_MAX_CHARACTERS_PER_BATCH"] = "2000"
    os.environ["OPENAI_NORMALIZATION_MAX_TOTAL_CHARACTERS"] = "10000"
    os.environ["OPENAI_NORMALIZATION_MAX_RETRIES"] = "2"
    os.environ["PLIEGOCHECK_ALLOW_FAKE_NORMALIZATION_PROVIDER"] = "true"
    from pliegocheck_api.config import get_settings
    from pliegocheck_api.db import get_engine, get_sessionmaker

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()


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
                "TRUNCATE TABLE decision_events, decision_reviews, "
                "decision_action_items, decision_rule_evaluations, "
                "decision_input_findings, decision_runs, decision_jobs, "
                "decision_policy_versions, "
                "specialized_evaluation_reviews, specialized_evaluation_evidence, "
                "specialized_evaluation_results, specialized_evaluation_events, "
                "specialized_evaluation_runs, specialized_evaluation_jobs, "
                "specialized_requirement_rules, "
                "financial_evaluation_result_reviews, "
                "financial_evaluation_results, financial_metric_calculations, "
                "financial_evaluation_events, financial_evaluation_runs, "
                "financial_evaluation_jobs, financial_requirement_rules, "
                "financial_formula_versions, "
                "requirement_evidence, requirement_relations, "
                "rejected_requirement_candidates, requirements, "
                "requirement_normalization_batches, requirement_normalization_runs, "
                "requirement_normalization_jobs, prompt_versions, "
                "company_evidence_links, person_credentials, person_experience, "
                "person_education, company_financial_metrics, rup_snapshots, "
                "company_unspsc_codes, company_profile_snapshots, company_people, "
                "company_legal_registrations, company_financial_periods, "
                "company_experience_records, company_evidence_documents, "
                "company_certifications, company_capabilities, company_audit_events, "
                "company_profiles, "
                "extracted_segments, document_extractions, "
                "document_processing_jobs, import_events, process_documents, processes "
                "RESTART IDENTITY CASCADE"
            )
        )
    if TEST_STORAGE_PATH.exists():
        shutil.rmtree(TEST_STORAGE_PATH)
    TEST_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
    yield
    if TEST_STORAGE_PATH.exists():
        shutil.rmtree(TEST_STORAGE_PATH)
