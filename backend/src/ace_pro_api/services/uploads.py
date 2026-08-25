from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import ceil
from pathlib import PurePath
from urllib.parse import quote
from uuid import uuid4

from ace_pro_api.config import Settings
from ace_pro_api.domain.enums import UploadStatus, VideoStatus
from ace_pro_api.domain.repositories import UploadRepository, VideoRepository
from ace_pro_api.errors import ApiError
from ace_pro_api.metrics import UPLOAD_EVENTS
from ace_pro_api.persistence.models import UploadPart, UploadSession, Video
from ace_pro_api.storage.base import ObjectStorage, StoredPart

ALLOWED_CONTAINERS = {"mov", "mp4"}
ALLOWED_CODECS = {"h264", "hevc", "unknown"}
ALLOWED_CONTENT_TYPES = {"video/mp4", "video/quicktime", "application/octet-stream"}


class CreateUploadService:
    def __init__(
        self,
        *,
        settings: Settings,
        videos: VideoRepository,
        uploads: UploadRepository,
        storage: ObjectStorage,
    ) -> None:
        self._settings = settings
        self._videos = videos
        self._uploads = uploads
        self._storage = storage

    async def create(
        self,
        *,
        owner_id: str,
        original_filename: str,
        content_type: str,
        container: str,
        codec: str,
        size_bytes: int,
        duration_seconds: int,
        source_fingerprint: str,
        idempotency_key: str | None,
    ) -> UploadSession:
        self._validate(
            original_filename=original_filename,
            content_type=content_type,
            container=container,
            codec=codec,
            size_bytes=size_bytes,
            duration_seconds=duration_seconds,
        )
        if idempotency_key:
            existing = await self._uploads.get_by_idempotency_key(idempotency_key)
            if existing is not None:
                if existing.video.owner_id != owner_id:
                    raise ApiError(
                        409,
                        "idempotency_conflict",
                        "Idempotency key is already in use.",
                    )
                return existing

        video_id = str(uuid4())
        upload_id = str(uuid4())
        object_key = f"videos/{video_id}/{uuid4().hex}/original.{container}"
        multipart_upload_id = await self._storage.create_multipart_upload(
            bucket=self._settings.s3_bucket,
            key=object_key,
            content_type=content_type,
        )
        now = datetime.now(UTC)
        video = Video(
            id=video_id,
            owner_id=owner_id,
            original_filename=PurePath(original_filename).name,
            content_type=content_type,
            container=container,
            codec=codec,
            declared_size_bytes=size_bytes,
            declared_duration_seconds=duration_seconds,
            bucket=self._settings.s3_bucket,
            object_key=object_key,
            status=VideoStatus.UPLOADING.value,
        )
        upload = UploadSession(
            id=upload_id,
            video=video,
            multipart_upload_id=multipart_upload_id,
            idempotency_key=idempotency_key,
            source_fingerprint=source_fingerprint,
            part_size_bytes=self._settings.multipart_part_size_bytes,
            status=UploadStatus.UPLOADING.value,
            expires_at=now + timedelta(hours=self._settings.upload_session_hours),
        )
        await self._videos.add(video)
        await self._uploads.add_session(upload)
        UPLOAD_EVENTS.labels("created").inc()
        return upload

    def _validate(
        self,
        *,
        original_filename: str,
        content_type: str,
        container: str,
        codec: str,
        size_bytes: int,
        duration_seconds: int,
    ) -> None:
        errors = {}
        normalized_extension = PurePath(original_filename).suffix.lower().removeprefix(".")
        if container not in ALLOWED_CONTAINERS or normalized_extension != container:
            errors["container"] = "Only matching MOV and MP4 files are accepted."
        if codec not in ALLOWED_CODECS:
            errors["codec"] = "Codec must be H.264, HEVC, or unknown."
        if content_type not in ALLOWED_CONTENT_TYPES:
            errors["content_type"] = "Unsupported video content type."
        if size_bytes < 1 or size_bytes > self._settings.max_video_size_bytes:
            errors["size_bytes"] = "Video must be greater than zero and no larger than 20 GiB."
        if duration_seconds < 1 or duration_seconds > self._settings.max_video_duration_seconds:
            errors["duration_seconds"] = "Video must be between 1 second and 3 hours."
        if errors:
            raise ApiError(422, "invalid_video", "Video metadata is not accepted.", errors)


class AuthorizePartsService:
    def __init__(
        self,
        *,
        settings: Settings,
        uploads: UploadRepository,
        storage: ObjectStorage,
    ) -> None:
        self._settings = settings
        self._uploads = uploads
        self._storage = storage

    async def authorize(
        self, *, owner_id: str, upload_id: str, part_numbers: list[int]
    ) -> dict[int, str]:
        if not part_numbers or len(part_numbers) > self._settings.max_presigned_parts_per_request:
            raise ApiError(
                422,
                "invalid_part_batch",
                f"Request between 1 and {self._settings.max_presigned_parts_per_request} parts.",
            )
        if len(set(part_numbers)) != len(part_numbers) or any(
            number < 1 or number > 10_000 for number in part_numbers
        ):
            raise ApiError(
                422,
                "invalid_part_numbers",
                "Part numbers must be unique integers from 1 through 10,000.",
            )
        upload = await self._uploads.get_session(upload_id)
        if upload is None or upload.video.owner_id != owner_id:
            raise ApiError(404, "upload_not_found", "Upload session was not found.")
        if upload.expires_at <= datetime.now(UTC):
            raise ApiError(410, "upload_expired", "Upload session has expired.")
        if upload.status not in {UploadStatus.PENDING.value, UploadStatus.UPLOADING.value}:
            raise ApiError(409, "upload_not_active", "Upload session is not active.")
        return await self._storage.presign_upload_parts(
            bucket=upload.video.bucket,
            key=upload.video.object_key,
            multipart_upload_id=upload.multipart_upload_id,
            part_numbers=part_numbers,
            expires_seconds=self._settings.presigned_url_seconds,
        )


@dataclass(frozen=True)
class UploadInspection:
    upload: UploadSession
    parts: list[UploadPart]


class UploadLifecycleService:
    def __init__(
        self,
        *,
        uploads: UploadRepository,
        videos: VideoRepository,
        storage: ObjectStorage,
    ) -> None:
        self._uploads = uploads
        self._videos = videos
        self._storage = storage

    async def inspect(self, *, owner_id: str, upload_id: str) -> UploadInspection:
        upload = await self._owned_upload(owner_id=owner_id, upload_id=upload_id)
        if upload.expires_at <= datetime.now(UTC) and upload.status in {
            UploadStatus.PENDING.value,
            UploadStatus.UPLOADING.value,
        }:
            await self._expire(upload)
            raise ApiError(410, "upload_expired", "Upload session has expired.")
        if upload.status in {UploadStatus.ABORTED.value, UploadStatus.EXPIRED.value}:
            return UploadInspection(upload=upload, parts=[])
        if upload.status == UploadStatus.COMPLETED.value:
            return UploadInspection(
                upload=upload,
                parts=list(await self._uploads.list_parts(upload.id)),
            )
        stored_parts = await self._storage.list_uploaded_parts(
            bucket=upload.video.bucket,
            key=upload.video.object_key,
            multipart_upload_id=upload.multipart_upload_id,
        )
        parts = [
            UploadPart(
                upload_id=upload.id,
                part_number=part.part_number,
                etag=part.etag,
                size_bytes=part.size_bytes,
                checksum=part.checksum,
            )
            for part in stored_parts
        ]
        await self._uploads.replace_parts(upload.id, parts)
        return UploadInspection(upload=upload, parts=parts)

    async def abort(self, *, owner_id: str, upload_id: str) -> UploadSession:
        upload = await self._owned_upload(owner_id=owner_id, upload_id=upload_id)
        if upload.status in {UploadStatus.ABORTED.value, UploadStatus.EXPIRED.value}:
            return upload
        if upload.status == UploadStatus.COMPLETED.value:
            raise ApiError(
                409,
                "upload_completed",
                "A completed upload must be deleted as a video.",
            )
        await self._storage.abort_multipart_upload(
            bucket=upload.video.bucket,
            key=upload.video.object_key,
            multipart_upload_id=upload.multipart_upload_id,
        )
        upload.status = UploadStatus.ABORTED.value
        upload.video.status = VideoStatus.ABORTED.value
        await self._uploads.replace_parts(upload.id, [])
        await self._uploads.save_session(upload)
        await self._videos.save(upload.video)
        UPLOAD_EVENTS.labels("aborted").inc()
        return upload

    async def cleanup_expired(self, *, limit: int = 100) -> int:
        expired = await self._uploads.list_expired_active(now=datetime.now(UTC), limit=limit)
        for upload in expired:
            await self._expire(upload)
        return len(expired)

    async def _owned_upload(self, *, owner_id: str, upload_id: str) -> UploadSession:
        upload = await self._uploads.get_session(upload_id)
        if upload is None or upload.video.owner_id != owner_id:
            raise ApiError(404, "upload_not_found", "Upload session was not found.")
        return upload

    async def _expire(self, upload: UploadSession) -> None:
        await self._storage.abort_multipart_upload(
            bucket=upload.video.bucket,
            key=upload.video.object_key,
            multipart_upload_id=upload.multipart_upload_id,
        )
        upload.status = UploadStatus.EXPIRED.value
        upload.video.status = VideoStatus.EXPIRED.value
        await self._uploads.replace_parts(upload.id, [])
        await self._uploads.save_session(upload)
        await self._videos.save(upload.video)
        UPLOAD_EVENTS.labels("expired").inc()


class CompleteUploadService:
    def __init__(
        self,
        *,
        settings: Settings,
        uploads: UploadRepository,
        videos: VideoRepository,
        storage: ObjectStorage,
    ) -> None:
        self._settings = settings
        self._uploads = uploads
        self._videos = videos
        self._storage = storage

    async def complete(
        self, *, owner_id: str, upload_id: str, client_parts: list[StoredPart]
    ) -> Video:
        upload = await self._uploads.get_session(upload_id)
        if upload is None or upload.video.owner_id != owner_id:
            raise ApiError(404, "upload_not_found", "Upload session was not found.")
        if upload.status == UploadStatus.COMPLETED.value:
            return upload.video
        if upload.status in {
            UploadStatus.ABORTED.value,
            UploadStatus.EXPIRED.value,
            UploadStatus.FAILED.value,
        }:
            raise ApiError(409, "upload_not_active", "Upload session cannot be completed.")
        if upload.expires_at <= datetime.now(UTC):
            raise ApiError(410, "upload_expired", "Upload session has expired.")

        existing_size = await self._storage.object_size(
            bucket=upload.video.bucket, key=upload.video.object_key
        )
        if existing_size is not None:
            return await self._finalize(upload, existing_size, [])

        authoritative_parts = await self._storage.list_uploaded_parts(
            bucket=upload.video.bucket,
            key=upload.video.object_key,
            multipart_upload_id=upload.multipart_upload_id,
        )
        self._validate_parts(upload, client_parts, authoritative_parts)
        upload.status = UploadStatus.COMPLETING.value
        upload.video.status = VideoStatus.COMPLETING.value
        await self._uploads.save_session(upload)
        await self._videos.save(upload.video)
        await self._storage.complete_multipart_upload(
            bucket=upload.video.bucket,
            key=upload.video.object_key,
            multipart_upload_id=upload.multipart_upload_id,
            parts=authoritative_parts,
        )
        final_size = await self._storage.object_size(
            bucket=upload.video.bucket, key=upload.video.object_key
        )
        if final_size is None:
            raise ApiError(502, "storage_completion_failed", "Completed object was not found.")
        return await self._finalize(upload, final_size, authoritative_parts)

    def _validate_parts(
        self,
        upload: UploadSession,
        client_parts: list[StoredPart],
        authoritative_parts: list[StoredPart],
    ) -> None:
        expected_count = ceil(upload.video.declared_size_bytes / upload.part_size_bytes)
        expected_numbers = list(range(1, expected_count + 1))
        actual_numbers = [part.part_number for part in authoritative_parts]
        if actual_numbers != expected_numbers:
            raise ApiError(409, "parts_incomplete", "Not all expected video parts are uploaded.")
        client_etags = {part.part_number: part.etag for part in client_parts}
        if len(client_etags) != len(client_parts) or any(
            client_etags.get(part.part_number) != part.etag for part in authoritative_parts
        ):
            raise ApiError(409, "parts_mismatch", "Completed part identifiers do not match S3.")
        if sum(part.size_bytes for part in authoritative_parts) != upload.video.declared_size_bytes:
            raise ApiError(409, "size_mismatch", "Uploaded bytes do not match the declared size.")

    async def _finalize(
        self, upload: UploadSession, final_size: int, parts: list[StoredPart]
    ) -> Video:
        if (
            final_size != upload.video.declared_size_bytes
            or final_size > self._settings.max_video_size_bytes
        ):
            upload.status = UploadStatus.FAILED.value
            upload.video.status = VideoStatus.FAILED.value
            upload.video.failure_code = "final_size_mismatch"
            await self._uploads.save_session(upload)
            await self._videos.save(upload.video)
            raise ApiError(409, "size_mismatch", "Stored object size does not match the upload.")
        if not self._settings.playback_base_url:
            raise ApiError(503, "playback_not_configured", "Playback base URL is not configured.")
        upload.status = UploadStatus.COMPLETED.value
        upload.video.status = VideoStatus.READY.value
        upload.video.final_size_bytes = final_size
        upload.video.storage_path = f"s3://{upload.video.bucket}/{upload.video.object_key}"
        upload.video.playback_url = (
            f"{self._settings.playback_base_url.rstrip('/')}/"
            f"{quote(upload.video.object_key, safe='/')}"
        )
        upload.video.completed_at = datetime.now(UTC)
        if parts:
            await self._uploads.replace_parts(
                upload.id,
                [
                    UploadPart(
                        upload_id=upload.id,
                        part_number=part.part_number,
                        etag=part.etag,
                        size_bytes=part.size_bytes,
                        checksum=part.checksum,
                    )
                    for part in parts
                ],
            )
        await self._uploads.save_session(upload)
        await self._videos.save(upload.video)
        UPLOAD_EVENTS.labels("completed").inc()
        return upload.video
