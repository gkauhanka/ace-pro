from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from .schema import BallObservation


def render_ball_overlay(
    video_path: Path,
    observations: list[BallObservation],
    output_path: Path,
    *,
    ffmpeg: str = "ffmpeg",
    ffprobe: str = "ffprobe",
) -> None:
    width, height = _video_dimensions(video_path, ffprobe=ffprobe)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ace-pro-overlay-") as temporary_directory:
        filter_path = Path(temporary_directory) / "ball.filter"
        filter_path.write_text(
            _drawbox_filter(observations, width=width, height=height), encoding="utf-8"
        )
        subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(video_path),
                "-filter_script:v",
                str(filter_path),
                "-an",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(output_path),
            ],
            check=True,
        )


def _video_dimensions(video_path: Path, *, ffprobe: str) -> tuple[int, int]:
    completed = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "json",
            str(video_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    streams = json.loads(completed.stdout).get("streams", [])
    if not streams:
        raise ValueError(f"video has no video stream: {video_path}")
    return int(streams[0]["width"]), int(streams[0]["height"])


def _drawbox_filter(
    observations: list[BallObservation], *, width: int, height: int
) -> str:
    visible = [item for item in observations if item.visible]
    filters: list[str] = []
    for index, item in enumerate(visible):
        assert item.x_px is not None and item.y_px is not None
        start_seconds = item.timestamp_ms / 1000
        next_timestamp = (
            visible[index + 1].timestamp_ms / 1000
            if index + 1 < len(visible)
            else start_seconds + 0.05
        )
        end_seconds = min(start_seconds + 0.12, max(start_seconds + 0.03, next_timestamp))
        x = min(max(0, item.x_px - 6), max(0, width - 12))
        y = min(max(0, item.y_px - 6), max(0, height - 12))
        filters.append(
            f"drawbox=x={x:.2f}:y={y:.2f}:w=12:h=12:color=red@0.9:t=fill:"
            f"enable='between(t,{start_seconds:.4f},{end_seconds:.4f})'"
        )
    return ",\n".join(filters) if filters else "null"
