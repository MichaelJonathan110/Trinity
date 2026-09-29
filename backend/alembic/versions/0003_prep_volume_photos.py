"""Add preparation phases, refeed entries, progress photos, RIR/set-type and
body circumferences.

Revision ID: 0003_prep_volume_photos
Revises: 0002_account_notifications
Create Date: 2026-09-29

Metadata-driven and idempotent. `create_all` only creates tables that do not yet
exist, so the new columns are added separately with ALTER TABLE after an
existence check - that way this revision is safe to re-run and works on both the
SQLite test database and PostgreSQL.
"""
from alembic import op
from sqlalchemy import inspect

from app.database.base import Base

# Importing the package registers every model on Base.metadata.
import app.models  # noqa: F401

revision = "0003_prep_volume_photos"
down_revision = "0002_account_notifications"
branch_labels = None
depends_on = None

# table -> [(column, DDL type)] added to tables that already existed.
NEW_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "exercise_sets": [
        ("rir", "NUMERIC(3, 1)"),
        ("set_type", "VARCHAR(16)"),
    ],
    "body_metrics": [
        ("neck_cm", "NUMERIC(5, 2)"),
        ("shoulder_cm", "NUMERIC(5, 2)"),
        ("chest_cm", "NUMERIC(5, 2)"),
        ("arm_cm", "NUMERIC(5, 2)"),
        ("forearm_cm", "NUMERIC(5, 2)"),
        ("thigh_cm", "NUMERIC(5, 2)"),
        ("calf_cm", "NUMERIC(5, 2)"),
        ("hip_cm", "NUMERIC(5, 2)"),
    ],
}

NEW_TABLES = ("preparation_phases", "refeed_entries", "progress_photos")


def upgrade() -> None:
    bind = op.get_bind()
    # 1. New tables (create_all is a no-op for anything already present).
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
    for name in NEW_TABLES:
        Base.metadata.tables[name].drop(bind=bind, checkfirst=True)
