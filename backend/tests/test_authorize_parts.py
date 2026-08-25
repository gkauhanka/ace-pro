from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from ace_pro_api.config import Settings
from ace_pro_api.domain.enums import UploadStatus
from ace_pro_api.errors import ApiError
from ace_pro_api.persistence.models import UploadSession, Video
from ace_pro_api.services.uploads import AuthorizePartsService


def upload_for(owner_id="owner-1", *, expires_at=None, status=UploadStatus.UPLOADING.value):
    video = Video(
        id="video-id",
        owner_id=owner_id,
        original_filename="match.mp4",
        content_type="video/mp4",
        container="mp4",
        codec="h264",
        declared_size_bytes=100,
        declared_duration_seconds=60,
        bucket="bucket",
        object_key="videos/random/original.mp4",
    )
    return UploadSession(
        id="upload-id",
        video=video,
        multipart_upload_id="multipart-id",
        source_fingerprint="fingerprint",
        part_size_bytes=64 * 1024 * 1024,
        status=status,
        expires_at=expires_at or datetime.now(UTC) + timedelta(hours=1),
    )


@pytest.mark.anyio
async def test_authorize_parts_presigns_requested_batch() -> None:
    uploads = AsyncMock()
    uploads.get_session.return_value = upload_for()
    storage = AsyncMock()
    storage.presign_upload_parts.return_value = {1: "url-1", 2: "url-2"}
    service = AuthorizePartsService(
        settings=Settings(_env_file=None), uploads=uploads, storage=storage
    )

    result = await service.authorize(owner_id="owner-1", upload_id="upload-id", part_numbers=[1, 2])

    assert result == {1: "url-1", 2: "url-2"}
    storage.presign_upload_parts.assert_awaited_once_with(
        bucket="bucket",
        key="videos/random/original.mp4",
        multipart_upload_id="multipart-id",
        part_numbers=[1, 2],
        expires_seconds=900,
    )


@pytest.mark.anyio
@pytest.mark.parametrize("part_numbers", [[], [0], [10_001], [1, 1]])
async def test_authorize_parts_rejects_invalid_part_numbers(part_numbers) -> None:
    uploads = AsyncMock()
    storage = AsyncMock()
    service = AuthorizePartsService(
        settings=Settings(_env_file=None), uploads=uploads, storage=storage
    )

    with pytest.raises(ApiError) as raised:
        await service.authorize(
            owner_id="owner-1", upload_id="upload-id", part_numbers=part_numbers
        )

    assert raised.value.status_code == 422
    storage.presign_upload_parts.assert_not_awaited()


@pytest.mark.anyio
async def test_authorize_parts_hides_other_owners_upload() -> None:
    uploads = AsyncMock()
    uploads.get_session.return_value = upload_for(owner_id="different-owner")
    service = AuthorizePartsService(
        settings=Settings(_env_file=None), uploads=uploads, storage=AsyncMock()
    )

    with pytest.raises(ApiError) as raised:
        await service.authorize(owner_id="owner-1", upload_id="upload-id", part_numbers=[1])

    assert raised.value.status_code == 404


@pytest.mark.anyio
async def test_authorize_parts_rejects_expired_upload() -> None:
    uploads = AsyncMock()
    uploads.get_session.return_value = upload_for(
        expires_at=datetime.now(UTC) - timedelta(seconds=1)
    )
    service = AuthorizePartsService(
        settings=Settings(_env_file=None), uploads=uploads, storage=AsyncMock()
    )

    with pytest.raises(ApiError) as raised:
        await service.authorize(owner_id="owner-1", upload_id="upload-id", part_numbers=[1])

    assert raised.value.status_code == 410
