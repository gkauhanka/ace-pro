from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from ace_pro_api.domain.enums import UploadStatus, VideoStatus
from ace_pro_api.errors import ApiError
from ace_pro_api.persistence.models import UploadSession, Video
from ace_pro_api.services.uploads import UploadLifecycleService
from ace_pro_api.storage.base import StoredPart


def active_upload(*, owner_id="owner-1", expires_at=None):
    video = Video(
        id="video-id",
        owner_id=owner_id,
        original_filename="match.mp4",
        content_type="video/mp4",
        container="mp4",
        codec="h264",
        declared_size_bytes=10,
        declared_duration_seconds=60,
        bucket="bucket",
        object_key="videos/random/original.mp4",
        status=VideoStatus.UPLOADING.value,
    )
    return UploadSession(
        id="upload-id",
        video=video,
        multipart_upload_id="multipart-id",
        source_fingerprint="fingerprint",
        part_size_bytes=5,
        status=UploadStatus.UPLOADING.value,
        expires_at=expires_at or datetime.now(UTC) + timedelta(hours=1),
    )


def lifecycle(upload):
    uploads = AsyncMock()
    uploads.get_session.return_value = upload
    videos = AsyncMock()
    storage = AsyncMock()
    service = UploadLifecycleService(uploads=uploads, videos=videos, storage=storage)
    return service, uploads, videos, storage


@pytest.mark.anyio
async def test_inspect_reconciles_authoritative_storage_parts() -> None:
    service, uploads, _videos, storage = lifecycle(active_upload())
    storage.list_uploaded_parts.return_value = [StoredPart(1, '"etag"', 5, "checksum")]

    result = await service.inspect(owner_id="owner-1", upload_id="upload-id")

    assert [(part.part_number, part.size_bytes) for part in result.parts] == [(1, 5)]
    uploads.replace_parts.assert_awaited_once()


@pytest.mark.anyio
async def test_inspect_expires_and_aborts_old_session() -> None:
    upload = active_upload(expires_at=datetime.now(UTC) - timedelta(seconds=1))
    service, uploads, videos, storage = lifecycle(upload)

    with pytest.raises(ApiError) as raised:
        await service.inspect(owner_id="owner-1", upload_id="upload-id")

    assert raised.value.status_code == 410
    assert upload.status == UploadStatus.EXPIRED.value
    assert upload.video.status == VideoStatus.EXPIRED.value
    storage.abort_multipart_upload.assert_awaited_once()
    uploads.save_session.assert_awaited_once_with(upload)
    videos.save.assert_awaited_once_with(upload.video)


@pytest.mark.anyio
async def test_abort_is_idempotent() -> None:
    upload = active_upload()
    service, uploads, videos, storage = lifecycle(upload)

    first = await service.abort(owner_id="owner-1", upload_id="upload-id")
    second = await service.abort(owner_id="owner-1", upload_id="upload-id")

    assert first is second
    assert upload.status == UploadStatus.ABORTED.value
    storage.abort_multipart_upload.assert_awaited_once()
    uploads.replace_parts.assert_awaited_once_with(upload.id, [])
    videos.save.assert_awaited_once_with(upload.video)


@pytest.mark.anyio
async def test_cleanup_expires_active_sessions() -> None:
    upload = active_upload(expires_at=datetime.now(UTC) - timedelta(hours=1))
    service, uploads, _videos, storage = lifecycle(upload)
    uploads.list_expired_active.return_value = [upload]

    count = await service.cleanup_expired(limit=10)

    assert count == 1
    uploads.list_expired_active.assert_awaited_once()
    storage.abort_multipart_upload.assert_awaited_once()

