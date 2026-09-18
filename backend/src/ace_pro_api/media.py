import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol
from urllib.parse import quote

from anyio import to_thread

from ace_pro_api.config import Settings
from ace_pro_api.persistence.models import AnalyzedPoint, Video
from ace_pro_api.storage.base import ObjectStorage


@dataclass(frozen=True)
class ClipArtifact:
    point_id: str
    object_key: str
    playback_url: str


class MediaProcessor(Protocol):
    async def inspect(self, video: Video) -> dict: ...

    async def generate_clips(
        self, *, video: Video, job_id: str, points: list[AnalyzedPoint]
    ) -> list[ClipArtifact]: ...


class FFmpegMediaProcessor:
    def __init__(self, *, storage: ObjectStorage, settings: Settings) -> None:
        self._storage = storage
        self._settings = settings

    async def inspect(self, video: Video) -> dict:
        with TemporaryDirectory(prefix="ace-pro-inspect-") as directory:
            source = str(Path(directory) / f"original.{video.container}")
            await self._storage.download_file(
                bucket=video.bucket, key=video.object_key, destination=source
            )
            return await to_thread.run_sync(self._probe, source)

    async def generate_clips(
        self, *, video: Video, job_id: str, points: list[AnalyzedPoint]
    ) -> list[ClipArtifact]:
        if not points:
            return []
        artifacts: list[ClipArtifact] = []
        with TemporaryDirectory(prefix="ace-pro-clips-") as directory:
            source = str(Path(directory) / f"original.{video.container}")
            await self._storage.download_file(
                bucket=video.bucket, key=video.object_key, destination=source
            )
            for point in points:
                output = str(Path(directory) / f"{point.id}.mp4")
                start_ms = max(0, point.start_ms - 3_000)
                end_ms = point.end_ms + 2_000
                await to_thread.run_sync(self._clip, source, output, start_ms, end_ms)
                object_key = f"videos/{video.id}/analysis/{job_id}/clips/{point.id}.mp4"
                await self._storage.upload_file(
                    bucket=video.bucket,
                    key=object_key,
                    source=output,
                    content_type="video/mp4",
                )
                artifacts.append(
                    ClipArtifact(
                        point_id=point.id,
                        object_key=object_key,
                        playback_url=self._playback_url(object_key),
                    )
                )
        return artifacts

    @staticmethod
    def _probe(source: str) -> dict:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration,format_name,size:stream=index,codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate:stream_tags=rotate",
                "-of",
                "json",
                source,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        payload = json.loads(result.stdout)
        video_stream = next(
            (
                stream
                for stream in payload.get("streams", [])
                if stream.get("codec_type") == "video"
            ),
            None,
        )
        if video_stream is None:
            raise ValueError("Media contains no video stream.")
        media_format = payload.get("format", {})
        return {
            "duration_seconds": round(float(media_format.get("duration", 0)), 3),
            "size_bytes": int(media_format.get("size", 0)),
            "format_name": media_format.get("format_name"),
            "codec": video_stream.get("codec_name"),
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
            "average_frame_rate": video_stream.get("avg_frame_rate"),
            "nominal_frame_rate": video_stream.get("r_frame_rate"),
            "rotation_degrees": int(video_stream.get("tags", {}).get("rotate", 0)),
            "inspection_version": "ffprobe-1",
        }

    @staticmethod
    def _clip(source: str, output: str, start_ms: int, end_ms: int) -> None:
        duration_ms = max(1, end_ms - start_ms)
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-ss",
                f"{start_ms / 1000:.3f}",
                "-i",
                source,
                "-t",
                f"{duration_ms / 1000:.3f}",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-c:a",
                "aac",
                "-movflags",
                "+faststart",
                output,
            ],
            check=True,
            capture_output=True,
            timeout=300,
        )

    def _playback_url(self, key: str) -> str:
        if self._settings.playback_base_url:
            return f"{self._settings.playback_base_url.rstrip('/')}/{quote(key, safe='/')}"
        origin = f"https://{self._settings.s3_bucket}.s3.{self._settings.aws_region}.amazonaws.com"
        return f"{origin}/{quote(key, safe='/')}"
