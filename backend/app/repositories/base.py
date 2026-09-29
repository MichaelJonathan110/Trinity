"""Generic repository helpers.

Services talk to repositories, never to the ORM session directly, so query
logic lives in one place and is easy to unit-test.
"""
from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class Repository(Generic[ModelT]):
    """Minimal CRUD on top of a single SQLAlchemy model."""

    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, pk: int) -> ModelT | None:
        return self.db.get(self.model, pk)

    def list(self, **filters) -> list[ModelT]:
        stmt = select(self.model)
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        return list(self.db.execute(stmt).scalars().all())

    def first(self, **filters) -> ModelT | None:
        rows = self.list(**filters)
        return rows[0] if rows else None

    def add(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelT) -> None:
        self.db.delete(obj)
        self.db.commit()
