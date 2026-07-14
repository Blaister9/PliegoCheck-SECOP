"""track source rows separately from normalized search results.

Revision ID: 20260713_0018
Revises: 20260713_0017
Create Date: 2026-07-13 19:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260713_0018"
down_revision: str | None = "20260713_0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "external_procurement_searches",
        sa.Column("source_row_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.execute("UPDATE external_procurement_searches SET source_row_count = result_count")
    op.alter_column(
        "external_procurement_searches",
        "source_row_count",
        existing_type=sa.Integer(),
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("external_procurement_searches", "source_row_count")
