from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from ace_pro_api.config import Settings
from ace_pro_api.errors import ApiError
from ace_pro_api.persistence.models import UploadSession, Video
from ace_pro_api.services.uploads import CreateUploadService


def make_service(settings=None):
    videos = AsyncMock()
    uploads = AsyncMock()
    uploads.get_by_idempotency_key.return_value = None
    storage = AsyncMock()
    storage.create_multipart_upload.return_value = "storage-upload-id"
    service = CreateUploadService(
        settings=settings or Settings(_env_file=None),
        videos=videos,
        uploads=uploads,
        storage=storage,
    )
    return service, videos, uploads, storage


@pytest.mark.anyio
async def test_create_upload_builds_non_guessable_object_and_24_hour_session() -> None:
    service, videos, uploads, storage = make_service()

    result = await service.create(
        owner_id="owner-1",
        original_filename="../match.mov",
        content_type="video/quicktime",
        container="mov",
        codec="hevc",
        size_bytes=100,
        duration_seconds=60,
        source_fingerprint="asset-fingerprint",
        idempotency_key="create-request-1",
    )

    assert result.video.original_filename == "match.mov"
    assert result.video.object_key.startswith(f"videos/{result.video.id}/")
    assert result.video.object_key.endswith("/original.mov")
    assert result.multipart_upload_id == "storage-upload-id"
    assert timedelta(hours=23, minutes=59) < result.expires_at - datetime.now(UTC)
    assert result.expires_at - datetime.now(UTC) <= timedelta(hours=24)
    videos.add.assert_awaited_once()
    uploads.add_session.assert_awaited_once_with(result)
    storage.create_multipart_upload.assert_awaited_once()


@pytest.mark.anyio
async def test_create_upload_accepts_unknown_codec_for_transfer_only_client() -> None:
    service, _videos, _uploads, _storage = make_service()

    result = await service.create(
        owner_id="owner-1",
        original_filename="match.mov",
        content_type="video/quicktime",
        container="mov",
        codec="unknown",
        size_bytes=100,
        duration_seconds=60,
        source_fingerprint="asset-fingerprint",
        idempotency_key=None,
    )

    assert result.video.codec == "unknown"


@pytest.mark.anyio
async def test_create_upload_returns_existing_idempotent_session() -> None:
    service, videos, uploads, storage = make_service()
    existing_video = Video(
        id="video-id",
        owner_id="owner-1",
        original_filename="match.mp4",
        content_type="video/mp4",
        container="mp4",
        codec="h264",
        declared_size_bytes=100,
        declared_duration_seconds=60,
        bucket="bucket",
        object_key="videos/random/original.mp4",
    )
    existing = UploadSession(
        id="upload-id",
        video=existing_video,
        multipart_upload_id="multipart-id",
        idempotency_key="same-request",
        source_fingerprint="fingerprint",
        part_size_bytes=64 * 1024 * 1024,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
    )
    uploads.get_by_idempotency_key.return_value = existing

    result = await service.create(
        owner_id="owner-1",
        original_filename="match.mp4",
        content_type="video/mp4",
        container="mp4",
        codec="h264",
        size_bytes=100,
        duration_seconds=60,
        source_fingerprint="fingerprint",
        idempotency_key="same-request",
    )

    assert result is existing
    videos.add.assert_not_awaited()
    storage.create_multipart_upload.assert_not_awaited()


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("changes", "field"),
    [
        ({"original_filename": "match.avi", "container": "avi"}, "container"),
        ({"codec": "prores"}, "codec"),
        ({"size_bytes": 20 * 1024 * 1024 * 1024 + 1}, "size_bytes"),
        ({"duration_seconds": 10801}, "duration_seconds"),
    ],
)
async def test_create_upload_rejects_invalid_metadata(changes, field) -> None:
    service, _videos, _uploads, storage = make_service()
    values = {
        "owner_id": "owner-1",
        "original_filename": "match.mp4",
        "content_type": "video/mp4",
        "container": "mp4",
        "codec": "h264",
        "size_bytes": 100,
        "duration_seconds": 60,
        "source_fingerprint": "fingerprint",
        "idempotency_key": None,
    }
    values.update(changes)

    with pytest.raises(ApiError) as raised:
        await service.create(**values)

    assert field in raised.value.details
    storage.create_multipart_upload.assert_not_awaited()
