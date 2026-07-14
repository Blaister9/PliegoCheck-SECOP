"""persist incremental SECOP document synchronization.

Revision ID: 20260713_0019
Revises: 20260713_0018
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260713_0019"
down_revision: str | None = "20260713_0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        )
    ]


def upgrade() -> None:
    op.create_table(
        "external_process_sync_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "process_id",
            sa.Uuid(),
            sa.ForeignKey("processes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "external_process_link_id",
            sa.Uuid(),
            sa.ForeignKey("external_procurement_process_links.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_system", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("input_digest", sa.String(64), nullable=False),
        sa.Column("discover_documents", sa.Boolean(), nullable=False),
        sa.Column("metadata_changed", sa.Boolean(), server_default=sa.false(), nullable=False),
        *[
            sa.Column(name, sa.Integer(), server_default="0", nullable=False)
            for name in (
                "documents_discovered",
                "documents_added",
                "documents_updated",
                "documents_unchanged",
                "documents_failed",
            )
        ],
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("error_code", sa.String(64)),
        sa.Column("error_message", sa.String(500)),
        sa.Column("source_updated_at", sa.DateTime(timezone=True)),
        sa.Column(
            "available_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("locked_at", sa.DateTime(timezone=True)),
        sa.Column("locked_by", sa.String(255)),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="3", nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("auth_users.id", ondelete="SET NULL")),
        *timestamps(),
        sa.CheckConstraint(
            "status IN ('PENDING','PROCESSING','COMPLETED','COMPLETED_WITH_WARNINGS',"
            "'FAILED','CANCELLED')",
            name="ck_external_sync_runs_status",
        ),
    )
    op.create_index(
        "ix_external_sync_runs_claim",
        "external_process_sync_runs",
        ["status", "available_at", "created_at"],
    )
    op.create_index(
        "ix_external_sync_runs_process", "external_process_sync_runs", ["process_id", "created_at"]
    )
    op.create_index(
        "uq_external_sync_runs_active",
        "external_process_sync_runs",
        ["process_id", "external_process_link_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('PENDING', 'PROCESSING')"),
    )
    op.create_table(
        "external_process_snapshots",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "process_id",
            sa.Uuid(),
            sa.ForeignKey("processes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sync_run_id",
            sa.Uuid(),
            sa.ForeignKey("external_process_sync_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_system", sa.String(32), nullable=False),
        sa.Column("source_process_id", sa.String(500), nullable=False),
        sa.Column("source_reference", sa.String(500)),
        sa.Column("source_status", sa.String(500)),
        sa.Column("source_publication_date", sa.DateTime(timezone=True)),
        sa.Column("source_closing_date", sa.DateTime(timezone=True)),
        sa.Column("source_estimated_value", sa.Numeric(24, 2)),
        sa.Column("source_currency", sa.String(3)),
        sa.Column("source_updated_at", sa.DateTime(timezone=True)),
        sa.Column("normalized_payload", sa.JSON(), nullable=False),
        sa.Column("raw_payload_hash", sa.String(64), nullable=False),
        sa.Column(
            "captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("sync_run_id", name="uq_external_process_snapshots_run"),
    )
    op.create_index(
        "ix_external_process_snapshots_process",
        "external_process_snapshots",
        ["process_id", "captured_at"],
    )
    op.create_table(
        "external_process_documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "process_id",
            sa.Uuid(),
            sa.ForeignKey("processes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "external_process_link_id",
            sa.Uuid(),
            sa.ForeignKey("external_procurement_process_links.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_system", sa.String(32), nullable=False),
        sa.Column("source_document_id", sa.String(500), nullable=False),
        sa.Column("source_document_reference", sa.String(500)),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("document_type", sa.String(255)),
        sa.Column("document_category", sa.String(255)),
        sa.Column("source_url", sa.String(2083)),
        sa.Column("source_public_url", sa.String(2083)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at_source", sa.DateTime(timezone=True)),
        sa.Column("reported_size_bytes", sa.Integer()),
        sa.Column("reported_content_type", sa.String(255)),
        sa.Column("discovery_status", sa.String(32), nullable=False),
        sa.Column("download_status", sa.String(32), nullable=False),
        sa.Column("addendum_status", sa.String(32), nullable=False),
        sa.Column("requires_human_review", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("current_version_id", sa.Uuid()),
        sa.Column("version_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        *timestamps(),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "process_id",
            "source_system",
            "source_document_id",
            name="uq_external_documents_source_key",
        ),
        sa.CheckConstraint(
            "discovery_status IN ('DISCOVERED','LINK_AVAILABLE','METADATA_ONLY',"
            "'UNSUPPORTED','MISSING','ERROR')",
            name="ck_external_documents_discovery",
        ),
        sa.CheckConstraint(
            "download_status IN ('NOT_REQUESTED','PENDING','DOWNLOADING','DOWNLOADED',"
            "'UNCHANGED','UPDATED','UNSUPPORTED','FAILED','REJECTED')",
            name="ck_external_documents_download",
        ),
        sa.CheckConstraint(
            "addendum_status IN ('CONFIRMED_ADDENDUM','POTENTIAL_ADDENDUM',"
            "'NOT_ADDENDUM','UNKNOWN')",
            name="ck_external_documents_addendum",
        ),
    )
    op.create_index(
        "ix_external_documents_process",
        "external_process_documents",
        ["process_id", "last_seen_at"],
    )
    op.create_table(
        "external_process_document_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "external_document_id",
            sa.Uuid(),
            sa.ForeignKey("external_process_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.String(2083)),
        sa.Column("source_updated_at", sa.DateTime(timezone=True)),
        sa.Column("reported_size_bytes", sa.Integer()),
        sa.Column("reported_content_type", sa.String(255)),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("detected_content_type", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(700), nullable=False),
        sa.Column("downloaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "process_document_id",
            sa.Uuid(),
            sa.ForeignKey("process_documents.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "previous_version_id",
            sa.Uuid(),
            sa.ForeignKey("external_process_document_versions.id", ondelete="SET NULL"),
        ),
        *timestamps(),
        sa.UniqueConstraint(
            "external_document_id", "sha256", name="uq_external_document_versions_hash"
        ),
        sa.UniqueConstraint(
            "external_document_id", "version_number", name="uq_external_document_versions_number"
        ),
    )
    op.create_index(
        "ix_external_document_versions_document",
        "external_process_document_versions",
        ["external_document_id", "version_number"],
    )
    op.create_table(
        "external_process_change_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "process_id",
            sa.Uuid(),
            sa.ForeignKey("processes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sync_run_id",
            sa.Uuid(),
            sa.ForeignKey("external_process_sync_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column(
            "external_document_id",
            sa.Uuid(),
            sa.ForeignKey("external_process_documents.id", ondelete="SET NULL"),
        ),
        sa.Column("old_value", sa.Text()),
        sa.Column("new_value", sa.Text()),
        sa.Column("metadata", sa.JSON(), nullable=False),
        *timestamps(),
        sa.CheckConstraint(
            "event_type IN ('PROCESS_STATUS_CHANGED','CLOSING_DATE_CHANGED',"
            "'ESTIMATED_VALUE_CHANGED','DOCUMENT_DISCOVERED','DOCUMENT_UPDATED',"
            "'DOCUMENT_REMOVED_FROM_SOURCE','POTENTIAL_ADDENDUM_DISCOVERED',"
            "'CONFIRMED_ADDENDUM_DISCOVERED','DOWNLOAD_FAILED')",
            name="ck_external_change_events_type",
        ),
    )
    op.create_index(
        "ix_external_change_events_process",
        "external_process_change_events",
        ["process_id", "created_at"],
    )
    op.create_table(
        "external_document_download_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "external_document_id",
            sa.Uuid(),
            sa.ForeignKey("external_process_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column(
            "available_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("locked_at", sa.DateTime(timezone=True)),
        sa.Column("locked_by", sa.String(255)),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="3", nullable=False),
        sa.Column("error_code", sa.String(64)),
        sa.Column("error_message", sa.String(500)),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("auth_users.id", ondelete="SET NULL")),
        *timestamps(),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "status IN ('NOT_REQUESTED','PENDING','DOWNLOADING','DOWNLOADED',"
            "'UNCHANGED','UPDATED','UNSUPPORTED','FAILED','REJECTED')",
            name="ck_external_download_jobs_status",
        ),
    )
    op.create_index(
        "ix_external_download_jobs_claim",
        "external_document_download_jobs",
        ["status", "available_at", "created_at"],
    )
    op.create_index(
        "uq_external_download_jobs_active",
        "external_document_download_jobs",
        ["external_document_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('PENDING', 'DOWNLOADING')"),
    )


def downgrade() -> None:
    for table in (
        "external_document_download_jobs",
        "external_process_change_events",
        "external_process_document_versions",
        "external_process_documents",
        "external_process_snapshots",
        "external_process_sync_runs",
    ):
        op.drop_table(table)
