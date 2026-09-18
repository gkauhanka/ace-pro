from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from ace_pro_api.api.dependencies import (
    get_current_user,
    get_database_session,
    get_media_processor,
)
from ace_pro_api.auth import CurrentUser
from ace_pro_api.media import MediaProcessor
from ace_pro_api.persistence.models import AnalysisJob, Insight
from ace_pro_api.persistence.repositories import (
    SqlAlchemyAnalysisRepository,
    SqlAlchemyVideoRepository,
)
from ace_pro_api.services.analysis import (
    AnalysisService,
    PointAnnotation,
    ReturnAnnotation,
    effective_event,
)

router = APIRouter(prefix="/api/v1", tags=["analysis"])


class AnalysisResponse(BaseModel):
    analysis_id: str
    video_id: str
    status: str
    stage: str
    progress: float
    pipeline_version: str
    snapshot_version: int
    media_metadata: dict | None
    failure_code: str | None
    failure_message: str | None
    created_at: datetime
    completed_at: datetime | None


class ReturnAnnotationRequest(BaseModel):
    timestamp_ms: int = Field(ge=0)
    stroke_side: Literal["forehand", "backhand", "unknown"]
    landing_zone: Literal["short", "deep", "unknown"]
    confidence: float = Field(default=1.0, ge=0, le=1)


class PointAnnotationRequest(BaseModel):
    sequence_number: int = Field(ge=1)
    start_ms: int = Field(ge=0)
    end_ms: int = Field(gt=0)
    winner_role: Literal["target", "opponent", "unknown"]
    confidence: float = Field(default=1.0, ge=0, le=1)
    return_event: ReturnAnnotationRequest


class ImportAnnotationsRequest(BaseModel):
    points: list[PointAnnotationRequest] = Field(min_length=1, max_length=1000)


class MetricGroup(BaseModel):
    points: int
    losses: int
    loss_rate: float


class ComparisonMetrics(BaseModel):
    loss_rate_difference: float


class InsightMetrics(BaseModel):
    short: MetricGroup
    deep: MetricGroup
    comparison: ComparisonMetrics


class InsightResponse(BaseModel):
    insight_id: str
    insight_type: str
    rule_version: str
    snapshot_version: int
    rank: int
    status: str
    title: str
    summary: str
    confidence: float
    metrics: InsightMetrics
    evidence_event_ids: list[str]


class EvidenceResponse(BaseModel):
    event_id: str
    event_revision: int
    point_number: int
    point_start_ms: int
    point_end_ms: int
    winner_role: str
    return_timestamp_ms: int
    stroke_side: str
    landing_zone: str
    confidence: float
    clip_status: str | None
    clip_playback_url: str | None


class AnalysisReportResponse(BaseModel):
    analysis: AnalysisResponse
    insights: list[InsightResponse]
    evidence: list[EvidenceResponse]


class CorrectionRequest(BaseModel):
    base_revision: int = Field(ge=0)
    stroke_side: Literal["forehand", "backhand", "unknown"] | None = None
    landing_zone: Literal["short", "deep", "unknown"] | None = None
    winner_role: Literal["target", "opponent", "unknown"] | None = None
    reason: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def ensure_changed_field(self):
        if self.stroke_side is None and self.landing_zone is None and self.winner_role is None:
            raise ValueError("At least one corrected field is required.")
        return self


class CorrectionResponse(BaseModel):
    event_id: str
    revision: int
    insight: InsightResponse


def analysis_response(job: AnalysisJob) -> AnalysisResponse:
    return AnalysisResponse(
        analysis_id=job.id,
        video_id=job.video_id,
        status=job.status,
        stage=job.stage,
        progress=job.progress,
        pipeline_version=job.pipeline_version,
        snapshot_version=job.snapshot_version,
        media_metadata=job.media_metadata,
        failure_code=job.failure_code,
        failure_message=job.failure_message,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


def insight_response(insight: Insight) -> InsightResponse:
    return InsightResponse(
        insight_id=insight.id,
        insight_type=insight.insight_type,
        rule_version=insight.rule_version,
        snapshot_version=insight.snapshot_version,
        rank=insight.rank,
        status=insight.status,
        title=insight.title,
        summary=insight.summary,
        confidence=insight.confidence,
        metrics=InsightMetrics.model_validate(insight.metrics),
        evidence_event_ids=list(insight.evidence_event_ids),
    )


def service_for(
    session: AsyncSession, media: MediaProcessor
) -> tuple[AnalysisService, SqlAlchemyAnalysisRepository]:
    analyses = SqlAlchemyAnalysisRepository(session)
    return (
        AnalysisService(
            analyses=analyses,
            videos=SqlAlchemyVideoRepository(session),
            media=media,
        ),
        analyses,
    )


async def report_for(
    *, service: AnalysisService, analyses: SqlAlchemyAnalysisRepository, owner_id: str, job_id: str
) -> AnalysisReportResponse:
    job = await service.get(owner_id=owner_id, job_id=job_id)
    points = await analyses.list_points(job.id)
    evidence = []
    for point in points:
        for event in point.events:
            if event.event_type != "return":
                continue
            attributes = effective_event(event)
            evidence.append(
                EvidenceResponse(
                    event_id=event.id,
                    event_revision=event.revision,
                    point_number=point.sequence_number,
                    point_start_ms=point.start_ms,
                    point_end_ms=point.end_ms,
                    winner_role=attributes.get("winner_role", point.winner_role),
                    return_timestamp_ms=event.timestamp_ms,
                    stroke_side=attributes.get("stroke_side", "unknown"),
                    landing_zone=attributes.get("landing_zone", "unknown"),
                    confidence=event.confidence,
                    clip_status=point.clip.status if point.clip else None,
                    clip_playback_url=point.clip.playback_url if point.clip else None,
                )
            )
    return AnalysisReportResponse(
        analysis=analysis_response(job),
        insights=[insight_response(insight) for insight in job.insights],
        evidence=evidence,
    )


@router.post(
    "/videos/{video_id}/analyses",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_analysis(
    video_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
    media: MediaProcessor = Depends(get_media_processor),
) -> AnalysisResponse:
    service, _analyses = service_for(session, media)
    job = await service.create(owner_id=current_user.id, video_id=video_id)
    return analysis_response(job)


@router.get("/analyses/{analysis_id}", response_model=AnalysisReportResponse)
async def get_analysis(
    analysis_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
    media: MediaProcessor = Depends(get_media_processor),
) -> AnalysisReportResponse:
    service, analyses = service_for(session, media)
    return await report_for(
        service=service, analyses=analyses, owner_id=current_user.id, job_id=analysis_id
    )


@router.post("/analyses/{analysis_id}/annotations", response_model=AnalysisReportResponse)
async def import_annotations(
    analysis_id: str,
    body: ImportAnnotationsRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
    media: MediaProcessor = Depends(get_media_processor),
) -> AnalysisReportResponse:
    service, analyses = service_for(session, media)
    await service.import_annotations(
        owner_id=current_user.id,
        job_id=analysis_id,
        annotations=[
            PointAnnotation(
                sequence_number=point.sequence_number,
                start_ms=point.start_ms,
                end_ms=point.end_ms,
                winner_role=point.winner_role,
                confidence=point.confidence,
                return_event=ReturnAnnotation(**point.return_event.model_dump()),
            )
            for point in body.points
        ],
    )
    return await report_for(
        service=service, analyses=analyses, owner_id=current_user.id, job_id=analysis_id
    )


@router.post("/events/{event_id}/corrections", response_model=CorrectionResponse)
async def correct_event(
    event_id: str,
    body: CorrectionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session),
    media: MediaProcessor = Depends(get_media_processor),
) -> CorrectionResponse:
    service, _analyses = service_for(session, media)
    fields = {
        key: value
        for key, value in body.model_dump(
            include={"stroke_side", "landing_zone", "winner_role"}
        ).items()
        if value is not None
    }
    event, insight = await service.correct_event(
        owner_id=current_user.id,
        event_id=event_id,
        base_revision=body.base_revision,
        corrected_fields=fields,
        reason=body.reason,
    )
    return CorrectionResponse(
        event_id=event.id,
        revision=event.revision,
        insight=insight_response(insight),
    )
