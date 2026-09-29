"""Repository layer against a real (in-memory) session (spec 51)."""
from datetime import date

from app.models.user import BodyMetric, User
from app.repositories import NotificationRepository, UserRepository
from app.models.insight import Notification


class TestUserRepository:
    def test_by_email_is_case_insensitive(self, db_session):
        db_session.add(User(email="athlete@example.com", password_hash="x"))
        db_session.commit()
        repo = UserRepository(db_session)
        assert repo.by_email("ATHLETE@example.com") is not None
        assert repo.by_email("missing@example.com") is None

    def test_add_and_get(self, db_session):
        repo = UserRepository(db_session)
        user = repo.add(User(email="new@example.com", password_hash="x"))
        assert user.id is not None
        assert repo.get(user.id).email == "new@example.com"

    def test_delete(self, db_session):
        repo = UserRepository(db_session)
        user = repo.add(User(email="gone@example.com", password_hash="x"))
        repo.delete(user)
        assert repo.get(user.id) is None


class TestNotificationRepository:
    def test_for_user_filters_and_orders(self, db_session):
        user = User(email="n@example.com", password_hash="x")
        db_session.add(user)
        db_session.commit()
        db_session.add_all(
            [
                Notification(user_id=user.id, kind="a", title="first"),
                Notification(user_id=user.id, kind="b", title="second"),
            ]
        )
        db_session.commit()
        repo = NotificationRepository(db_session)
        rows = repo.for_user(user.id)
        assert len(rows) == 2
        assert repo.for_user(user.id, limit=1) == [rows[0]]


class TestGenericRepository:
    def test_list_with_filters(self, db_session):
        user = User(email="f@example.com", password_hash="x")
        db_session.add(user)
        db_session.commit()
        db_session.add_all(
            [
                BodyMetric(user_id=user.id, measured_on=date(2026, 1, 1), weight_kg=80),
                BodyMetric(user_id=user.id, measured_on=date(2026, 1, 2), weight_kg=79),
            ]
        )
        db_session.commit()
        from app.repositories.base import Repository

        class MetricRepo(Repository[BodyMetric]):
            model = BodyMetric

        repo = MetricRepo(db_session)
        assert len(repo.list(user_id=user.id)) == 2
        assert repo.first(measured_on=date(2026, 1, 2)).weight_kg == 79
        assert repo.list(user_id=999999) == []
