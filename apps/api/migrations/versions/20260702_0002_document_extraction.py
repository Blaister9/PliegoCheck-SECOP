"""document extraction queue and results

Revision ID: 20260702_0002
Revises: 20260702_0001
Create Date: 2026-07-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260702_0002"
down_revision: str | None = "20260702_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "process_documents",
        sa.Column(
            "processing_status",
            sa.String(length=32),
            nullable=False,
            server_default="NOT_QUEUED",
        ),
    )
    op.create_check_constraint(
        "ck_documents_processing_status",
        "process_documents",
        "processing_status IN ('NOT_QUEUED', 'QUEUED', 'PROCESSING', 'COMPLETED', "
        "'COMPLETED_WITH_WARNINGS', 'NEEDS_OCR', 'UNSUPPORTED', 'ENCRYPTED', 'FAILED')",
    )
    op.create_index(
        "ix_process_documents_processing_status",
        "process_documents",
        ["processing_status"],
    )
    op.alter_column("process_documents", "processing_status", server_default=None)

    op.create_table(
        "document_processing_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column(
            "available_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.String(length=128), nullable=True),
        sa.Column("last_error_code", sa.String(length=64), nullable=True),
        sa.Column("last_error_message", sa.String(length=1000), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "job_type IN ('EXTRACT_DOCUMENT')",
            name="ck_processing_jobs_type",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED')",
            name="ck_processing_jobs_status",
        ),
        sa.CheckConstraint("priority >= 0", name="ck_processing_jobs_priority_nonnegative"),
        sa.CheckConstraint("attempt_count >= 0", name="ck_processing_jobs_attempt_nonnegative"),
        sa.CheckConstraint("max_attempts > 0", name="ck_processing_jobs_max_attempts_positive"),
        sa.ForeignKeyConstraint(["document_id"], ["process_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_processing_jobs_claim",
        "document_processing_jobs",
        ["status", "available_at", "priority", "created_at"],
    )
    op.create_index(
        "ix_processing_jobs_document_id",
        "document_processing_jobs",
        ["document_id"],
    )
    op.create_index(
        "uq_processing_jobs_active_document_type",
        "document_processing_jobs",
        ["document_id", "job_type"],
        unique=True,
        postgresql_where=sa.text("status IN ('PENDING', 'PROCESSING')"),
    )

    op.create_table(
        "document_extractions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column("extractor_name", sa.String(length=128), nullable=False),
        sa.Column("extractor_version", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("detected_format", sa.String(length=32), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("sheet_count", sa.Integer(), nullable=True),
        sa.Column("segment_count", sa.Integer(), nullable=False),
        sa.Column("character_count", sa.Integer(), nullable=False),
        sa.Column("language_hint", sa.String(length=32), nullable=True),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'COMPLETED_WITH_WARNINGS', "
            "'NEEDS_OCR', 'UNSUPPORTED', 'ENCRYPTED', 'FAILED')",
            name="ck_document_extractions_status",
        ),
        sa.CheckConstraint("source_sha256 ~ '^[a-f0-9]{64}$'", name="ck_extractions_sha256"),
        sa.CheckConstraint(
            "page_count IS NULL OR page_count >= 0",
            name="ck_extractions_page_count",
        ),
        sa.CheckConstraint(
            "sheet_count IS NULL OR sheet_count >= 0",
            name="ck_extractions_sheet_count",
        ),
        sa.CheckConstraint("segment_count >= 0", name="ck_extractions_segment_count"),
        sa.CheckConstraint("character_count >= 0", name="ck_extractions_character_count"),
        sa.ForeignKeyConstraint(["document_id"], ["process_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["document_processing_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_document_extractions_document_id",
        "document_extractions",
        ["document_id"],
    )
    op.create_index("ix_document_extractions_job_id", "document_extractions", ["job_id"])
    op.create_index(
        "uq_document_extractions_active_version",
        "document_extractions",
        ["document_id", "source_sha256", "extractor_name", "extractor_version"],
        unique=True,
        postgresql_where=sa.text("status IN ('PENDING', 'PROCESSING')"),
    )

    op.create_table(
        "extracted_segments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("extraction_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("segment_type", sa.String(length=32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("paragraph_index", sa.Integer(), nullable=True),
        sa.Column("table_index", sa.Integer(), nullable=True),
        sa.Column("sheet_name", sa.String(length=255), nullable=True),
        sa.Column("row_start", sa.Integer(), nullable=True),
        sa.Column("row_end", sa.Integer(), nullable=True),
        sa.Column("line_start", sa.Integer(), nullable=True),
        sa.Column("line_end", sa.Integer(), nullable=True),
        sa.Column("source_location", sa.JSON(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "segment_type IN ('PAGE_TEXT', 'PARAGRAPH', 'TABLE', 'SHEET_ROW', 'TEXT_LINES')",
            name="ck_segments_type",
        ),
        sa.CheckConstraint("sequence > 0", name="ck_segments_sequence_positive"),
        sa.CheckConstraint("btrim(text) <> ''", name="ck_segments_text_not_blank"),
        sa.CheckConstraint(
            "page_number IS NULL OR page_number > 0",
            name="ck_segments_page_positive",
        ),
        sa.CheckConstraint(
            "paragraph_index IS NULL OR paragraph_index > 0",
            name="ck_segments_paragraph_positive",
        ),
        sa.CheckConstraint(
            "table_index IS NULL OR table_index > 0",
            name="ck_segments_table_positive",
        ),
        sa.CheckConstraint(
            "row_start IS NULL OR row_start > 0",
            name="ck_segments_row_start_positive",
        ),
        sa.CheckConstraint("row_end IS NULL OR row_end >= row_start", name="ck_segments_row_range"),
        sa.CheckConstraint(
            "line_start IS NULL OR line_start > 0",
            name="ck_segments_line_start_positive",
        ),
        sa.CheckConstraint(
            "line_end IS NULL OR line_end >= line_start",
            name="ck_segments_line_range",
        ),
        sa.ForeignKeyConstraint(["extraction_id"], ["document_extractions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("extraction_id", "sequence", name="uq_segments_extraction_sequence"),
    )
    op.create_index(
        "ix_extracted_segments_extraction_id",
        "extracted_segments",
        ["extraction_id"],
    )
    op.create_index("ix_extracted_segments_page_number", "extracted_segments", ["page_number"])
    op.create_index("ix_extracted_segments_sheet_name", "extracted_segments", ["sheet_name"])
    op.create_index("ix_extracted_segments_segment_type", "extracted_segments", ["segment_type"])


def downgrade() -> None:
    op.drop_index("ix_extracted_segments_segment_type", table_name="extracted_segments")
    op.drop_index("ix_extracted_segments_sheet_name", table_name="extracted_segments")
    op.drop_index("ix_extracted_segments_page_number", table_name="extracted_segments")
    op.drop_index("ix_extracted_segments_extraction_id", table_name="extracted_segments")
    op.drop_table("extracted_segments")
    op.drop_index("uq_document_extractions_active_version", table_name="document_extractions")
    op.drop_index("ix_document_extractions_job_id", table_name="document_extractions")
    op.drop_index("ix_document_extractions_document_id", table_name="document_extractions")
    op.drop_table("document_extractions")
    op.drop_index("uq_processing_jobs_active_document_type", table_name="document_processing_jobs")
    op.drop_index("ix_processing_jobs_document_id", table_name="document_processing_jobs")
    op.drop_index("ix_processing_jobs_claim", table_name="document_processing_jobs")
    op.drop_table("document_processing_jobs")
    op.drop_index("ix_process_documents_processing_status", table_name="process_documents")
    op.drop_constraint(
        "ck_documents_processing_status",
        "process_documents",
        type_="check",
    )
    op.drop_column("process_documents", "processing_status")
