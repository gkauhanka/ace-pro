from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ace_pro_api.domain.enums import UploadStatus
from ace_pro_api.persistence.models import UploadPart, UploadSession, Video


class SqlAlchemyVideoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, video: Video) -> Video:
        self._session.add(video)
        await self._session.flush()
        return video

    async def get(self, video_id: str) -> Video | None:
        return await self._session.scalar(
            select(Video).options(selectinload(Video.upload)).where(Video.id == video_id)
        )

    async def save(self, video: Video) -> Video:
        saved = await self._session.merge(video)
        await self._session.flush()
        return saved


class SqlAlchemyUploadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_session(self, upload: UploadSession) -> UploadSession:
        self._session.add(upload)
        await self._session.flush()
        return upload

    async def get_session(self, upload_id: str) -> UploadSession | None:
        return await self._session.scalar(
            select(UploadSession)
            .options(selectinload(UploadSession.video))
            .where(UploadSession.id == upload_id)
        )

    async def get_by_idempotency_key(self, key: str) -> UploadSession | None:
        return await self._session.scalar(
            select(UploadSession)
            .options(selectinload(UploadSession.video))
            .where(UploadSession.idempotency_key == key)
        )

    async def save_session(self, upload: UploadSession) -> UploadSession:
        saved = await self._session.merge(upload)
        await self._session.flush()
        return saved

    async def replace_parts(
        self, upload_id: str, parts: Sequence[UploadPart]
    ) -> Sequence[UploadPart]:
        await self._session.execute(delete(UploadPart).where(UploadPart.upload_id == upload_id))
        self._session.add_all(parts)
        await self._session.flush()
        return parts

    async def list_parts(self, upload_id: str) -> Sequence[UploadPart]:
        result = await self._session.scalars(
            select(UploadPart)
            .where(UploadPart.upload_id == upload_id)
            .order_by(UploadPart.part_number)
        )
        return result.all()

    async def list_expired_active(
        self, *, now: datetime, limit: int
    ) -> Sequence[UploadSession]:
        result = await self._session.scalars(
            select(UploadSession)
            .options(selectinload(UploadSession.video))
            .where(
                UploadSession.expires_at <= now,
                UploadSession.status.in_(
                    [UploadStatus.PENDING.value, UploadStatus.UPLOADING.value]
                ),
            )
            .order_by(UploadSession.expires_at)
            .limit(limit)
        )
        return result.all()
