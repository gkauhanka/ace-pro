from datetime import datetime

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ace_pro_api.api.dependencies import (
    get_cdn_invalidator,
    get_current_user,
    get_database_session,
    get_object_storage,
)
from ace_pro_api.auth import CurrentUser
from ace_pro_api.persistence.repositories import (
    SqlAlchemyUploadRepository,
    SqlAlchemyVideoRepository,
)
from ace_pro_api.services.videos import VideoService
from ace_pro_api.storage.cdn import CdnInvalidator
from ace_pro_api.storage.s3 import S3ObjectStorage

router = APIRouter(prefix="/api/v1/videos", tags=["videos"])


class VideoResponse(BaseModel):
    video_id: str
    status: str
    original_filename: str
    size_bytes: int | None
    duration_seconds: int
    container: str
    codec: str
    storage_path: str | None
    playback_url: str | None
    created_at: datetime
    completed_at: datetime | None


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
    storage: S3ObjectStorage = Depends(get_object_storage),
    cdn: CdnInvalidator = Depends(get_cdn_invalidator),
) -> VideoResponse:
    video = await VideoService(
        videos=SqlAlchemyVideoRepository(session),
        uploads=SqlAlchemyUploadRepository(session),
        storage=storage,
        cdn=cdn,
    ).get(owner_id=current_user.id, video_id=video_id)
    return VideoResponse(
        video_id=video.id,
        status=video.status,
        original_filename=video.original_filename,
        size_bytes=video.final_size_bytes or video.declared_size_bytes,
        duration_seconds=video.declared_duration_seconds,
        container=video.container,
        codec=video.codec,
        storage_path=video.storage_path,
        playback_url=video.playback_url,
        created_at=video.created_at,
        completed_at=video.completed_at,
    )


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
    storage: S3ObjectStorage = Depends(get_object_storage),
    cdn: CdnInvalidator = Depends(get_cdn_invalidator),
) -> Response:
    await VideoService(
        videos=SqlAlchemyVideoRepository(session),
        uploads=SqlAlchemyUploadRepository(session),
        storage=storage,
        cdn=cdn,
    ).delete(owner_id=current_user.id, video_id=video_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

