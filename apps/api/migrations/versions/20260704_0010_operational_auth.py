"""operational auth.

Revision ID: 20260704_0010
Revises: 20260704_0009
Create Date: 2026-07-04 13:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260704_0010"
down_revision: str | None = "20260704_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_STATUS = "status IN ('ACTIVE', 'DISABLED', 'LOCKED', 'PENDING')"
ROLE_NAME = "name IN ('ADMIN', 'ANALYST', 'REVIEWER', 'VIEWER')"


def upgrade() -> None:
    op.create_table(
        "auth_users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(USER_STATUS, name="ck_auth_users_status"),
        sa.CheckConstraint(
            "failed_login_attempts >= 0",
            name="ck_auth_users_failed_login_attempts",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_auth_users_email", "auth_users", ["email"], unique=True)
    op.create_index("ix_auth_users_status", "auth_users", ["status"])

    op.create_table(
        "auth_roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=32), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(ROLE_NAME, name="ck_auth_roles_name"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_auth_roles_name", "auth_roles", ["name"], unique=True)

    op.create_table(
        "auth_user_roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["role_id"], ["auth_roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["auth_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_auth_user_roles_user_role"),
    )
    op.create_index("ix_auth_user_roles_user", "auth_user_roles", ["user_id"])
    op.create_index("ix_auth_user_roles_role", "auth_user_roles", ["role_id"])

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("session_token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.Column("user_agent_hash", sa.String(length=64), nullable=True),
        sa.CheckConstraint(
            "session_token_hash ~ '^[a-f0-9]{64}$'",
            name="ck_auth_sessions_token_hash",
        ),
        sa.CheckConstraint(
            "ip_hash IS NULL OR ip_hash ~ '^[a-f0-9]{64}$'",
            name="ck_auth_sessions_ip",
        ),
        sa.CheckConstraint(
            "user_agent_hash IS NULL OR user_agent_hash ~ '^[a-f0-9]{64}$'",
            name="ck_auth_sessions_user_agent",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["auth_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_auth_sessions_token_hash",
        "auth_sessions",
        ["session_token_hash"],
        unique=True,
    )
    op.create_index("ix_auth_sessions_user", "auth_sessions", ["user_id"])
    op.create_index("ix_auth_sessions_expires", "auth_sessions", ["expires_at"])

    op.create_table(
        "auth_login_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("email_hash", sa.String(length=64), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("failure_reason", sa.String(length=64), nullable=True),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.Column("user_agent_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["auth_users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_auth_login_events_user", "auth_login_events", ["user_id"])
    op.create_index("ix_auth_login_events_email_hash", "auth_login_events", ["email_hash"])
    op.create_index("ix_auth_login_events_created_at", "auth_login_events", ["created_at"])

    op.create_table(
        "operational_audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("actor_email_hash", sa.String(length=64), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=True),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.Column("user_agent_hash", sa.String(length=64), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["auth_users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_operational_audit_events_actor",
        "operational_audit_events",
        ["actor_user_id"],
    )
    op.create_index(
        "ix_operational_audit_events_type",
        "operational_audit_events",
        ["event_type"],
    )
    op.create_index(
        "ix_operational_audit_events_entity",
        "operational_audit_events",
        ["entity_type", "entity_id"],
    )
    op.create_index(
        "ix_operational_audit_events_created_at",
        "operational_audit_events",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_operational_audit_events_created_at", table_name="operational_audit_events")
    op.drop_index("ix_operational_audit_events_entity", table_name="operational_audit_events")
    op.drop_index("ix_operational_audit_events_type", table_name="operational_audit_events")
    op.drop_index("ix_operational_audit_events_actor", table_name="operational_audit_events")
    op.drop_table("operational_audit_events")
    op.drop_index("ix_auth_login_events_created_at", table_name="auth_login_events")
    op.drop_index("ix_auth_login_events_email_hash", table_name="auth_login_events")
    op.drop_index("ix_auth_login_events_user", table_name="auth_login_events")
    op.drop_table("auth_login_events")
    op.drop_index("ix_auth_sessions_expires", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_user", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_token_hash", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_index("ix_auth_user_roles_role", table_name="auth_user_roles")
    op.drop_index("ix_auth_user_roles_user", table_name="auth_user_roles")
    op.drop_table("auth_user_roles")
    op.drop_index("ix_auth_roles_name", table_name="auth_roles")
    op.drop_table("auth_roles")
    op.drop_index("ix_auth_users_status", table_name="auth_users")
    op.drop_index("ix_auth_users_email", table_name="auth_users")
    op.drop_table("auth_users")
