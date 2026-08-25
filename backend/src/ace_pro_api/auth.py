from dataclasses import dataclass
from typing import Protocol

from fastapi import Header

from ace_pro_api.config import Settings
from ace_pro_api.errors import ApiError


@dataclass(frozen=True)
class CurrentUser:
    id: str


class AuthProvider(Protocol):
    async def current_user(self, presented_identity: str | None) -> CurrentUser: ...


class DevelopmentAuthProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def current_user(self, presented_identity: str | None) -> CurrentUser:
        if self._settings.environment == "production":
            raise ApiError(
                status_code=501,
                code="authentication_not_configured",
                message="A production authentication provider has not been configured.",
            )
        return CurrentUser(id=presented_identity or "local-test-user")


async def development_identity_header(
    x_dev_user: str | None = Header(default=None, max_length=255),
) -> str | None:
    return x_dev_user

