from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ACE_PRO_",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8000, ge=1, le=65535)
    aws_region: str = "us-west-2"
    database_url: str = "postgresql+asyncpg://ace_pro:ace_pro@127.0.0.1:5432/ace_pro"
    s3_bucket: str = "ace-pro-videos"
    s3_endpoint_url: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_force_path_style: bool = False
    playback_base_url: str | None = None
    upload_session_hours: int = Field(default=24, ge=1, le=168)
    multipart_part_size_bytes: int = Field(default=64 * 1024 * 1024, ge=5 * 1024 * 1024)
    max_video_size_bytes: int = Field(default=20 * 1024 * 1024 * 1024, ge=1)
    max_video_duration_seconds: int = Field(default=3 * 60 * 60, ge=1)
    presigned_url_seconds: int = Field(default=15 * 60, ge=60, le=60 * 60)
    max_presigned_parts_per_request: int = Field(default=100, ge=1, le=1000)
    cloudfront_distribution_id: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
