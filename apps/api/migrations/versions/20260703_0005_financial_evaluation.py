"""financial evaluation.

Revision ID: 20260703_0005
Revises: 20260702_0004
Create Date: 2026-07-03 00:00:00.000000
"""

# ruff: noqa: E501

from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision: str = "20260703_0005"
down_revision: str | None = "20260702_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


JOB_STATUS = (
    "'PENDING', 'PROCESSING', 'COMPLETED', 'COMPLETED_WITH_WARNINGS', 'FAILED', 'CANCELLED'"
)
RESULT_STATUS = (
    "'COMPLIES', 'DOES_NOT_COMPLY', 'PARTIAL', 'UNKNOWN', 'NOT_APPLICABLE', 'CONFLICTING_EVIDENCE'"
)
REVIEW_STATUS = "'PENDING', 'CONFIRMED', 'OVERRIDDEN', 'REJECTED'"
RULE_TYPES = "'DIRECT_METRIC', 'DERIVED_METRIC', 'RANGE', 'COMPOSITE_ALL', 'COMPOSITE_ANY', 'INFORMATIONAL', 'UNSUPPORTED'"
MAPPING_STATUS = "'MAPPED', 'PARTIALLY_MAPPED', 'AMBIGUOUS', 'UNSUPPORTED', 'INVALID'"
OPERATORS = "'GREATER_THAN', 'GREATER_THAN_OR_EQUAL', 'LESS_THAN', 'LESS_THAN_OR_EQUAL', 'EQUAL', 'NOT_EQUAL', 'BETWEEN_INCLUSIVE', 'BETWEEN_EXCLUSIVE', 'EXISTS', 'NOT_EXISTS'"
PERIOD_POLICIES = "'EXACT_YEAR', 'LATEST_AVAILABLE', 'LATEST_BEFORE_PROCESS_CLOSING', 'RUP_REFERENCE_PERIOD', 'MANUAL_SELECTION', 'UNKNOWN'"
SOURCE_BASES = "'EXPLICIT_EXPECTED_VALUE', 'EXPLICIT_DESCRIPTION', 'MANUAL_OVERRIDE', 'UNKNOWN'"
CALC_STATUS = "'COMPLETED', 'MISSING_INPUT', 'DIVISION_BY_ZERO', 'UNIT_MISMATCH', 'CURRENCY_MISMATCH', 'CONFLICTING_INPUT', 'FAILED'"
METRICS = "'CURRENT_ASSETS', 'CURRENT_LIABILITIES', 'TOTAL_ASSETS', 'TOTAL_LIABILITIES', 'EQUITY', 'REVENUE', 'OPERATING_PROFIT', 'NET_PROFIT', 'INTEREST_EXPENSE', 'WORKING_CAPITAL', 'LIQUIDITY_RATIO', 'DEBT_RATIO', 'INTEREST_COVERAGE', 'RETURN_ON_ASSETS', 'RETURN_ON_EQUITY', 'OTHER'"


def upgrade() -> None:
    op.create_table(
        "financial_formula_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("formula_name", sa.String(length=128), nullable=False),
        sa.Column("semantic_version", sa.String(length=32), nullable=False),
        sa.Column("expression", sa.Text(), nullable=False),
        sa.Column("required_metric_types", sa.JSON(), nullable=False),
        sa.Column("output_metric_type", sa.String(length=64), nullable=False),
        sa.Column("output_unit", sa.String(length=64), nullable=True),
        sa.Column("rounding_policy", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.CheckConstraint("btrim(formula_name) <> ''", name="ck_financial_formula_versions_name"),
        sa.CheckConstraint(
            "btrim(semantic_version) <> ''", name="ck_financial_formula_versions_version"
        ),
        sa.CheckConstraint(
            "btrim(expression) <> ''", name="ck_financial_formula_versions_expression"
        ),
        sa.CheckConstraint(
            f"output_metric_type IN ({METRICS})", name="ck_financial_formula_versions_output_metric"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "formula_name", "semantic_version", name="uq_financial_formula_versions_name_version"
        ),
    )
    op.create_index(
        "ix_financial_formula_versions_active",
        "financial_formula_versions",
        ["formula_name", "is_active"],
    )
    op.bulk_insert(
        sa.table(
            "financial_formula_versions",
            sa.column("id", sa.Uuid),
            sa.column("formula_name", sa.String),
            sa.column("semantic_version", sa.String),
            sa.column("expression", sa.Text),
            sa.column("required_metric_types", sa.JSON),
            sa.column("output_metric_type", sa.String),
            sa.column("output_unit", sa.String),
            sa.column("rounding_policy", sa.String),
            sa.column("is_active", sa.Boolean),
        ),
        [
            {
                "id": UUID("00000000-0000-6000-8000-000000000001"),
                "formula_name": "WORKING_CAPITAL",
                "semantic_version": "1.0.0",
                "expression": "CURRENT_ASSETS - CURRENT_LIABILITIES",
                "required_metric_types": ["CURRENT_ASSETS", "CURRENT_LIABILITIES"],
                "output_metric_type": "WORKING_CAPITAL",
                "output_unit": "COP",
                "rounding_policy": "ROUND_HALF_UP:2",
                "is_active": True,
            },
            {
                "id": UUID("00000000-0000-6000-8000-000000000002"),
                "formula_name": "LIQUIDITY_RATIO",
                "semantic_version": "1.0.0",
                "expression": "CURRENT_ASSETS / CURRENT_LIABILITIES",
                "required_metric_types": ["CURRENT_ASSETS", "CURRENT_LIABILITIES"],
                "output_metric_type": "LIQUIDITY_RATIO",
                "output_unit": "ratio",
                "rounding_policy": "ROUND_HALF_UP:6",
                "is_active": True,
            },
            {
                "id": UUID("00000000-0000-6000-8000-000000000003"),
                "formula_name": "DEBT_RATIO",
                "semantic_version": "1.0.0",
                "expression": "TOTAL_LIABILITIES / TOTAL_ASSETS",
                "required_metric_types": ["TOTAL_LIABILITIES", "TOTAL_ASSETS"],
                "output_metric_type": "DEBT_RATIO",
                "output_unit": "ratio",
                "rounding_policy": "ROUND_HALF_UP:6",
                "is_active": True,
            },
            {
                "id": UUID("00000000-0000-6000-8000-000000000004"),
                "formula_name": "INTEREST_COVERAGE",
                "semantic_version": "1.0.0",
                "expression": "OPERATING_PROFIT / INTEREST_EXPENSE",
                "required_metric_types": ["OPERATING_PROFIT", "INTEREST_EXPENSE"],
                "output_metric_type": "INTEREST_COVERAGE",
                "output_unit": "ratio",
                "rounding_policy": "ROUND_HALF_UP:6",
                "is_active": True,
            },
            {
                "id": UUID("00000000-0000-6000-8000-000000000005"),
                "formula_name": "RETURN_ON_ASSETS",
                "semantic_version": "1.0.0",
                "expression": "NET_PROFIT / TOTAL_ASSETS",
                "required_metric_types": ["NET_PROFIT", "TOTAL_ASSETS"],
                "output_metric_type": "RETURN_ON_ASSETS",
                "output_unit": "ratio",
                "rounding_policy": "ROUND_HALF_UP:6",
                "is_active": True,
            },
            {
                "id": UUID("00000000-0000-6000-8000-000000000006"),
                "formula_name": "RETURN_ON_EQUITY",
                "semantic_version": "1.0.0",
                "expression": "NET_PROFIT / EQUITY",
                "required_metric_types": ["NET_PROFIT", "EQUITY"],
                "output_metric_type": "RETURN_ON_EQUITY",
                "output_unit": "ratio",
                "rounding_policy": "ROUND_HALF_UP:6",
                "is_active": True,
            },
        ],
    )

    op.create_table(
        "financial_requirement_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("requirement_id", sa.Uuid(), nullable=False),
        sa.Column("normalization_run_id", sa.Uuid(), nullable=False),
        sa.Column("rule_type", sa.String(length=64), nullable=False),
        sa.Column("metric_type", sa.String(length=64), nullable=True),
        sa.Column("operator", sa.String(length=64), nullable=True),
        sa.Column("required_value", sa.Numeric(28, 8), nullable=True),
        sa.Column("required_min_value", sa.Numeric(28, 8), nullable=True),
        sa.Column("required_max_value", sa.Numeric(28, 8), nullable=True),
        sa.Column("unit", sa.String(length=64), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("period_policy", sa.String(length=64), nullable=False),
        sa.Column("period_year", sa.Integer(), nullable=True),
        sa.Column("condition_group", sa.JSON(), nullable=False),
        sa.Column("source_basis", sa.String(length=64), nullable=False),
        sa.Column("mapping_status", sa.String(length=64), nullable=False),
        sa.Column("mapping_warnings", sa.JSON(), nullable=False),
        sa.Column("requires_human_review", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_manual_override", sa.Boolean(), nullable=False),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            f"rule_type IN ({RULE_TYPES})", name="ck_financial_requirement_rules_type"
        ),
        sa.CheckConstraint(
            f"metric_type IS NULL OR metric_type IN ({METRICS})",
            name="ck_financial_requirement_rules_metric",
        ),
        sa.CheckConstraint(
            f"operator IS NULL OR operator IN ({OPERATORS})",
            name="ck_financial_requirement_rules_operator",
        ),
        sa.CheckConstraint(
            f"period_policy IN ({PERIOD_POLICIES})",
            name="ck_financial_requirement_rules_period_policy",
        ),
        sa.CheckConstraint(
            f"source_basis IN ({SOURCE_BASES})", name="ck_financial_requirement_rules_source_basis"
        ),
        sa.CheckConstraint(
            f"mapping_status IN ({MAPPING_STATUS})",
            name="ck_financial_requirement_rules_mapping_status",
        ),
        sa.CheckConstraint("version > 0", name="ck_financial_requirement_rules_version_positive"),
        sa.ForeignKeyConstraint(
            ["normalization_run_id"], ["requirement_normalization_runs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "normalization_run_id",
            "requirement_id",
            "version",
            name="uq_financial_requirement_rules_version",
        ),
    )
    op.create_index(
        "ix_financial_requirement_rules_requirement_id",
        "financial_requirement_rules",
        ["requirement_id"],
    )
    op.create_index(
        "ix_financial_requirement_rules_run_id",
        "financial_requirement_rules",
        ["normalization_run_id"],
    )
    op.create_index(
        "ix_financial_requirement_rules_latest",
        "financial_requirement_rules",
        ["normalization_run_id", "requirement_id", "version"],
    )

    op.create_table(
        "financial_evaluation_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("process_id", sa.Uuid(), nullable=False),
        sa.Column("normalization_run_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("company_profile_snapshot_id", sa.Uuid(), nullable=False),
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
        sa.CheckConstraint(f"status IN ({JOB_STATUS})", name="ck_financial_evaluation_jobs_status"),
        sa.CheckConstraint("priority >= 0", name="ck_financial_evaluation_jobs_priority"),
        sa.CheckConstraint("attempt_count >= 0", name="ck_financial_evaluation_jobs_attempts"),
        sa.CheckConstraint("max_attempts > 0", name="ck_financial_evaluation_jobs_max_attempts"),
        sa.ForeignKeyConstraint(["company_id"], ["company_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["company_profile_snapshot_id"], ["company_profile_snapshots.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["normalization_run_id"], ["requirement_normalization_runs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["process_id"], ["processes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_financial_evaluation_jobs_claim",
        "financial_evaluation_jobs",
        ["status", "available_at", "priority", "created_at"],
    )
    op.create_index(
        "ix_financial_evaluation_jobs_inputs",
        "financial_evaluation_jobs",
        ["process_id", "normalization_run_id", "company_profile_snapshot_id"],
    )
    op.create_index(
        "uq_financial_evaluation_jobs_active_inputs",
        "financial_evaluation_jobs",
        ["process_id", "normalization_run_id", "company_id", "company_profile_snapshot_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('PENDING', 'PROCESSING')"),
    )

    op.create_table(
        "financial_evaluation_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("process_id", sa.Uuid(), nullable=False),
        sa.Column("normalization_run_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("company_profile_snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("input_manifest", sa.JSON(), nullable=False),
        sa.Column("input_digest", sa.String(length=64), nullable=False),
        sa.Column("rule_version", sa.String(length=32), nullable=False),
        sa.Column("formula_versions", sa.JSON(), nullable=False),
        sa.Column("requirement_count", sa.Integer(), nullable=False),
        sa.Column("evaluated_count", sa.Integer(), nullable=False),
        sa.Column("complies_count", sa.Integer(), nullable=False),
        sa.Column("does_not_comply_count", sa.Integer(), nullable=False),
        sa.Column("partial_count", sa.Integer(), nullable=False),
        sa.Column("unknown_count", sa.Integer(), nullable=False),
        sa.Column("not_applicable_count", sa.Integer(), nullable=False),
        sa.Column("conflicting_count", sa.Integer(), nullable=False),
        sa.Column("warning_count", sa.Integer(), nullable=False),
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
        sa.CheckConstraint(f"status IN ({JOB_STATUS})", name="ck_financial_evaluation_runs_status"),
        sa.CheckConstraint("input_digest ~ '^[a-f0-9]{64}$'", name="ck_financial_runs_digest"),
        sa.CheckConstraint("requirement_count >= 0", name="ck_financial_runs_requirement_count"),
        sa.CheckConstraint("evaluated_count >= 0", name="ck_financial_runs_evaluated_count"),
        sa.CheckConstraint("complies_count >= 0", name="ck_financial_runs_complies_count"),
        sa.CheckConstraint(
            "does_not_comply_count >= 0", name="ck_financial_runs_does_not_comply_count"
        ),
        sa.CheckConstraint("partial_count >= 0", name="ck_financial_runs_partial_count"),
        sa.CheckConstraint("unknown_count >= 0", name="ck_financial_runs_unknown_count"),
        sa.CheckConstraint(
            "not_applicable_count >= 0", name="ck_financial_runs_not_applicable_count"
        ),
        sa.CheckConstraint("conflicting_count >= 0", name="ck_financial_runs_conflicting_count"),
        sa.CheckConstraint("warning_count >= 0", name="ck_financial_runs_warning_count"),
        sa.ForeignKeyConstraint(["company_id"], ["company_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["company_profile_snapshot_id"], ["company_profile_snapshots.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["job_id"], ["financial_evaluation_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["normalization_run_id"], ["requirement_normalization_runs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["process_id"], ["processes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_financial_runs_process_company",
        "financial_evaluation_runs",
        ["process_id", "company_id", "created_at"],
    )
    op.create_index(
        "ix_financial_runs_inputs", "financial_evaluation_runs", ["process_id", "input_digest"]
    )
    op.create_index(
        "ix_financial_runs_snapshot", "financial_evaluation_runs", ["company_profile_snapshot_id"]
    )

    op.create_table(
        "financial_metric_calculations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("financial_period_id", sa.Uuid(), nullable=True),
        sa.Column("metric_type", sa.String(length=64), nullable=False),
        sa.Column("formula_name", sa.String(length=128), nullable=False),
        sa.Column("formula_version", sa.String(length=32), nullable=False),
        sa.Column("input_values", sa.JSON(), nullable=False),
        sa.Column("raw_result", sa.Numeric(28, 8), nullable=True),
        sa.Column("rounded_result", sa.Numeric(28, 8), nullable=True),
        sa.Column("unit", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("warning_codes", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            f"metric_type IN ({METRICS})", name="ck_financial_metric_calculations_metric"
        ),
        sa.CheckConstraint(
            f"status IN ({CALC_STATUS})", name="ck_financial_metric_calculations_status"
        ),
        sa.ForeignKeyConstraint(["run_id"], ["financial_evaluation_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_financial_metric_calculations_run_id", "financial_metric_calculations", ["run_id"]
    )
    op.create_index(
        "ix_financial_metric_calculations_period_id",
        "financial_metric_calculations",
        ["financial_period_id"],
    )

    op.create_table(
        "financial_evaluation_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("requirement_id", sa.Uuid(), nullable=False),
        sa.Column("financial_rule_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("metric_type", sa.String(length=64), nullable=True),
        sa.Column("operator", sa.String(length=64), nullable=True),
        sa.Column("required_value", sa.Numeric(28, 8), nullable=True),
        sa.Column("required_min_value", sa.Numeric(28, 8), nullable=True),
        sa.Column("required_max_value", sa.Numeric(28, 8), nullable=True),
        sa.Column("required_unit", sa.String(length=64), nullable=True),
        sa.Column("actual_value", sa.Numeric(28, 8), nullable=True),
        sa.Column("actual_unit", sa.String(length=64), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("financial_period_id", sa.Uuid(), nullable=True),
        sa.Column("calculation_id", sa.Uuid(), nullable=True),
        sa.Column("explanation_code", sa.String(length=64), nullable=False),
        sa.Column("explanation_parameters", sa.JSON(), nullable=False),
        sa.Column("metric_inputs", sa.JSON(), nullable=False),
        sa.Column("evidence_refs", sa.JSON(), nullable=False),
        sa.Column("requires_human_review", sa.Boolean(), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("reviewed_status", sa.String(length=64), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            f"status IN ({RESULT_STATUS})", name="ck_financial_evaluation_results_status"
        ),
        sa.CheckConstraint(
            f"review_status IN ({REVIEW_STATUS})",
            name="ck_financial_evaluation_results_review_status",
        ),
        sa.CheckConstraint(
            f"metric_type IS NULL OR metric_type IN ({METRICS})",
            name="ck_financial_evaluation_results_metric",
        ),
        sa.CheckConstraint(
            f"operator IS NULL OR operator IN ({OPERATORS})",
            name="ck_financial_evaluation_results_operator",
        ),
        sa.ForeignKeyConstraint(
            ["calculation_id"], ["financial_metric_calculations.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["financial_rule_id"], ["financial_requirement_rules.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["financial_evaluation_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "run_id", "requirement_id", name="uq_financial_results_run_requirement"
        ),
    )
    op.create_index(
        "ix_financial_evaluation_results_run_id", "financial_evaluation_results", ["run_id"]
    )
    op.create_index(
        "ix_financial_evaluation_results_requirement_id",
        "financial_evaluation_results",
        ["requirement_id"],
    )
    op.create_index(
        "ix_financial_evaluation_results_status", "financial_evaluation_results", ["status"]
    )
    op.create_index(
        "ix_financial_evaluation_results_period_id",
        "financial_evaluation_results",
        ["financial_period_id"],
    )
    op.create_index(
        "ix_financial_evaluation_results_review", "financial_evaluation_results", ["review_status"]
    )

    op.create_table(
        "financial_evaluation_result_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("result_id", sa.Uuid(), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("override_status", sa.String(length=64), nullable=True),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column("original_status", sa.String(length=64), nullable=False),
        sa.Column("reviewer", sa.String(length=128), nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column(
            "reviewed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            f"review_status IN ({REVIEW_STATUS})", name="ck_financial_result_reviews_status"
        ),
        sa.CheckConstraint(
            f"override_status IS NULL OR override_status IN ({RESULT_STATUS})",
            name="ck_financial_result_reviews_override_status",
        ),
        sa.ForeignKeyConstraint(
            ["result_id"], ["financial_evaluation_results.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_financial_result_reviews_result_id",
        "financial_evaluation_result_reviews",
        ["result_id"],
    )
    op.create_index(
        "ix_financial_result_reviews_reviewed_at",
        "financial_evaluation_result_reviews",
        ["reviewed_at"],
    )

    op.create_table(
        "financial_evaluation_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=True),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("process_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.String(length=1000), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["company_id"], ["company_profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_id"], ["financial_evaluation_jobs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["process_id"], ["processes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["financial_evaluation_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_financial_evaluation_events_run_id", "financial_evaluation_events", ["run_id"]
    )
    op.create_index(
        "ix_financial_evaluation_events_job_id", "financial_evaluation_events", ["job_id"]
    )
    op.create_index(
        "ix_financial_evaluation_events_type", "financial_evaluation_events", ["event_type"]
    )


def downgrade() -> None:
    op.drop_index("ix_financial_evaluation_events_type", table_name="financial_evaluation_events")
    op.drop_index("ix_financial_evaluation_events_job_id", table_name="financial_evaluation_events")
    op.drop_index("ix_financial_evaluation_events_run_id", table_name="financial_evaluation_events")
    op.drop_table("financial_evaluation_events")
    op.drop_index(
        "ix_financial_result_reviews_reviewed_at", table_name="financial_evaluation_result_reviews"
    )
    op.drop_index(
        "ix_financial_result_reviews_result_id", table_name="financial_evaluation_result_reviews"
    )
    op.drop_table("financial_evaluation_result_reviews")
    op.drop_index(
        "ix_financial_evaluation_results_review", table_name="financial_evaluation_results"
    )
    op.drop_index(
        "ix_financial_evaluation_results_period_id", table_name="financial_evaluation_results"
    )
    op.drop_index(
        "ix_financial_evaluation_results_status", table_name="financial_evaluation_results"
    )
    op.drop_index(
        "ix_financial_evaluation_results_requirement_id", table_name="financial_evaluation_results"
    )
    op.drop_index(
        "ix_financial_evaluation_results_run_id", table_name="financial_evaluation_results"
    )
    op.drop_table("financial_evaluation_results")
    op.drop_index(
        "ix_financial_metric_calculations_period_id", table_name="financial_metric_calculations"
    )
    op.drop_index(
        "ix_financial_metric_calculations_run_id", table_name="financial_metric_calculations"
    )
    op.drop_table("financial_metric_calculations")
    op.drop_index("ix_financial_runs_snapshot", table_name="financial_evaluation_runs")
    op.drop_index("ix_financial_runs_inputs", table_name="financial_evaluation_runs")
    op.drop_index("ix_financial_runs_process_company", table_name="financial_evaluation_runs")
    op.drop_table("financial_evaluation_runs")
    op.drop_index(
        "uq_financial_evaluation_jobs_active_inputs", table_name="financial_evaluation_jobs"
    )
    op.drop_index("ix_financial_evaluation_jobs_inputs", table_name="financial_evaluation_jobs")
    op.drop_index("ix_financial_evaluation_jobs_claim", table_name="financial_evaluation_jobs")
    op.drop_table("financial_evaluation_jobs")
    op.drop_index("ix_financial_requirement_rules_latest", table_name="financial_requirement_rules")
    op.drop_index("ix_financial_requirement_rules_run_id", table_name="financial_requirement_rules")
    op.drop_index(
        "ix_financial_requirement_rules_requirement_id", table_name="financial_requirement_rules"
    )
    op.drop_table("financial_requirement_rules")
    op.drop_index("ix_financial_formula_versions_active", table_name="financial_formula_versions")
    op.drop_table("financial_formula_versions")
