"""requirement normalization

Revision ID: 20260702_0003
Revises: 20260702_0002
Create Date: 2026-07-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260702_0003"
down_revision: str | None = "20260702_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STATUS_VALUES = (
    "'PENDING', 'PROCESSING', 'COMPLETED', 'COMPLETED_WITH_WARNINGS', 'FAILED', 'CANCELLED'"
)


def upgrade() -> None:
    op.create_table(
        "prompt_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("prompt_name", sa.String(length=128), nullable=False),
        sa.Column("semantic_version", sa.String(length=32), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("system_content", sa.Text(), nullable=False),
        sa.Column("user_template_content", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.CheckConstraint("btrim(prompt_name) <> ''", name="ck_prompt_versions_name_not_blank"),
        sa.CheckConstraint(
            "content_sha256 ~ '^[a-f0-9]{64}$'",
            name="ck_prompt_versions_content_sha256",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_prompt_versions_identity",
        "prompt_versions",
        ["prompt_name", "semantic_version", "content_sha256"],
    )
    op.create_index(
        "ix_prompt_versions_name_active",
        "prompt_versions",
        ["prompt_name", "is_active"],
    )

    op.create_table(
        "requirement_normalization_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("process_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=True),
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
        sa.Column("force", sa.Boolean(), nullable=False),
        sa.Column("last_error_code", sa.String(length=64), nullable=True),
        sa.Column("last_error_message", sa.String(length=1000), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            f"status IN ({STATUS_VALUES})",
            name="ck_requirement_normalization_jobs_status",
        ),
        sa.CheckConstraint(
            "priority >= 0",
            name="ck_requirement_normalization_jobs_priority_nonnegative",
        ),
        sa.CheckConstraint(
            "attempt_count >= 0",
            name="ck_requirement_normalization_jobs_attempt_nonnegative",
        ),
        sa.CheckConstraint(
            "max_attempts > 0",
            name="ck_requirement_normalization_jobs_max_attempts_positive",
        ),
        sa.ForeignKeyConstraint(["process_id"], ["processes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_requirement_normalization_jobs_claim",
        "requirement_normalization_jobs",
        ["status", "available_at", "priority", "created_at"],
    )
    op.create_index(
        "ix_requirement_normalization_jobs_process_id",
        "requirement_normalization_jobs",
        ["process_id"],
    )
    op.create_index(
        "ix_requirement_normalization_jobs_run_id",
        "requirement_normalization_jobs",
        ["run_id"],
    )
    op.create_index(
        "uq_requirement_normalization_active_process",
        "requirement_normalization_jobs",
        ["process_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('PENDING', 'PROCESSING')"),
    )

    op.create_table(
        "requirement_normalization_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("process_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("reasoning_effort", sa.String(length=32), nullable=False),
        sa.Column("prompt_version_id", sa.Uuid(), nullable=False),
        sa.Column("consolidation_prompt_version_id", sa.Uuid(), nullable=False),
        sa.Column("input_manifest", sa.JSON(), nullable=False),
        sa.Column("input_digest", sa.String(length=64), nullable=False),
        sa.Column("source_extraction_ids", sa.JSON(), nullable=False),
        sa.Column("segment_count", sa.Integer(), nullable=False),
        sa.Column("batch_count", sa.Integer(), nullable=False),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column("accepted_requirement_count", sa.Integer(), nullable=False),
        sa.Column("rejected_candidate_count", sa.Integer(), nullable=False),
        sa.Column("warning_count", sa.Integer(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("reasoning_tokens", sa.Integer(), nullable=False),
        sa.Column("provider_response_ids", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            f"status IN ({STATUS_VALUES})",
            name="ck_requirement_normalization_runs_status",
        ),
        sa.CheckConstraint(
            "provider IN ('openai', 'fake')",
            name="ck_requirement_normalization_runs_provider",
        ),
        sa.CheckConstraint("segment_count >= 0", name="ck_requirement_normalization_runs_segments"),
        sa.CheckConstraint("batch_count >= 0", name="ck_requirement_normalization_runs_batches"),
        sa.CheckConstraint(
            "candidate_count >= 0", name="ck_requirement_normalization_runs_candidates"
        ),
        sa.CheckConstraint(
            "accepted_requirement_count >= 0",
            name="ck_requirement_normalization_runs_accepted",
        ),
        sa.CheckConstraint(
            "rejected_candidate_count >= 0",
            name="ck_requirement_normalization_runs_rejected",
        ),
        sa.CheckConstraint("warning_count >= 0", name="ck_requirement_normalization_runs_warnings"),
        sa.CheckConstraint(
            "input_tokens >= 0", name="ck_requirement_normalization_runs_input_tokens"
        ),
        sa.CheckConstraint(
            "output_tokens >= 0", name="ck_requirement_normalization_runs_output_tokens"
        ),
        sa.CheckConstraint(
            "reasoning_tokens >= 0",
            name="ck_requirement_normalization_runs_reasoning_tokens",
        ),
        sa.CheckConstraint(
            "input_digest ~ '^[a-f0-9]{64}$'",
            name="ck_requirement_normalization_runs_input_digest",
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["requirement_normalization_jobs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["process_id"], ["processes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["prompt_version_id"], ["prompt_versions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["consolidation_prompt_version_id"], ["prompt_versions.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_requirement_normalization_runs_created_at",
        "requirement_normalization_runs",
        ["created_at"],
    )
    op.create_index(
        "ix_requirement_normalization_runs_input_digest",
        "requirement_normalization_runs",
        ["process_id", "input_digest"],
    )
    op.create_index(
        "ix_requirement_normalization_runs_job_id",
        "requirement_normalization_runs",
        ["job_id"],
    )
    op.create_index(
        "ix_requirement_normalization_runs_process_id",
        "requirement_normalization_runs",
        ["process_id"],
    )

    op.create_table(
        "requirement_normalization_batches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("batch_index", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("segment_ids", sa.JSON(), nullable=False),
        sa.Column("input_digest", sa.String(length=64), nullable=False),
        sa.Column("provider_response_id", sa.String(length=128), nullable=True),
        sa.Column("structured_output", sa.JSON(), nullable=True),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("reasoning_tokens", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            f"status IN ({STATUS_VALUES})",
            name="ck_requirement_normalization_batches_status",
        ),
        sa.CheckConstraint("batch_index >= 0", name="ck_requirement_batches_index_nonnegative"),
        sa.CheckConstraint("candidate_count >= 0", name="ck_requirement_batches_candidates"),
        sa.CheckConstraint("input_tokens >= 0", name="ck_requirement_batches_input_tokens"),
        sa.CheckConstraint("output_tokens >= 0", name="ck_requirement_batches_output_tokens"),
        sa.CheckConstraint("reasoning_tokens >= 0", name="ck_requirement_batches_reasoning_tokens"),
        sa.CheckConstraint("input_digest ~ '^[a-f0-9]{64}$'", name="ck_requirement_batches_digest"),
        sa.ForeignKeyConstraint(
            ["run_id"], ["requirement_normalization_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "batch_index", name="uq_requirement_batches_run_index"),
    )
    op.create_index(
        "ix_requirement_normalization_batches_run_id",
        "requirement_normalization_batches",
        ["run_id"],
    )
    op.create_index(
        "ix_requirement_normalization_batches_run_order",
        "requirement_normalization_batches",
        ["run_id", "batch_index"],
    )

    op.create_table(
        "requirements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("process_id", sa.Uuid(), nullable=False),
        sa.Column("normalization_run_id", sa.Uuid(), nullable=False),
        sa.Column("stable_key", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("scope", sa.String(length=64), nullable=False),
        sa.Column("modality", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("condition_text", sa.Text(), nullable=True),
        sa.Column("expected_value", sa.JSON(), nullable=True),
        sa.Column("criticality", sa.String(length=32), nullable=False),
        sa.Column("criticality_basis", sa.String(length=32), nullable=False),
        sa.Column("subsanability", sa.String(length=32), nullable=False),
        sa.Column("subsanability_basis", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("evidence_status", sa.String(length=32), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("requires_human_review", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "category IN ('LEGAL', 'FINANCIAL', 'ORGANIZATIONAL', 'EXPERIENCE', 'TECHNICAL', "
            "'WORKFORCE', 'GUARANTEE', 'SCHEDULE', 'ECONOMIC', 'OPERATIONAL', 'DOCUMENTARY', "
            "'RISK_AND_INELIGIBILITY')",
            name="ck_requirements_category",
        ),
        sa.CheckConstraint(
            "scope IN ('PROPOSAL_SUBMISSION', 'HABILITATING', 'SCORING', 'CONTRACT_EXECUTION', "
            "'INFORMATIONAL', 'UNKNOWN')",
            name="ck_requirements_scope",
        ),
        sa.CheckConstraint(
            "modality IN ('MANDATORY', 'OPTIONAL', 'CONDITIONAL', 'PROHIBITED', 'UNKNOWN')",
            name="ck_requirements_modality",
        ),
        sa.CheckConstraint(
            "criticality IN ('BLOCKING', 'HIGH', 'MEDIUM', 'LOW', 'INFORMATIONAL', 'UNKNOWN')",
            name="ck_requirements_criticality",
        ),
        sa.CheckConstraint(
            "criticality_basis IN ('EXPLICIT', 'INFERRED', 'UNKNOWN')",
            name="ck_requirements_criticality_basis",
        ),
        sa.CheckConstraint(
            "subsanability IN ('SUBSANABLE', 'NON_SUBSANABLE', 'CONDITIONAL', 'UNKNOWN')",
            name="ck_requirements_subsanability",
        ),
        sa.CheckConstraint(
            "subsanability_basis IN ('EXPLICIT', 'INFERRED', 'UNKNOWN')",
            name="ck_requirements_subsanability_basis",
        ),
        sa.CheckConstraint(
            "evidence_status IN ('VALIDATED', 'PARTIALLY_VALIDATED', "
            "'REJECTED_UNSUPPORTED', 'UNKNOWN')",
            name="ck_requirements_evidence_status",
        ),
        sa.CheckConstraint(
            "review_status IN ('PENDING', 'IN_REVIEW', 'ACCEPTED', 'REJECTED')",
            name="ck_requirements_review_status",
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="ck_requirements_confidence"
        ),
        sa.CheckConstraint("stable_key ~ '^[a-f0-9]{64}$'", name="ck_requirements_stable_key"),
        sa.CheckConstraint(
            "btrim(description) <> ''", name="ck_requirements_description_not_blank"
        ),
        sa.ForeignKeyConstraint(["process_id"], ["processes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["normalization_run_id"], ["requirement_normalization_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "normalization_run_id", "stable_key", name="uq_requirements_run_stable_key"
        ),
    )
    op.create_index("ix_requirements_category", "requirements", ["category"])
    op.create_index("ix_requirements_process_id", "requirements", ["process_id"])
    op.create_index("ix_requirements_review_status", "requirements", ["review_status"])
    op.create_index("ix_requirements_run_id", "requirements", ["normalization_run_id"])
    op.create_index("ix_requirements_stable_key", "requirements", ["stable_key"])

    op.create_table(
        "rejected_requirement_candidates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=True),
        sa.Column("candidate_id", sa.String(length=128), nullable=True),
        sa.Column("rejection_reason", sa.String(length=64), nullable=False),
        sa.Column("rejection_message", sa.String(length=1000), nullable=False),
        sa.Column("raw_candidate", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "rejection_reason IN ('SCHEMA_INVALID', 'REJECTED_UNSUPPORTED', 'INVALID_SEGMENT', "
            "'QUOTE_NOT_FOUND', 'OUTSIDE_SNAPSHOT', 'LOCATION_MISMATCH', 'FORBIDDEN_DECISION', "
            "'EXACT_DUPLICATE')",
            name="ck_rejected_requirement_candidates_reason",
        ),
        sa.ForeignKeyConstraint(
            ["batch_id"], ["requirement_normalization_batches.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["run_id"], ["requirement_normalization_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_rejected_candidates_batch_id", "rejected_requirement_candidates", ["batch_id"]
    )
    op.create_index("ix_rejected_candidates_run_id", "rejected_requirement_candidates", ["run_id"])

    op.create_table(
        "requirement_relations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("process_id", sa.Uuid(), nullable=False),
        sa.Column("normalization_run_id", sa.Uuid(), nullable=False),
        sa.Column("source_requirement_id", sa.Uuid(), nullable=False),
        sa.Column("target_requirement_id", sa.Uuid(), nullable=False),
        sa.Column("relation_type", sa.String(length=64), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("requires_human_review", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "relation_type IN ('INDEPENDENT', 'EXACT_DUPLICATE', 'POTENTIAL_DUPLICATE', "
            "'POTENTIAL_CONFLICT', 'POTENTIAL_AMENDMENT')",
            name="ck_requirement_relations_type",
        ),
        sa.CheckConstraint(
            "source_requirement_id <> target_requirement_id",
            name="ck_requirement_relations_not_self",
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_requirement_relations_confidence",
        ),
        sa.ForeignKeyConstraint(["process_id"], ["processes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["normalization_run_id"], ["requirement_normalization_runs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["source_requirement_id"], ["requirements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_requirement_id"], ["requirements.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "normalization_run_id",
            "source_requirement_id",
            "target_requirement_id",
            "relation_type",
            name="uq_requirement_relations_unique",
        ),
    )
    op.create_index("ix_requirement_relations_process_id", "requirement_relations", ["process_id"])
    op.create_index(
        "ix_requirement_relations_run_id", "requirement_relations", ["normalization_run_id"]
    )
    op.create_index(
        "ix_requirement_relations_source", "requirement_relations", ["source_requirement_id"]
    )
    op.create_index(
        "ix_requirement_relations_target", "requirement_relations", ["target_requirement_id"]
    )

    op.create_table(
        "requirement_evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("requirement_id", sa.Uuid(), nullable=False),
        sa.Column("extraction_id", sa.Uuid(), nullable=False),
        sa.Column("segment_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_role", sa.String(length=32), nullable=False),
        sa.Column("quoted_text", sa.Text(), nullable=False),
        sa.Column("quote_start", sa.Integer(), nullable=True),
        sa.Column("quote_end", sa.Integer(), nullable=True),
        sa.Column("source_location", sa.JSON(), nullable=False),
        sa.Column("validation_status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "evidence_role IN ('PRIMARY', 'SUPPORTING', 'CONFLICTING')",
            name="ck_requirement_evidence_role",
        ),
        sa.CheckConstraint(
            "validation_status IN ('VALID', 'INVALID_SEGMENT', 'QUOTE_NOT_FOUND', "
            "'OUTSIDE_SNAPSHOT', 'LOCATION_MISMATCH')",
            name="ck_requirement_evidence_validation_status",
        ),
        sa.CheckConstraint(
            "btrim(quoted_text) <> ''", name="ck_requirement_evidence_quote_not_blank"
        ),
        sa.CheckConstraint(
            "quote_start IS NULL OR quote_start >= 0",
            name="ck_requirement_evidence_quote_start",
        ),
        sa.CheckConstraint(
            "quote_end IS NULL OR quote_start IS NULL OR quote_end >= quote_start",
            name="ck_requirement_evidence_quote_range",
        ),
        sa.ForeignKeyConstraint(["extraction_id"], ["document_extractions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["segment_id"], ["extracted_segments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_requirement_evidence_requirement_id", "requirement_evidence", ["requirement_id"]
    )
    op.create_index("ix_requirement_evidence_segment_id", "requirement_evidence", ["segment_id"])


def downgrade() -> None:
    op.drop_index("ix_requirement_evidence_segment_id", table_name="requirement_evidence")
    op.drop_index("ix_requirement_evidence_requirement_id", table_name="requirement_evidence")
    op.drop_table("requirement_evidence")
    op.drop_index("ix_requirement_relations_target", table_name="requirement_relations")
    op.drop_index("ix_requirement_relations_source", table_name="requirement_relations")
    op.drop_index("ix_requirement_relations_run_id", table_name="requirement_relations")
    op.drop_index("ix_requirement_relations_process_id", table_name="requirement_relations")
    op.drop_table("requirement_relations")
    op.drop_index("ix_rejected_candidates_run_id", table_name="rejected_requirement_candidates")
    op.drop_index("ix_rejected_candidates_batch_id", table_name="rejected_requirement_candidates")
    op.drop_table("rejected_requirement_candidates")
    op.drop_index("ix_requirements_stable_key", table_name="requirements")
    op.drop_index("ix_requirements_run_id", table_name="requirements")
    op.drop_index("ix_requirements_review_status", table_name="requirements")
    op.drop_index("ix_requirements_process_id", table_name="requirements")
    op.drop_index("ix_requirements_category", table_name="requirements")
    op.drop_table("requirements")
    op.drop_index(
        "ix_requirement_normalization_batches_run_order",
        table_name="requirement_normalization_batches",
    )
    op.drop_index(
        "ix_requirement_normalization_batches_run_id",
        table_name="requirement_normalization_batches",
    )
    op.drop_table("requirement_normalization_batches")
    op.drop_index(
        "ix_requirement_normalization_runs_process_id",
        table_name="requirement_normalization_runs",
    )
    op.drop_index(
        "ix_requirement_normalization_runs_job_id",
        table_name="requirement_normalization_runs",
    )
    op.drop_index(
        "ix_requirement_normalization_runs_input_digest",
        table_name="requirement_normalization_runs",
    )
    op.drop_index(
        "ix_requirement_normalization_runs_created_at",
        table_name="requirement_normalization_runs",
    )
    op.drop_table("requirement_normalization_runs")
    op.drop_index(
        "uq_requirement_normalization_active_process",
        table_name="requirement_normalization_jobs",
    )
    op.drop_index(
        "ix_requirement_normalization_jobs_run_id",
        table_name="requirement_normalization_jobs",
    )
    op.drop_index(
        "ix_requirement_normalization_jobs_process_id",
        table_name="requirement_normalization_jobs",
    )
    op.drop_index(
        "ix_requirement_normalization_jobs_claim",
        table_name="requirement_normalization_jobs",
    )
    op.drop_table("requirement_normalization_jobs")
    op.drop_index("ix_prompt_versions_name_active", table_name="prompt_versions")
    op.drop_index("ix_prompt_versions_identity", table_name="prompt_versions")
    op.drop_table("prompt_versions")
