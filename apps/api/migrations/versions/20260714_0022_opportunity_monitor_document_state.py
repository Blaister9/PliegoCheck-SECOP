"""Persist document inventory state for opportunity monitors.

Revision ID: 20260714_0022
Revises: 20260714_0021
Create Date: 2026-07-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260714_0022"
down_revision: str | None = "20260714_0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "opportunity_monitor_candidate_states",
        sa.Column("document_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "opportunity_monitor_candidate_states",
        sa.Column("document_version_hash", sa.String(length=64), server_default="", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("opportunity_monitor_candidate_states", "document_version_hash")
    op.drop_column("opportunity_monitor_candidate_states", "document_count")
