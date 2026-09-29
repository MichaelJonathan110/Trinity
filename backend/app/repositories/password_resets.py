"""Password-reset token lookups."""
from app.models.auth import PasswordResetToken
from app.repositories.base import Repository


class PasswordResetRepository(Repository[PasswordResetToken]):
    model = PasswordResetToken

    def by_hash(self, token_hash: str) -> PasswordResetToken | None:
        return self.first(token_hash=token_hash)
