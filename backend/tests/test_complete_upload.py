from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from ace_pro_api.config import Settings
from ace_pro_api.domain.enums import UploadStatus, VideoStatus
from ace_pro_api.errors import ApiError
from ace_pro_api.persistence.models import UploadSession, Video
from ace_pro_api.services.uploads import CompleteUploadService
from ace_pro_api.storage.base import StoredPart


def completion_service(*, size=10):
    video = Video(
        id="video-id",
        owner_id="owner-1",
        original_filename="match.mp4",
        content_type="video/mp4",
        container="mp4",
        codec="h264",
        declared_size_bytes=size,
        declared_duration_seconds=60,
        bucket="bucket",
        object_key="videos/random/original.mp4",
        status=VideoStatus.UPLOADING.value,
    )
    upload = UploadSession(
        id="upload-id",
        video=video,
        multipart_upload_id="multipart-id",
        source_fingerprint="fingerprint",
        part_size_bytes=5,
        status=UploadStatus.UPLOADING.value,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    uploads = AsyncMock()
    uploads.get_session.return_value = upload
    videos = AsyncMock()
    storage = AsyncMock()
    settings = Settings(playback_base_url="https://media.example.test", _env_file=None)
    service = CompleteUploadService(
        settings=settings,
        uploads=uploads,
        videos=videos,
        storage=storage,
    )
    return service, upload, uploads, videos, storage


@pytest.mark.anyio
async def test_complete_upload_validates_parts_and_returns_references() -> None:
    service, upload, uploads, videos, storage = completion_service()
    parts = [StoredPart(1, '"one"', 5), StoredPart(2, '"two"', 5)]
    storage.object_size.side_effect = [None, 10]
    storage.list_uploaded_parts.return_value = parts

    video = await service.complete(owner_id="owner-1", upload_id="upload-id", client_parts=parts)

    storage.complete_multipart_upload.assert_awaited_once()
    assert upload.status == UploadStatus.COMPLETED.value
    assert video.status == VideoStatus.READY.value
    assert video.storage_path == "s3://bucket/videos/random/original.mp4"
    assert video.playback_url == "https://media.example.test/videos/random/original.mp4"
    assert video.final_size_bytes == 10
    uploads.replace_parts.assert_awaited_once()
    videos.save.assert_awaited()


@pytest.mark.anyio
async def test_complete_upload_recovers_when_object_already_exists() -> None:
    service, upload, _uploads, _videos, storage = completion_service()
    storage.object_size.return_value = 10

    video = await service.complete(owner_id="owner-1", upload_id="upload-id", client_parts=[])

    assert upload.status == UploadStatus.COMPLETED.value
    assert video.status == VideoStatus.READY.value
    storage.list_uploaded_parts.assert_not_awaited()
    storage.complete_multipart_upload.assert_not_awaited()


@pytest.mark.anyio
async def test_complete_upload_is_idempotent_after_database_completion() -> None:
    service, upload, _uploads, _videos, storage = completion_service()
    upload.status = UploadStatus.COMPLETED.value
    upload.video.status = VideoStatus.READY.value
    upload.video.storage_path = "s3://bucket/key"
    upload.video.playback_url = "https://media.example/key"

    video = await service.complete(owner_id="owner-1", upload_id="upload-id", client_parts=[])

    assert video is upload.video
    storage.object_size.assert_not_awaited()


@pytest.mark.anyio
async def test_complete_upload_rejects_missing_or_mismatched_parts() -> None:
    service, _upload, _uploads, _videos, storage = completion_service()
    storage.object_size.return_value = None
    storage.list_uploaded_parts.return_value = [StoredPart(1, '"one"', 5)]

    with pytest.raises(ApiError) as raised:
        await service.complete(
            owner_id="owner-1",
            upload_id="upload-id",
            client_parts=[StoredPart(1, '"different"', 5)],
        )

    assert raised.value.code == "parts_incomplete"
    storage.complete_multipart_upload.assert_not_awaited()

