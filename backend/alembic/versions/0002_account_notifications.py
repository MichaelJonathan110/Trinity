"""Add account-lifecycle and notification-preference tables.

Revision ID: 0002_account_notifications
Revises: 0001_initial
Create Date: 2026-09-29

Metadata-driven and idempotent: it builds any table that is registered on
Base.metadata but not yet present, so it can be re-run safely.
"""
from alembic import op

from app.database.base import Base

# Importing the package registers every model on Base.metadata.
import app.models  # noqa: F401

revision = "0002_account_notifications"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    for name in ("notification_preferences", "password_reset_tokens"):
        Base.metadata.tables[name].drop(bind=bind, checkfirst=True)
