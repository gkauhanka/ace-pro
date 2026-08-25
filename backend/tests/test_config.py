from ace_pro_api.config import Settings


def test_settings_defaults_to_confirmed_region() -> None:
    settings = Settings(_env_file=None)

    assert settings.aws_region == "us-west-2"
    assert settings.environment == "development"


def test_settings_accepts_environment_overrides(monkeypatch) -> None:
    monkeypatch.setenv("ACE_PRO_LOG_LEVEL", "DEBUG")

    settings = Settings(_env_file=None)

    assert settings.log_level == "DEBUG"

