from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ace_pro_api.domain.enums import UploadStatus
from ace_pro_api.persistence.models import (
    AnalysisEvent,
    AnalysisJob,
    AnalyzedPoint,
    EventCorrection,
    EvidenceClip,
    Insight,
    UploadPart,
    UploadSession,
    Video,
)


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

    async def list_expired_active(self, *, now: datetime, limit: int) -> Sequence[UploadSession]:
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


class SqlAlchemyAnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_job(self, job: AnalysisJob) -> AnalysisJob:
        self._session.add(job)
        await self._session.flush()
        return job

    async def get_job(self, job_id: str) -> AnalysisJob | None:
        return await self._session.scalar(
            select(AnalysisJob)
            .execution_options(populate_existing=True)
            .options(
                selectinload(AnalysisJob.video),
                selectinload(AnalysisJob.insights),
                selectinload(AnalysisJob.clips),
            )
            .where(AnalysisJob.id == job_id)
        )

    async def get_by_video_version(
        self, video_id: str, pipeline_version: str
    ) -> AnalysisJob | None:
        return await self._session.scalar(
            select(AnalysisJob).where(
                AnalysisJob.video_id == video_id,
                AnalysisJob.pipeline_version == pipeline_version,
            )
        )

    async def save_job(self, job: AnalysisJob) -> AnalysisJob:
        saved = await self._session.merge(job)
        await self._session.flush()
        return saved

    async def replace_points(
        self, job_id: str, points: Sequence[AnalyzedPoint]
    ) -> Sequence[AnalyzedPoint]:
        point_ids = select(AnalyzedPoint.id).where(AnalyzedPoint.job_id == job_id)
        event_ids = select(AnalysisEvent.id).where(AnalysisEvent.point_id.in_(point_ids))
        await self._session.execute(
            delete(EventCorrection).where(EventCorrection.event_id.in_(event_ids))
        )
        await self._session.execute(
            delete(AnalysisEvent).where(AnalysisEvent.point_id.in_(point_ids))
        )
        await self._session.execute(delete(EvidenceClip).where(EvidenceClip.job_id == job_id))
        await self._session.execute(delete(Insight).where(Insight.job_id == job_id))
        await self._session.execute(delete(AnalyzedPoint).where(AnalyzedPoint.job_id == job_id))
        self._session.add_all(points)
        await self._session.flush()
        return points

    async def list_points(self, job_id: str) -> Sequence[AnalyzedPoint]:
        result = await self._session.scalars(
            select(AnalyzedPoint)
            .options(
                selectinload(AnalyzedPoint.events).selectinload(AnalysisEvent.corrections),
                selectinload(AnalyzedPoint.clip),
            )
            .where(AnalyzedPoint.job_id == job_id)
            .order_by(AnalyzedPoint.sequence_number)
        )
        return result.all()

    async def replace_insight(self, job_id: str, insight: Insight) -> Insight:
        await self._session.execute(delete(Insight).where(Insight.job_id == job_id))
        self._session.add(insight)
        await self._session.flush()
        return insight

    async def get_event(self, event_id: str) -> AnalysisEvent | None:
        return await self._session.scalar(
            select(AnalysisEvent)
            .options(
                selectinload(AnalysisEvent.corrections),
                selectinload(AnalysisEvent.point)
                .selectinload(AnalyzedPoint.job)
                .selectinload(AnalysisJob.video),
            )
            .where(AnalysisEvent.id == event_id)
        )

    async def add_correction(self, correction: EventCorrection) -> EventCorrection:
        self._session.add(correction)
        await self._session.flush()
        return correction

    async def save_event(self, event: AnalysisEvent) -> AnalysisEvent:
        saved = await self._session.merge(event)
        await self._session.flush()
        return saved
