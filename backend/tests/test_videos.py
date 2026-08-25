from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from ace_pro_api.domain.enums import UploadStatus, VideoStatus
from ace_pro_api.errors import ApiError
from ace_pro_api.persistence.models import UploadSession, Video
from ace_pro_api.services.videos import VideoService


def video_service(*, owner_id="owner-1", status=VideoStatus.READY.value, with_upload=True):
    video = Video(
        id="video-id",
        owner_id=owner_id,
        original_filename="match.mp4",
        content_type="video/mp4",
        container="mp4",
        codec="h264",
        declared_size_bytes=10,
        declared_duration_seconds=60,
        final_size_bytes=10,
        bucket="bucket",
        object_key="videos/random/original.mp4",
        status=status,
        storage_path="s3://bucket/videos/random/original.mp4",
        playback_url="https://media.example/videos/random/original.mp4",
    )
    if with_upload:
        video.upload = UploadSession(
            id="upload-id",
            video=video,
            multipart_upload_id="multipart-id",
            source_fingerprint="fingerprint",
            part_size_bytes=5,
            status=(
                UploadStatus.COMPLETED.value
                if status == VideoStatus.READY.value
                else UploadStatus.UPLOADING.value
            ),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
    videos = AsyncMock()
    videos.get.return_value = video
    uploads = AsyncMock()
    storage = AsyncMock()
    cdn = AsyncMock()
    service = VideoService(videos=videos, uploads=uploads, storage=storage, cdn=cdn)
    return service, video, videos, uploads, storage, cdn


@pytest.mark.anyio
async def test_get_video_hides_other_owner_and_deleted_video() -> None:
    service, _video, _videos, _uploads, _storage, _cdn = video_service(
        owner_id="different-owner"
    )

    with pytest.raises(ApiError) as raised:
        await service.get(owner_id="owner-1", video_id="video-id")

    assert raised.value.status_code == 404


@pytest.mark.anyio
async def test_delete_ready_video_removes_object_and_invalidates_path() -> None:
    service, video, videos, _uploads, storage, cdn = video_service()

    result = await service.delete(owner_id="owner-1", video_id="video-id")

    assert result is video
    storage.delete_object.assert_awaited_once_with(
        bucket="bucket", key="videos/random/original.mp4"
    )
    storage.abort_multipart_upload.assert_not_awaited()
    cdn.invalidate.assert_awaited_once_with("/videos/random/original.mp4")
    assert video.status == VideoStatus.DELETED.value
    assert video.storage_path is None
    assert video.playback_url is None
    assert video.deleted_at is not None
    assert videos.save.await_count == 2


@pytest.mark.anyio
async def test_delete_incomplete_video_aborts_multipart_upload() -> None:
    service, video, _videos, uploads, storage, _cdn = video_service(
        status=VideoStatus.UPLOADING.value
    )

    await service.delete(owner_id="owner-1", video_id="video-id")

    storage.abort_multipart_upload.assert_awaited_once_with(
        bucket=video.bucket,
        key=video.object_key,
        multipart_upload_id=video.upload.multipart_upload_id,
    )
    uploads.replace_parts.assert_awaited_once_with(video.upload.id, [])
    assert video.upload.status == UploadStatus.ABORTED.value


@pytest.mark.anyio
async def test_delete_is_idempotent_after_deleted_state() -> None:
    service, video, videos, _uploads, storage, cdn = video_service(
        status=VideoStatus.DELETED.value
    )

    result = await service.delete(owner_id="owner-1", video_id="video-id")

    assert result is video
    storage.delete_object.assert_not_awaited()
    cdn.invalidate.assert_not_awaited()
    videos.save.assert_not_awaited()

