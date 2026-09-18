from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ace_pro_api.api.dependencies import get_database_session, get_media_processor
from ace_pro_api.domain.enums import VideoStatus
from ace_pro_api.main import create_app
from ace_pro_api.media import ClipArtifact
from ace_pro_api.persistence.models import Base, Video


class ApiFakeMediaProcessor:
    async def inspect(self, _video: Video) -> dict:
        return {"duration_seconds": 600.0, "codec": "h264", "inspection_version": "fake-1"}

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


def api_points() -> list[dict]:
    points = []
    for sequence in range(1, 10):
        short = sequence <= 6
        points.append(
            {
                "sequence_number": sequence,
                "start_ms": sequence * 10_000,
                "end_ms": sequence * 10_000 + 8_000,
                "winner_role": ("opponent" if sequence in {1, 2, 3, 4, 7} else "target"),
                "return_event": {
                    "timestamp_ms": sequence * 10_000 + 2_000,
                    "stroke_side": "backhand",
                    "landing_zone": "short" if short else "deep",
                },
            }
        )
    return points


@pytest.mark.anyio
async def test_analysis_http_flow_imports_evidence_and_accepts_correction() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        session.add(
            Video(
                id="video-id",
                owner_id="local-test-user",
                original_filename="match.mp4",
                content_type="video/mp4",
                container="mp4",
                codec="h264",
                declared_size_bytes=100,
                declared_duration_seconds=600,
                final_size_bytes=100,
                bucket="bucket",
                object_key="videos/random/original.mp4",
                status=VideoStatus.READY.value,
            )
        )
        await session.commit()

    async def database_override() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app = create_app()
    app.dependency_overrides[get_database_session] = database_override
    app.dependency_overrides[get_media_processor] = lambda: ApiFakeMediaProcessor()

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            review = await client.get("/analysis-review")
            assert review.status_code == 200
            assert "text/html" in review.headers["content-type"]
            assert "Save correction and recalculate" in review.text
            created = await client.post("/api/v1/videos/video-id/analyses")
            assert created.status_code == 201
            analysis_id = created.json()["analysis_id"]
            assert created.json()["status"] == "awaiting_annotations"

            imported = await client.post(
                f"/api/v1/analyses/{analysis_id}/annotations",
                json={"points": api_points()},
            )
            assert imported.status_code == 200
            report = imported.json()
            assert report["analysis"]["status"] == "ready"
            assert report["insights"][0]["status"] == "published"
            assert len(report["evidence"]) == 9
            assert all(item["clip_playback_url"] for item in report["evidence"])

            event = report["evidence"][0]
            corrected = await client.post(
                f"/api/v1/events/{event['event_id']}/corrections",
                json={
                    "base_revision": event["event_revision"],
                    "winner_role": "target",
                    "reason": "reviewed_clip",
                },
            )
            assert corrected.status_code == 200
            assert corrected.json()["revision"] == 1
            assert corrected.json()["insight"]["metrics"]["short"]["losses"] == 3

            refreshed = await client.get(f"/api/v1/analyses/{analysis_id}")
            assert refreshed.status_code == 200
            assert refreshed.json()["analysis"]["snapshot_version"] == 2
            assert refreshed.json()["evidence"][0]["winner_role"] == "target"
    finally:
        await engine.dispose()
