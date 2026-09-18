from dataclasses import dataclass
from datetime import UTC, datetime
from statistics import fmean
from uuid import uuid4

from ace_pro_api.domain.enums import AnalysisStatus, ClipStatus, VideoStatus
from ace_pro_api.domain.repositories import AnalysisRepository, VideoRepository
from ace_pro_api.errors import ApiError
from ace_pro_api.media import MediaProcessor
from ace_pro_api.persistence.models import (
    AnalysisEvent,
    AnalysisJob,
    AnalyzedPoint,
    EventCorrection,
    EvidenceClip,
    Insight,
)

PIPELINE_VERSION = "manual-return-depth-1"
RULE_VERSION = "return-depth-1"
MIN_SHORT_SAMPLE = 6
MIN_DEEP_SAMPLE = 3
MIN_EFFECT_DIFFERENCE = 0.15


@dataclass(frozen=True)
class ReturnAnnotation:
    timestamp_ms: int
    stroke_side: str
    landing_zone: str
    confidence: float = 1.0


@dataclass(frozen=True)
class PointAnnotation:
    sequence_number: int
    start_ms: int
    end_ms: int
    winner_role: str
    return_event: ReturnAnnotation
    confidence: float = 1.0


def effective_event(event: AnalysisEvent) -> dict:
    attributes = dict(event.predicted_attributes)
    if event.corrections:
        latest = max(
            event.corrections,
            key=lambda correction: (correction.base_revision, correction.created_at),
        )
        attributes.update(latest.corrected_fields)
    return attributes


class AnalysisService:
    def __init__(
        self,
        *,
        analyses: AnalysisRepository,
        videos: VideoRepository,
        media: MediaProcessor,
    ) -> None:
        self._analyses = analyses
        self._videos = videos
        self._media = media

    async def create(self, *, owner_id: str, video_id: str) -> AnalysisJob:
        video = await self._owned_ready_video(owner_id=owner_id, video_id=video_id)
        existing = await self._analyses.get_by_video_version(video.id, PIPELINE_VERSION)
        if existing is not None:
            return existing

        job = AnalysisJob(
            id=str(uuid4()),
            video_id=video.id,
            pipeline_version=PIPELINE_VERSION,
            status=AnalysisStatus.INSPECTING.value,
            stage="media_inspection",
            progress=0.05,
        )
        await self._analyses.add_job(job)
        try:
            job.media_metadata = await self._media.inspect(video)
            job.status = AnalysisStatus.AWAITING_ANNOTATIONS.value
            job.stage = "manual_annotation"
            job.progress = 0.20
        except Exception:
            job.status = AnalysisStatus.FAILED.value
            job.stage = "media_inspection"
            job.failure_code = "media_inspection_failed"
            job.failure_message = "The uploaded video could not be inspected."
        return await self._analyses.save_job(job)

    async def get(self, *, owner_id: str, job_id: str) -> AnalysisJob:
        job = await self._analyses.get_job(job_id)
        if job is None or job.video.owner_id != owner_id:
            raise ApiError(404, "analysis_not_found", "Analysis was not found.")
        return job

    async def import_annotations(
        self, *, owner_id: str, job_id: str, annotations: list[PointAnnotation]
    ) -> AnalysisJob:
        job = await self.get(owner_id=owner_id, job_id=job_id)
        if job.status not in {
            AnalysisStatus.AWAITING_ANNOTATIONS.value,
            AnalysisStatus.READY.value,
            AnalysisStatus.FAILED.value,
        }:
            raise ApiError(409, "analysis_not_editable", "Analysis cannot accept annotations.")
        self._validate_annotations(job, annotations)

        points = [self._point_from_annotation(job.id, annotation) for annotation in annotations]
        await self._analyses.replace_points(job.id, points)
        job.snapshot_version += 1
        job.status = AnalysisStatus.GENERATING_CLIPS.value
        job.stage = "evidence_clips"
        job.progress = 0.70
        job.failure_code = None
        job.failure_message = None
        await self._analyses.save_job(job)

        clips_by_point = {
            point.id: EvidenceClip(
                id=str(uuid4()),
                job_id=job.id,
                point_id=point.id,
                start_ms=max(0, point.start_ms - 3_000),
                end_ms=point.end_ms + 2_000,
                status=ClipStatus.PENDING.value,
            )
            for point in points
        }
        for point in points:
            point.clip = clips_by_point[point.id]

        try:
            artifacts = await self._media.generate_clips(
                video=job.video, job_id=job.id, points=points
            )
            for artifact in artifacts:
                clip = clips_by_point[artifact.point_id]
                clip.object_key = artifact.object_key
                clip.playback_url = artifact.playback_url
                clip.status = ClipStatus.READY.value
            if len(artifacts) != len(points):
                raise RuntimeError("Media processor returned an incomplete clip set.")
        except Exception:
            for clip in clips_by_point.values():
                if clip.status != ClipStatus.READY.value:
                    clip.status = ClipStatus.FAILED.value
                    clip.failure_code = "clip_generation_failed"
            job.status = AnalysisStatus.FAILED.value
            job.failure_code = "clip_generation_failed"
            job.failure_message = "Evidence clips could not be generated."
            return await self._analyses.save_job(job)

        await self._calculate(job=job, points=points)
        job.status = AnalysisStatus.READY.value
        job.stage = "complete"
        job.progress = 1.0
        job.completed_at = datetime.now(UTC)
        return await self._analyses.save_job(job)

    async def correct_event(
        self,
        *,
        owner_id: str,
        event_id: str,
        base_revision: int,
        corrected_fields: dict,
        reason: str | None,
    ) -> tuple[AnalysisEvent, Insight]:
        event = await self._analyses.get_event(event_id)
        if event is None or event.point.job.video.owner_id != owner_id:
            raise ApiError(404, "event_not_found", "Analysis event was not found.")
        if event.revision != base_revision:
            raise ApiError(
                409,
                "event_revision_conflict",
                "The event was changed by another review.",
                {"current_revision": event.revision},
            )
        self._validate_correction(corrected_fields)
        correction = EventCorrection(
            id=str(uuid4()),
            event_id=event.id,
            base_revision=base_revision,
            corrected_fields=corrected_fields,
            actor_id=owner_id,
            reason=reason,
        )
        await self._analyses.add_correction(correction)
        event.corrections.append(correction)
        event.revision += 1
        await self._analyses.save_event(event)

        job = event.point.job
        job.snapshot_version += 1
        points = list(await self._analyses.list_points(job.id))
        insight = await self._calculate(job=job, points=points)
        await self._analyses.save_job(job)
        return event, insight

    async def _calculate(self, *, job: AnalysisJob, points: list[AnalyzedPoint]) -> Insight:
        groups: dict[str, list[tuple[AnalyzedPoint, AnalysisEvent, dict]]] = {
            "short": [],
            "deep": [],
        }
        for point in points:
            for event in point.events:
                if event.event_type != "return":
                    continue
                attributes = effective_event(event)
                if attributes.get("stroke_side") != "backhand":
                    continue
                zone = attributes.get("landing_zone")
                if zone in groups:
                    groups[zone].append((point, event, attributes))

        metrics: dict[str, dict[str, float | int]] = {}
        for zone, items in groups.items():
            losses = sum(
                1
                for point, _event, attributes in items
                if attributes.get("winner_role", point.winner_role) == "opponent"
            )
            count = len(items)
            metrics[zone] = {
                "points": count,
                "losses": losses,
                "loss_rate": round(losses / count, 4) if count else 0.0,
            }

        short_rate = float(metrics["short"]["loss_rate"])
        deep_rate = float(metrics["deep"]["loss_rate"])
        difference = round(short_rate - deep_rate, 4)
        metrics["comparison"] = {"loss_rate_difference": difference}
        eligible = groups["short"] + groups["deep"]
        confidence = round(fmean(item[1].confidence for item in eligible), 4) if eligible else 0.0
        publishable = (
            int(metrics["short"]["points"]) >= MIN_SHORT_SAMPLE
            and int(metrics["deep"]["points"]) >= MIN_DEEP_SAMPLE
            and difference >= MIN_EFFECT_DIFFERENCE
        )
        short_losses = int(metrics["short"]["losses"])
        short_count = int(metrics["short"]["points"])
        summary = (
            f"You lost {short_losses} of {short_count} points "
            f"({round(short_rate * 100)}%) after a short backhand return."
            if short_count
            else "No eligible short backhand returns were found."
        )
        insight = Insight(
            id=str(uuid4()),
            job_id=job.id,
            insight_type="backhand_return_depth",
            rule_version=RULE_VERSION,
            snapshot_version=job.snapshot_version,
            rank=1,
            metrics=metrics,
            confidence=confidence,
            status="published" if publishable else "insufficient_data",
            title=(
                "Short backhand returns were costly"
                if publishable
                else "More return evidence is needed"
            ),
            summary=summary,
            evidence_event_ids=[item[1].id for item in eligible],
        )
        return await self._analyses.replace_insight(job.id, insight)

    async def _owned_ready_video(self, *, owner_id: str, video_id: str):
        video = await self._videos.get(video_id)
        if video is None or video.owner_id != owner_id:
            raise ApiError(404, "video_not_found", "Video was not found.")
        if video.status != VideoStatus.READY.value:
            raise ApiError(409, "video_not_ready", "Video must be ready before analysis.")
        return video

    @staticmethod
    def _point_from_annotation(job_id: str, annotation: PointAnnotation) -> AnalyzedPoint:
        point = AnalyzedPoint(
            id=str(uuid4()),
            job_id=job_id,
            sequence_number=annotation.sequence_number,
            start_ms=annotation.start_ms,
            end_ms=annotation.end_ms,
            winner_role=annotation.winner_role,
            confidence=annotation.confidence,
        )
        point.events.append(
            AnalysisEvent(
                id=str(uuid4()),
                event_type="return",
                timestamp_ms=annotation.return_event.timestamp_ms,
                player_role="target",
                predicted_attributes={
                    "stroke_side": annotation.return_event.stroke_side,
                    "landing_zone": annotation.return_event.landing_zone,
                },
                confidence=annotation.return_event.confidence,
                model_version="manual-1",
                corrections=[],
            )
        )
        return point

    @staticmethod
    def _validate_annotations(job: AnalysisJob, annotations: list[PointAnnotation]) -> None:
        if not annotations:
            raise ApiError(422, "annotations_empty", "At least one point is required.")
        sequence_numbers = [annotation.sequence_number for annotation in annotations]
        if len(sequence_numbers) != len(set(sequence_numbers)):
            raise ApiError(422, "duplicate_point", "Point sequence numbers must be unique.")
        duration_ms = int(float((job.media_metadata or {}).get("duration_seconds", 0)) * 1000)
        for annotation in annotations:
            if annotation.start_ms >= annotation.end_ms:
                raise ApiError(422, "invalid_point_range", "Point start must precede its end.")
            if not annotation.start_ms <= annotation.return_event.timestamp_ms <= annotation.end_ms:
                raise ApiError(422, "invalid_return_time", "Return must occur inside its point.")
            if duration_ms and annotation.end_ms > duration_ms:
                raise ApiError(422, "point_out_of_range", "Point exceeds the video duration.")

    @staticmethod
    def _validate_correction(fields: dict) -> None:
        allowed = {"stroke_side", "landing_zone", "winner_role"}
        if not fields or not set(fields).issubset(allowed):
            raise ApiError(422, "invalid_correction", "Correction contains unsupported fields.")
        if "stroke_side" in fields and fields["stroke_side"] not in {
            "forehand",
            "backhand",
            "unknown",
        }:
            raise ApiError(422, "invalid_correction", "Invalid stroke side.")
        if "landing_zone" in fields and fields["landing_zone"] not in {
            "short",
            "deep",
            "unknown",
        }:
            raise ApiError(422, "invalid_correction", "Invalid landing zone.")
        if "winner_role" in fields and fields["winner_role"] not in {
            "target",
            "opponent",
            "unknown",
        }:
            raise ApiError(422, "invalid_correction", "Invalid point winner.")
