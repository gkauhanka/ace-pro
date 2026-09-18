import shutil
import subprocess
from pathlib import Path

import pytest

from ace_pro_api.config import Settings
from ace_pro_api.media import FFmpegMediaProcessor
from ace_pro_api.persistence.models import AnalyzedPoint, Video


class LocalFileStorage:
    def __init__(self, source: Path, output_directory: Path) -> None:
        self.source = source
        self.output_directory = output_directory

    async def download_file(self, *, bucket: str, key: str, destination: str) -> None:
        del bucket, key
        shutil.copyfile(self.source, destination)

    async def upload_file(self, *, bucket: str, key: str, source: str, content_type: str) -> None:
        del bucket, content_type
        destination = self.output_directory / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)


@pytest.mark.anyio
async def test_ffmpeg_processor_inspects_and_generates_playable_clip(tmp_path: Path) -> None:
    source = tmp_path / "source.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=green:s=320x240:d=3:r=30",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(source),
        ],
        check=True,
        timeout=30,
    )
    storage = LocalFileStorage(source, tmp_path / "objects")
    processor = FFmpegMediaProcessor(
        storage=storage,
        settings=Settings(
            s3_bucket="bucket",
            playback_base_url="https://media.example",
            _env_file=None,
        ),
    )
    video = Video(
        id="video-id",
        owner_id="owner",
        original_filename="source.mp4",
        content_type="video/mp4",
        container="mp4",
        codec="h264",
        declared_size_bytes=source.stat().st_size,
        declared_duration_seconds=3,
        bucket="bucket",
        object_key="videos/source.mp4",
        status="ready",
    )

    metadata = await processor.inspect(video)
    artifacts = await processor.generate_clips(
        video=video,
        job_id="job-id",
        points=[
            AnalyzedPoint(
                id="point-id",
                job_id="job-id",
                sequence_number=1,
                start_ms=500,
                end_ms=2000,
                winner_role="target",
                confidence=1.0,
            )
        ],
    )

    assert metadata["codec"] == "h264"
    assert metadata["width"] == 320
    assert metadata["height"] == 240
    assert metadata["duration_seconds"] == 3.0
    assert len(artifacts) == 1
    assert artifacts[0].playback_url.endswith("/point-id.mp4")
    output = tmp_path / "objects" / artifacts[0].object_key
    assert output.exists()
    assert output.stat().st_size > 0
