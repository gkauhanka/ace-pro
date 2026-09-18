from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from ace_pro_api.persistence.models import (
    AnalysisEvent,
    AnalysisJob,
    AnalyzedPoint,
    EventCorrection,
    Insight,
    UploadPart,
    UploadSession,
    Video,
)


class VideoRepository(Protocol):
    async def add(self, video: Video) -> Video: ...

    async def get(self, video_id: str) -> Video | None: ...

    async def save(self, video: Video) -> Video: ...


class UploadRepository(Protocol):
    async def add_session(self, upload: UploadSession) -> UploadSession: ...

    async def get_session(self, upload_id: str) -> UploadSession | None: ...

    async def get_by_idempotency_key(self, key: str) -> UploadSession | None: ...

    async def save_session(self, upload: UploadSession) -> UploadSession: ...

    async def replace_parts(
        self, upload_id: str, parts: Sequence[UploadPart]
    ) -> Sequence[UploadPart]: ...

    async def list_parts(self, upload_id: str) -> Sequence[UploadPart]: ...

    async def list_expired_active(
        self, *, now: datetime, limit: int
    ) -> Sequence[UploadSession]: ...


class AnalysisRepository(Protocol):
    async def add_job(self, job: AnalysisJob) -> AnalysisJob: ...

    async def get_job(self, job_id: str) -> AnalysisJob | None: ...

    async def get_by_video_version(
        self, video_id: str, pipeline_version: str
    ) -> AnalysisJob | None: ...

    async def save_job(self, job: AnalysisJob) -> AnalysisJob: ...

    async def replace_points(
        self, job_id: str, points: Sequence[AnalyzedPoint]
    ) -> Sequence[AnalyzedPoint]: ...

    async def list_points(self, job_id: str) -> Sequence[AnalyzedPoint]: ...

    async def replace_insight(self, job_id: str, insight: Insight) -> Insight: ...

    async def get_event(self, event_id: str) -> AnalysisEvent | None: ...

    async def add_correction(self, correction: EventCorrection) -> EventCorrection: ...

    async def save_event(self, event: AnalysisEvent) -> AnalysisEvent: ...
