"""external procurement search and import.

Revision ID: 20260713_0016
Revises: 20260704_0010
Create Date: 2026-07-13 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260713_0016"
down_revision: str | None = "20260704_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_processes_source", "processes", type_="check")
    op.create_check_constraint(
        "ck_processes_source", "processes", "source IN ('MANUAL', 'SECOP_IMPORT')"
    )
    op.create_table(
        "external_procurement_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_system", sa.String(32), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("base_url", sa.String(2083), nullable=False),
        sa.Column("dataset_id", sa.String(64), nullable=False),
        sa.Column("human_url", sa.String(2083), nullable=False),
        sa.Column("api_url", sa.String(2083), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True)),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('AVAILABLE','PARTIAL','STALE','ERROR','UNSUPPORTED')",
            name="ck_external_procurement_sources_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_system", "dataset_id", name="uq_external_procurement_sources_system_dataset"
        ),
    )
    op.create_index(
        "ix_external_procurement_sources_system", "external_procurement_sources", ["source_system"]
    )
    op.create_table(
        "external_procurement_searches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("query", sa.String(200)),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("limit", sa.Integer(), nullable=False),
        sa.Column("offset", sa.Integer(), nullable=False),
        sa.Column("unsupported_filters", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("error_code", sa.String(64)),
        sa.Column("error_message", sa.String(500)),
        sa.Column("created_by", sa.Uuid()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('PENDING','RUNNING','COMPLETED','COMPLETED_WITH_WARNINGS','FAILED')",
            name="ck_external_procurement_searches_status",
        ),
        sa.ForeignKeyConstraint(["source_id"], ["external_procurement_sources.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["auth_users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_external_procurement_searches_created_at",
        "external_procurement_searches",
        ["created_at"],
    )
    op.create_index(
        "ix_external_procurement_searches_source", "external_procurement_searches", ["source_id"]
    )
    op.create_table(
        "external_procurement_search_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("search_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("source_system", sa.String(32), nullable=False),
        sa.Column("source_dataset", sa.String(64), nullable=False),
        sa.Column("source_process_id", sa.String(500), nullable=False),
        sa.Column("source_process_reference", sa.String(500)),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("entity_name", sa.String(500), nullable=False),
        sa.Column("modality", sa.String(500)),
        sa.Column("status", sa.String(500)),
        sa.Column("estimated_value", sa.Numeric(24, 2)),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("publication_date", sa.DateTime(timezone=True)),
        sa.Column("closing_date", sa.DateTime(timezone=True)),
        sa.Column("department", sa.String(300)),
        sa.Column("municipality", sa.String(300)),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("normalized_payload", sa.JSON(), nullable=False),
        sa.Column("raw_payload_hash", sa.String(64), nullable=False),
        sa.Column("field_statuses", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("source_url", sa.String(2083)),
        sa.Column("documents_url", sa.String(2083)),
        sa.Column("documents_status", sa.String(64), nullable=False),
        sa.Column("import_status", sa.String(32), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "import_status IN ('PENDING','IMPORTED','SKIPPED_DUPLICATE','FAILED')",
            name="ck_external_procurement_results_import_status",
        ),
        sa.CheckConstraint(
            "documents_status IN ('DOCUMENTS_NOT_AVAILABLE','DOCUMENT_LINKS_AVAILABLE',"
            "'DOCUMENT_DOWNLOAD_UNSUPPORTED','DOCUMENT_DOWNLOAD_FAILED','DOCUMENTS_IMPORTED')",
            name="ck_external_procurement_results_documents_status",
        ),
        sa.ForeignKeyConstraint(
            ["search_id"], ["external_procurement_searches.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["source_id"], ["external_procurement_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "search_id",
            "source_dataset",
            "source_process_id",
            name="uq_external_procurement_results_search_process",
        ),
    )
    op.create_index(
        "ix_external_procurement_results_search",
        "external_procurement_search_results",
        ["search_id"],
    )
    op.create_index(
        "ix_external_procurement_results_source_key",
        "external_procurement_search_results",
        ["source_system", "source_dataset", "source_process_id"],
    )
    op.create_table(
        "external_procurement_process_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("process_id", sa.Uuid(), nullable=False),
        sa.Column("source_result_id", sa.Uuid(), nullable=False),
        sa.Column("source_system", sa.String(32), nullable=False),
        sa.Column("source_dataset", sa.String(64), nullable=False),
        sa.Column("source_process_id", sa.String(500), nullable=False),
        sa.Column("source_process_reference", sa.String(500)),
        sa.Column("source_url", sa.String(2083)),
        sa.Column("documents_url", sa.String(2083)),
        sa.Column("documents_status", sa.String(64), nullable=False),
        sa.Column("external_metadata", sa.JSON(), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "documents_status IN ('DOCUMENTS_NOT_AVAILABLE','DOCUMENT_LINKS_AVAILABLE',"
            "'DOCUMENT_DOWNLOAD_UNSUPPORTED','DOCUMENT_DOWNLOAD_FAILED','DOCUMENTS_IMPORTED')",
            name="ck_external_procurement_links_documents_status",
        ),
        sa.ForeignKeyConstraint(["process_id"], ["processes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_result_id"], ["external_procurement_search_results.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_system",
            "source_dataset",
            "source_process_id",
            name="uq_external_procurement_links_source_key",
        ),
    )
    op.create_index(
        "ix_external_procurement_links_process",
        "external_procurement_process_links",
        ["process_id"],
    )
    op.create_table(
        "external_procurement_imports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_result_id", sa.Uuid(), nullable=False),
        sa.Column("process_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("deduplication_key", sa.String(64), nullable=False),
        sa.Column("import_manifest", sa.JSON(), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.Uuid()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('PENDING','IMPORTED','SKIPPED_DUPLICATE','FAILED')",
            name="ck_external_procurement_imports_status",
        ),
        sa.ForeignKeyConstraint(["source_result_id"], ["external_procurement_search_results.id"]),
        sa.ForeignKeyConstraint(["process_id"], ["processes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["auth_users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_external_procurement_imports_result",
        "external_procurement_imports",
        ["source_result_id"],
    )
    op.create_index(
        "ix_external_procurement_imports_process", "external_procurement_imports", ["process_id"]
    )
    op.create_index(
        "ix_external_procurement_imports_dedup",
        "external_procurement_imports",
        ["deduplication_key"],
    )


def downgrade() -> None:
    op.drop_table("external_procurement_imports")
    op.drop_table("external_procurement_process_links")
    op.drop_table("external_procurement_search_results")
    op.drop_table("external_procurement_searches")
    op.drop_table("external_procurement_sources")
    op.drop_constraint("ck_processes_source", "processes", type_="check")
    op.create_check_constraint("ck_processes_source", "processes", "source IN ('MANUAL')")
