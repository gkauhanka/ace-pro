from dataclasses import dataclass

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ace_pro_api.domain.enums import AnalysisStatus, VideoStatus
from ace_pro_api.errors import ApiError
from ace_pro_api.media import ClipArtifact
from ace_pro_api.persistence.models import Base, Video
from ace_pro_api.persistence.repositories import (
    SqlAlchemyAnalysisRepository,
    SqlAlchemyVideoRepository,
)
from ace_pro_api.services.analysis import (
    AnalysisService,
    PointAnnotation,
    ReturnAnnotation,
)


class FakeMediaProcessor:
    async def inspect(self, _video: Video) -> dict:
        return {
            "duration_seconds": 3600.0,
            "codec": "h264",
            "width": 1920,
            "height": 1080,
            "average_frame_rate": "30/1",
            "inspection_version": "fake-1",
        }

    async def generate_clips(
        self, *, video: Video, job_id: str, points: list
    ) -> list[ClipArtifact]:
        return [
            ClipArtifact(
                point_id=point.id,
                object_key=f"videos/{video.id}/analysis/{job_id}/clips/{point.id}.mp4",
                playback_url=f"https://media.example/{point.id}.mp4",
            )
            for point in points
        ]


@dataclass
class AnalysisHarness:
    session: AsyncSession
    service: AnalysisService
    analyses: SqlAlchemyAnalysisRepository


async def make_harness() -> tuple[AnalysisHarness, object]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    session = factory()
    videos = SqlAlchemyVideoRepository(session)
    analyses = SqlAlchemyAnalysisRepository(session)
    await videos.add(
        Video(
            id="video-id",
            owner_id="owner-1",
            original_filename="match.mp4",
            content_type="video/mp4",
            container="mp4",
            codec="h264",
            declared_size_bytes=100,
            declared_duration_seconds=3600,
            final_size_bytes=100,
            bucket="bucket",
            object_key="videos/random/original.mp4",
            status=VideoStatus.READY.value,
            storage_path="s3://bucket/videos/random/original.mp4",
            playback_url="https://media.example/original.mp4",
        )
    )
    service = AnalysisService(
        analyses=analyses,
        videos=videos,
        media=FakeMediaProcessor(),
    )
    return AnalysisHarness(session, service, analyses), engine


def annotation(
    sequence: int, *, zone: str, winner: str, stroke: str = "backhand"
) -> PointAnnotation:
    start = sequence * 10_000
    return PointAnnotation(
        sequence_number=sequence,
        start_ms=start,
        end_ms=start + 8_000,
        winner_role=winner,
        return_event=ReturnAnnotation(
            timestamp_ms=start + 2_000,
            stroke_side=stroke,
            landing_zone=zone,
        ),
    )


def match_annotations() -> list[PointAnnotation]:
    short = [
        annotation(index, zone="short", winner="opponent" if index <= 7 else "target")
        for index in range(1, 12)
    ]
    deep = [
        annotation(index, zone="deep", winner="opponent" if index <= 14 else "target")
        for index in range(12, 20)
    ]
    return short + deep


@pytest.mark.anyio
async def test_manual_annotations_produce_evidence_backed_insight() -> None:
    harness, engine = await make_harness()
    try:
        job = await harness.service.create(owner_id="owner-1", video_id="video-id")

        assert job.status == AnalysisStatus.AWAITING_ANNOTATIONS.value
        assert job.media_metadata["codec"] == "h264"

        completed = await harness.service.import_annotations(
            owner_id="owner-1",
            job_id=job.id,
            annotations=match_annotations(),
        )
        reloaded = await harness.service.get(owner_id="owner-1", job_id=job.id)
        points = list(await harness.analyses.list_points(job.id))

        assert completed.status == AnalysisStatus.READY.value
        assert completed.progress == 1.0
        assert len(points) == 19
        assert all(point.clip and point.clip.playback_url for point in points)
        assert len(reloaded.insights) == 1
        insight = reloaded.insights[0]
        assert insight.status == "published"
        assert insight.metrics["short"] == {
            "points": 11,
            "losses": 7,
            "loss_rate": 0.6364,
        }
        assert insight.metrics["deep"] == {
            "points": 8,
            "losses": 3,
            "loss_rate": 0.375,
        }
        assert len(insight.evidence_event_ids) == 19
    finally:
        await harness.session.close()
        await engine.dispose()


@pytest.mark.anyio
async def test_correction_is_preserved_and_recalculates_insight() -> None:
    harness, engine = await make_harness()
    try:
        job = await harness.service.create(owner_id="owner-1", video_id="video-id")
        await harness.service.import_annotations(
            owner_id="owner-1", job_id=job.id, annotations=match_annotations()
        )
        points = list(await harness.analyses.list_points(job.id))
        event = points[0].events[0]

        corrected, insight = await harness.service.correct_event(
            owner_id="owner-1",
            event_id=event.id,
            base_revision=0,
            corrected_fields={"winner_role": "target"},
            reason="reviewed_clip",
        )

        assert corrected.revision == 1
        assert corrected.predicted_attributes == {
            "stroke_side": "backhand",
            "landing_zone": "short",
        }
        assert len(corrected.corrections) == 1
        assert insight.snapshot_version == 2
        assert insight.metrics["short"]["losses"] == 6

        with pytest.raises(ApiError) as raised:
            await harness.service.correct_event(
                owner_id="owner-1",
                event_id=event.id,
                base_revision=0,
                corrected_fields={"landing_zone": "deep"},
                reason=None,
            )
        assert raised.value.code == "event_revision_conflict"
    finally:
        await harness.session.close()
        await engine.dispose()


@pytest.mark.anyio
async def test_analysis_creation_is_idempotent() -> None:
    harness, engine = await make_harness()
    try:
        first = await harness.service.create(owner_id="owner-1", video_id="video-id")
        second = await harness.service.create(owner_id="owner-1", video_id="video-id")

        assert second.id == first.id
    finally:
        await harness.session.close()
        await engine.dispose()


@pytest.mark.anyio
async def test_annotation_timestamps_must_fall_inside_video_and_point() -> None:
    harness, engine = await make_harness()
    try:
        job = await harness.service.create(owner_id="owner-1", video_id="video-id")
        invalid = PointAnnotation(
            sequence_number=1,
            start_ms=1000,
            end_ms=2000,
            winner_role="target",
            return_event=ReturnAnnotation(
                timestamp_ms=3000,
                stroke_side="backhand",
                landing_zone="short",
            ),
        )

        with pytest.raises(ApiError) as raised:
            await harness.service.import_annotations(
                owner_id="owner-1", job_id=job.id, annotations=[invalid]
            )
        assert raised.value.code == "invalid_return_time"
    finally:
        await harness.session.close()
        await engine.dispose()
