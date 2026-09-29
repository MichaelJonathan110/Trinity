"""TRINITY initial schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-29

Metadata-driven: builds every table from the model definitions so the migration
can never drift from the ORM. Idempotent on re-run.
"""
from alembic import op

from app.database.base import Base

# Import the package so every model module is registered on Base.metadata.
import app.models  # noqa: F401

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
