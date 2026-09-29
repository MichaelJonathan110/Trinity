"""User lookups."""
from app.models.user import User
from app.repositories.base import Repository


class UserRepository(Repository[User]):
    model = User

    def by_email(self, email: str) -> User | None:
        return self.first(email=email.lower())
