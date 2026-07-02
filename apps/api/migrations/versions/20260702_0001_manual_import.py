"""manual import persistence

Revision ID: 20260702_0001
Revises:
Create Date: 2026-07-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260702_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "processes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("internal_reference", sa.String(length=64), nullable=False),
        sa.Column("secop_reference", sa.String(length=500), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("contracting_entity", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_url", sa.String(length=2083), nullable=True),
        sa.Column("selection_method", sa.String(length=500), nullable=True),
        sa.Column("estimated_value", sa.Numeric(24, 2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closing_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "closing_at IS NULL OR published_at IS NULL OR closing_at >= published_at",
            name="ck_processes_closing_after_published",
        ),
        sa.CheckConstraint("btrim(title) <> ''", name="ck_processes_title_not_blank"),
        sa.CheckConstraint(
            "btrim(contracting_entity) <> ''",
            name="ck_processes_contracting_entity_not_blank",
        ),
        sa.CheckConstraint("source IN ('MANUAL')", name="ck_processes_source"),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'DOCUMENTS_PENDING', 'READY_FOR_INVENTORY')",
            name="ck_processes_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_processes_created_at", "processes", ["created_at"])
    op.create_index(
        "ix_processes_internal_reference",
        "processes",
        ["internal_reference"],
        unique=True,
    )
    op.create_index("ix_processes_status", "processes", ["status"])

    op.create_table(
        "process_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("process_id", sa.Uuid(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=700), nullable=False),
        sa.Column("declared_content_type", sa.String(length=255), nullable=True),
        sa.Column("detected_content_type", sa.String(length=255), nullable=True),
        sa.Column("extension", sa.String(length=16), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("document_type", sa.String(length=64), nullable=False),
        sa.Column("upload_status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "document_type IN ('UNKNOWN', 'TERMS', 'TECHNICAL_ANNEX', 'FINANCIAL_ANNEX', "
            "'EXPERIENCE_ANNEX', 'RISK_MATRIX', 'SCHEDULE', 'FORM', 'ADDENDUM', "
            "'SUPPORTING_DOCUMENT')",
            name="ck_documents_type",
        ),
        sa.CheckConstraint("sha256 ~ '^[a-f0-9]{64}$'", name="ck_documents_sha256"),
        sa.CheckConstraint("size_bytes > 0", name="ck_documents_size_positive"),
        sa.CheckConstraint(
            "upload_status IN ('STORED', 'REJECTED')",
            name="ck_documents_upload_status",
        ),
        sa.ForeignKeyConstraint(["process_id"], ["processes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("process_id", "sha256", name="uq_process_documents_process_sha256"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index("ix_process_documents_process_id", "process_documents", ["process_id"])

    op.create_table(
        "import_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("process_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["document_id"], ["process_documents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["process_id"], ["processes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_events_document_id", "import_events", ["document_id"])
    op.create_index("ix_import_events_process_id", "import_events", ["process_id"])


def downgrade() -> None:
    op.drop_index("ix_import_events_process_id", table_name="import_events")
    op.drop_index("ix_import_events_document_id", table_name="import_events")
    op.drop_table("import_events")
    op.drop_index("ix_process_documents_process_id", table_name="process_documents")
    op.drop_table("process_documents")
    op.drop_index("ix_processes_status", table_name="processes")
    op.drop_index("ix_processes_internal_reference", table_name="processes")
    op.drop_index("ix_processes_created_at", table_name="processes")
    op.drop_table("processes")
