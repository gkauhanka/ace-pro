from datetime import UTC, datetime
from urllib.parse import quote

from ace_pro_api.domain.enums import UploadStatus, VideoStatus
from ace_pro_api.domain.repositories import UploadRepository, VideoRepository
from ace_pro_api.errors import ApiError
from ace_pro_api.metrics import UPLOAD_EVENTS
from ace_pro_api.persistence.models import Video
from ace_pro_api.storage.base import ObjectStorage
from ace_pro_api.storage.cdn import CdnInvalidator


class VideoService:
    def __init__(
        self,
        *,
        videos: VideoRepository,
        uploads: UploadRepository,
        storage: ObjectStorage,
        cdn: CdnInvalidator,
    ) -> None:
        self._videos = videos
        self._uploads = uploads
        self._storage = storage
        self._cdn = cdn

    async def get(self, *, owner_id: str, video_id: str) -> Video:
        video = await self._videos.get(video_id)
        if video is None or video.owner_id != owner_id or video.status == VideoStatus.DELETED.value:
            raise ApiError(404, "video_not_found", "Video was not found.")
        return video

    async def delete(self, *, owner_id: str, video_id: str) -> Video:
        video = await self._videos.get(video_id)
        if video is None or video.owner_id != owner_id:
            raise ApiError(404, "video_not_found", "Video was not found.")
        if video.status == VideoStatus.DELETED.value:
            return video
        video.status = VideoStatus.DELETING.value
        await self._videos.save(video)
        if video.upload is not None and video.upload.status not in {
            UploadStatus.COMPLETED.value,
            UploadStatus.ABORTED.value,
            UploadStatus.EXPIRED.value,
        }:
            await self._storage.abort_multipart_upload(
                bucket=video.bucket,
                key=video.object_key,
                multipart_upload_id=video.upload.multipart_upload_id,
            )
            video.upload.status = UploadStatus.ABORTED.value
            await self._uploads.replace_parts(video.upload.id, [])
            await self._uploads.save_session(video.upload)
        await self._storage.delete_object(bucket=video.bucket, key=video.object_key)
        await self._cdn.invalidate(f"/{quote(video.object_key, safe='/')}")
        video.status = VideoStatus.DELETED.value
        video.storage_path = None
        video.playback_url = None
        video.deleted_at = datetime.now(UTC)
        await self._videos.save(video)
        UPLOAD_EVENTS.labels("deleted").inc()
        return video
