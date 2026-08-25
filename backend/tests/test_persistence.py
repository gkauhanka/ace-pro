from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ace_pro_api.domain.enums import UploadStatus, VideoStatus
from ace_pro_api.persistence.models import Base, UploadPart, UploadSession, Video
from ace_pro_api.persistence.repositories import (
    SqlAlchemyUploadRepository,
    SqlAlchemyVideoRepository,
)


@pytest.mark.anyio
async def test_video_upload_and_parts_round_trip() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        videos = SqlAlchemyVideoRepository(session)
        uploads = SqlAlchemyUploadRepository(session)
        video = Video(
            id="video-id",
            owner_id="owner-id",
            original_filename="match.mov",
            content_type="video/quicktime",
            container="mov",
            codec="hevc",
            declared_size_bytes=100,
            declared_duration_seconds=60,
            bucket="ace-pro-test",
            object_key="videos/random/original.mov",
            status=VideoStatus.PENDING.value,
        )
        upload = UploadSession(
            id="upload-id",
            video=video,
            multipart_upload_id="s3-upload-id",
            source_fingerprint="fingerprint",
            part_size_bytes=5,
            status=UploadStatus.UPLOADING.value,
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
        await videos.add(video)
        await uploads.add_session(upload)
        await uploads.replace_parts(
            upload.id,
            [
                UploadPart(upload_id=upload.id, part_number=2, etag="two", size_bytes=5),
                UploadPart(upload_id=upload.id, part_number=1, etag="one", size_bytes=5),
            ],
        )
        await session.commit()

    async with factory() as session:
        videos = SqlAlchemyVideoRepository(session)
        uploads = SqlAlchemyUploadRepository(session)
        stored_video = await videos.get("video-id")
        stored_parts = await uploads.list_parts("upload-id")

        assert stored_video is not None
        assert stored_video.object_key == "videos/random/original.mov"
        assert [part.part_number for part in stored_parts] == [1, 2]

    await engine.dispose()

