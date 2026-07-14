"""allow unknown currency in external procurement results and imported processes.

Revision ID: 20260713_0017
Revises: 20260713_0016
Create Date: 2026-07-13 16:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260713_0017"
down_revision: str | None = "20260713_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "external_procurement_search_results",
        "currency",
        existing_type=sa.String(length=3),
        nullable=True,
    )
    op.alter_column(
        "processes",
        "currency",
        existing_type=sa.String(length=3),
        nullable=True,
    )


def downgrade() -> None:
    op.execute("UPDATE processes SET currency = 'COP' WHERE currency IS NULL")
    op.alter_column(
        "processes",
        "currency",
        existing_type=sa.String(length=3),
        nullable=False,
    )
    op.execute(
        "UPDATE external_procurement_search_results SET currency = 'COP' WHERE currency IS NULL"
    )
    op.alter_column(
        "external_procurement_search_results",
        "currency",
        existing_type=sa.String(length=3),
        nullable=False,
    )
