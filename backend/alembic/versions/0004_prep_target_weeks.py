"""Add target_weeks to preparation phases.

Revision ID: 0004_prep_target_weeks
Revises: 0003_prep_volume_photos
Create Date: 2026-10-05

A preparation block is measured in weeks, so the phase now stores how many
weeks it is planned to run. Metadata-driven and idempotent, exactly like 0003:
`create_all` only creates tables that do not yet exist, so the new column is
added separately with ALTER TABLE after an existence check. That keeps this
revision safe to re-run and works on both SQLite and PostgreSQL.
"""
from alembic import op
from sqlalchemy import inspect

from app.database.base import Base

# Importing the package registers every model on Base.metadata.
import app.models  # noqa: F401

revision = "0004_prep_target_weeks"
down_revision = "0003_prep_volume_photos"
branch_labels = None
depends_on = None

# table -> [(column, DDL type)] added to tables that already existed.
NEW_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "preparation_phases": [
        ("target_weeks", "INTEGER"),
    ],
}


def upgrade() -> None:
    bind = op.get_bind()
    # 1. Any brand-new tables (a no-op for anything already present).
    Base.metadata.create_all(bind=bind)

    # 2. New columns on tables that already existed.
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())
    for table, columns in NEW_COLUMNS.items():
        if table not in existing_tables:
            continue
        present = {c["name"] for c in inspector.get_columns(table)}
        for name, ddl in columns:
            if name not in present:
                op.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "preparation_phases" in set(inspector.get_table_names()):
        present = {c["name"] for c in inspector.get_columns("preparation_phases")}
        if "target_weeks" in present:
            op.execute("ALTER TABLE preparation_phases DROP COLUMN target_weeks")
