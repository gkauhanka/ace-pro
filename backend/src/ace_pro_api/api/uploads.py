from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Header, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ace_pro_api.api.dependencies import (
    get_current_user,
    get_database_session,
    get_object_storage,
)
from ace_pro_api.auth import CurrentUser
from ace_pro_api.config import get_settings
from ace_pro_api.persistence.repositories import (
    SqlAlchemyUploadRepository,
    SqlAlchemyVideoRepository,
)
from ace_pro_api.services.uploads import (
    AuthorizePartsService,
    CompleteUploadService,
    CreateUploadService,
    UploadLifecycleService,
)
from ace_pro_api.storage.base import StoredPart
from ace_pro_api.storage.s3 import S3ObjectStorage

router = APIRouter(prefix="/api/v1/uploads", tags=["uploads"])


class CreateUploadRequest(BaseModel):
    original_filename: str = Field(min_length=1, max_length=1024)
    content_type: str = Field(min_length=1, max_length=255)
    container: str = Field(min_length=1, max_length=16)
    codec: str = Field(min_length=1, max_length=32)
    size_bytes: int
    duration_seconds: int
    source_fingerprint: str = Field(min_length=1, max_length=512)


class CreateUploadResponse(BaseModel):
    video_id: str
    upload_id: str
    object_key: str
    part_size_bytes: int
    expires_at: datetime


class AuthorizePartsRequest(BaseModel):
    part_numbers: list[int] = Field(min_length=1, max_length=100)


class AuthorizedPart(BaseModel):
    part_number: int
    url: str


class AuthorizePartsResponse(BaseModel):
    parts: list[AuthorizedPart]
    expires_at: datetime


class UploadedPartResponse(BaseModel):
    part_number: int
    etag: str
    size_bytes: int
    checksum: str | None


class UploadStatusResponse(BaseModel):
    video_id: str
    upload_id: str
    status: str
    part_size_bytes: int
    expires_at: datetime
    parts: list[UploadedPartResponse]


class CompletePartRequest(BaseModel):
    part_number: int = Field(ge=1, le=10_000)
    etag: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(gt=0)


class CompleteUploadRequest(BaseModel):
    parts: list[CompletePartRequest] = Field(min_length=1, max_length=10_000)


class CompleteUploadResponse(BaseModel):
    video_id: str
    storage_path: str
    playback_url: str


@router.post("", response_model=CreateUploadResponse, status_code=status.HTTP_201_CREATED)
async def create_upload(
    body: CreateUploadRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
    storage: S3ObjectStorage = Depends(get_object_storage),
    idempotency_key: str | None = Header(default=None, max_length=255),
) -> CreateUploadResponse:
    service = CreateUploadService(
        settings=get_settings(),
        videos=SqlAlchemyVideoRepository(session),
        uploads=SqlAlchemyUploadRepository(session),
        storage=storage,
    )
    upload = await service.create(
        owner_id=current_user.id,
        idempotency_key=idempotency_key,
        **body.model_dump(),
    )
    return CreateUploadResponse(
        video_id=upload.video.id,
        upload_id=upload.id,
        object_key=upload.video.object_key,
        part_size_bytes=upload.part_size_bytes,
        expires_at=upload.expires_at,
    )


@router.post("/{upload_id}/parts", response_model=AuthorizePartsResponse)
async def authorize_parts(
    upload_id: str,
    body: AuthorizePartsRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
    storage: S3ObjectStorage = Depends(get_object_storage),
) -> AuthorizePartsResponse:
    settings = get_settings()
    urls = await AuthorizePartsService(
        settings=settings,
        uploads=SqlAlchemyUploadRepository(session),
        storage=storage,
    ).authorize(
        owner_id=current_user.id,
        upload_id=upload_id,
        part_numbers=body.part_numbers,
    )
    return AuthorizePartsResponse(
        parts=[
            AuthorizedPart(part_number=number, url=urls[number])
            for number in body.part_numbers
        ],
        expires_at=datetime.now(UTC) + timedelta(seconds=settings.presigned_url_seconds),
    )


@router.get("/{upload_id}", response_model=UploadStatusResponse)
async def inspect_upload(
    upload_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
    storage: S3ObjectStorage = Depends(get_object_storage),
) -> UploadStatusResponse:
    inspection = await UploadLifecycleService(
        uploads=SqlAlchemyUploadRepository(session),
        videos=SqlAlchemyVideoRepository(session),
        storage=storage,
    ).inspect(owner_id=current_user.id, upload_id=upload_id)
    return UploadStatusResponse(
        video_id=inspection.upload.video.id,
        upload_id=inspection.upload.id,
        status=inspection.upload.status,
        part_size_bytes=inspection.upload.part_size_bytes,
        expires_at=inspection.upload.expires_at,
        parts=[
            UploadedPartResponse(
                part_number=part.part_number,
                etag=part.etag,
                size_bytes=part.size_bytes,
                checksum=part.checksum,
            )
            for part in inspection.parts
        ],
    )


@router.delete("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
async def abort_upload(
    upload_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
    storage: S3ObjectStorage = Depends(get_object_storage),
) -> Response:
    await UploadLifecycleService(
        uploads=SqlAlchemyUploadRepository(session),
        videos=SqlAlchemyVideoRepository(session),
        storage=storage,
    ).abort(owner_id=current_user.id, upload_id=upload_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{upload_id}/complete", response_model=CompleteUploadResponse)
async def complete_upload(
    upload_id: str,
    body: CompleteUploadRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
    storage: S3ObjectStorage = Depends(get_object_storage),
) -> CompleteUploadResponse:
    video = await CompleteUploadService(
        settings=get_settings(),
        uploads=SqlAlchemyUploadRepository(session),
        videos=SqlAlchemyVideoRepository(session),
        storage=storage,
    ).complete(
        owner_id=current_user.id,
        upload_id=upload_id,
        client_parts=[
            StoredPart(
                part_number=part.part_number,
                etag=part.etag,
                size_bytes=part.size_bytes,
            )
            for part in body.parts
        ],
    )
    return CompleteUploadResponse(
        video_id=video.id,
        storage_path=video.storage_path or "",
        playback_url=video.playback_url or "",
    )
