import pytest

from ace_pro_api.auth import DevelopmentAuthProvider
from ace_pro_api.config import Settings
from ace_pro_api.errors import ApiError


@pytest.mark.anyio
async def test_development_auth_uses_header_or_local_identity() -> None:
    provider = DevelopmentAuthProvider(Settings(environment="development", _env_file=None))

    assert (await provider.current_user("tester")).id == "tester"
    assert (await provider.current_user(None)).id == "local-test-user"


@pytest.mark.anyio
async def test_development_auth_fails_closed_in_production() -> None:
    provider = DevelopmentAuthProvider(Settings(environment="production", _env_file=None))

    with pytest.raises(ApiError) as raised:
        await provider.current_user(None)

    assert raised.value.code == "authentication_not_configured"

