"""decision report package.

Revision ID: 20260704_0009
Revises: 142b8ab4f85d
Create Date: 2026-07-04 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260704_0009"
down_revision: str | None = "142b8ab4f85d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JOB_STATUS = (
    "status IN ('PENDING', 'PROCESSING', 'COMPLETED', "
    "'COMPLETED_WITH_WARNINGS', 'FAILED', 'CANCELLED')"
)
PACKAGE_STATUS = (
    "status IN ('DRAFT', 'GENERATING', 'COMPLETED', "
    "'COMPLETED_WITH_WARNINGS', 'FAILED', 'ARCHIVED')"
)
ARTIFACT_TYPE = (
    "artifact_type IN ('EXECUTIVE_HTML', 'EXECUTIVE_MARKDOWN', "
    "'REQUIREMENTS_MATRIX_JSON', 'REQUIREMENTS_MATRIX_CSV', "
    "'EVIDENCE_INDEX_JSON', 'ACTIONS_JSON', 'DECISION_MANIFEST_JSON', "
    "'PACKAGE_MANIFEST_JSON', 'PACKAGE_ZIP')"
)


def upgrade() -> None:
    op.create_table(
        "decision_report_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("process_id", sa.Uuid(), nullable=False),
        sa.Column("decision_run_id", sa.Uuid(), nullable=False),
        sa.Column("package_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column(
            "available_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.String(length=128), nullable=True),
        sa.Column("force", sa.Boolean(), nullable=False),
        sa.Column("last_error_code", sa.String(length=64), nullable=True),
        sa.Column("last_error_message", sa.String(length=1000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(JOB_STATUS, name="ck_decision_report_jobs_status"),
        sa.CheckConstraint("attempt_count >= 0", name="ck_decision_report_jobs_attempts"),
        sa.CheckConstraint("max_attempts > 0", name="ck_decision_report_jobs_max_attempts"),
        sa.CheckConstraint("priority >= 0", name="ck_decision_report_jobs_priority"),
        sa.ForeignKeyConstraint(["decision_run_id"], ["decision_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["process_id"], ["processes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_decision_report_jobs_claim",
        "decision_report_jobs",
        ["status", "available_at", "priority", "created_at"],
    )
    op.create_index(
        "ix_decision_report_jobs_decision_run", "decision_report_jobs", ["decision_run_id"]
    )
    op.create_index("ix_decision_report_jobs_process", "decision_report_jobs", ["process_id"])
    op.create_index(
        "uq_decision_report_jobs_active_run",
        "decision_report_jobs",
        ["decision_run_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('PENDING', 'PROCESSING')"),
    )

    op.create_table(
        "decision_report_packages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("process_id", sa.Uuid(), nullable=False),
        sa.Column("decision_run_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("package_version", sa.String(length=32), nullable=False),
        sa.Column("template_version", sa.String(length=32), nullable=False),
        sa.Column("input_manifest", sa.JSON(), nullable=False),
        sa.Column("input_digest", sa.String(length=64), nullable=False),
        sa.Column("package_digest", sa.String(length=64), nullable=True),
        sa.Column("artifact_count", sa.Integer(), nullable=False),
        sa.Column("warning_count", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(length=128), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.CheckConstraint(PACKAGE_STATUS, name="ck_decision_report_packages_status"),
        sa.CheckConstraint(
            "input_digest ~ '^[a-f0-9]{64}$'",
            name="ck_decision_report_packages_input_digest",
        ),
        sa.CheckConstraint(
            "package_digest IS NULL OR package_digest ~ '^[a-f0-9]{64}$'",
            name="ck_decision_report_packages_package_digest",
        ),
        sa.CheckConstraint(
            "artifact_count >= 0", name="ck_decision_report_packages_artifact_count"
        ),
        sa.CheckConstraint("warning_count >= 0", name="ck_decision_report_packages_warning_count"),
        sa.ForeignKeyConstraint(["decision_run_id"], ["decision_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["decision_report_jobs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["process_id"], ["processes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_decision_report_packages_created_at", "decision_report_packages", ["created_at"]
    )
    op.create_index(
        "ix_decision_report_packages_decision_run",
        "decision_report_packages",
        ["decision_run_id"],
    )
    op.create_index(
        "ix_decision_report_packages_idempotency",
        "decision_report_packages",
        ["decision_run_id", "input_digest"],
    )
    op.create_index(
        "ix_decision_report_packages_process", "decision_report_packages", ["process_id"]
    )
    op.create_index("ix_decision_report_packages_status", "decision_report_packages", ["status"])

    op.create_table(
        "decision_report_artifacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("package_id", sa.Uuid(), nullable=False),
        sa.Column("artifact_type", sa.String(length=64), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("storage_key", sa.String(length=700), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("template_version", sa.String(length=32), nullable=False),
        sa.Column("source_digest", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(ARTIFACT_TYPE, name="ck_decision_report_artifacts_type"),
        sa.CheckConstraint("size_bytes >= 0", name="ck_decision_report_artifacts_size"),
        sa.CheckConstraint("sha256 ~ '^[a-f0-9]{64}$'", name="ck_decision_report_artifacts_sha"),
        sa.CheckConstraint(
            "source_digest ~ '^[a-f0-9]{64}$'",
            name="ck_decision_report_artifacts_source_digest",
        ),
        sa.ForeignKeyConstraint(
            ["package_id"], ["decision_report_packages.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "package_id", "filename", name="uq_decision_report_artifacts_package_filename"
        ),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index(
        "ix_decision_report_artifacts_package", "decision_report_artifacts", ["package_id"]
    )

    op.create_table(
        "decision_report_sections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("package_id", sa.Uuid(), nullable=False),
        sa.Column("section_code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("summary_payload", sa.JSON(), nullable=False),
        sa.Column("warning_codes", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["package_id"], ["decision_report_packages.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("package_id", "section_code", name="uq_decision_report_sections_code"),
    )
    op.create_index(
        "ix_decision_report_sections_package",
        "decision_report_sections",
        ["package_id", "sequence"],
    )

    op.create_table(
        "decision_report_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=True),
        sa.Column("package_id", sa.Uuid(), nullable=True),
        sa.Column("process_id", sa.Uuid(), nullable=False),
        sa.Column("decision_run_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.String(length=1000), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["decision_run_id"], ["decision_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_id"], ["decision_report_jobs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["package_id"], ["decision_report_packages.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["process_id"], ["processes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_decision_report_events_job", "decision_report_events", ["job_id"])
    op.create_index("ix_decision_report_events_package", "decision_report_events", ["package_id"])
    op.create_index("ix_decision_report_events_type", "decision_report_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_decision_report_events_type", table_name="decision_report_events")
    op.drop_index("ix_decision_report_events_package", table_name="decision_report_events")
    op.drop_index("ix_decision_report_events_job", table_name="decision_report_events")
    op.drop_table("decision_report_events")
    op.drop_index("ix_decision_report_sections_package", table_name="decision_report_sections")
    op.drop_table("decision_report_sections")
    op.drop_index("ix_decision_report_artifacts_package", table_name="decision_report_artifacts")
    op.drop_table("decision_report_artifacts")
    op.drop_index("ix_decision_report_packages_status", table_name="decision_report_packages")
    op.drop_index("ix_decision_report_packages_process", table_name="decision_report_packages")
    op.drop_index("ix_decision_report_packages_idempotency", table_name="decision_report_packages")
    op.drop_index("ix_decision_report_packages_decision_run", table_name="decision_report_packages")
    op.drop_index("ix_decision_report_packages_created_at", table_name="decision_report_packages")
    op.drop_table("decision_report_packages")
    op.drop_index(
        "uq_decision_report_jobs_active_run",
        table_name="decision_report_jobs",
        postgresql_where=sa.text("status IN ('PENDING', 'PROCESSING')"),
    )
    op.drop_index("ix_decision_report_jobs_process", table_name="decision_report_jobs")
    op.drop_index("ix_decision_report_jobs_decision_run", table_name="decision_report_jobs")
    op.drop_index("ix_decision_report_jobs_claim", table_name="decision_report_jobs")
    op.drop_table("decision_report_jobs")
