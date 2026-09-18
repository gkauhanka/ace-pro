from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from typing import Any

from .schema import SCHEMA_VERSION, BallObservation, write_observations

PINNED_TRACKNET_REVISION = "cb7eea7988474771ceac7e880bbffc35bfa87bca"


def normalize_tracknet_csv(
    csv_path: Path,
    output_path: Path,
    *,
    fps: float | None = None,
    source_video: Path | None = None,
    checkpoint_path: Path | None = None,
    model_version: str = PINNED_TRACKNET_REVISION,
) -> Path:
    if fps <= 0:
        raise ValueError("fps must be positive")
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"TrackNet CSV has no predictions: {csv_path}")

    names = {name.lower(): name for name in (rows[0].keys() if rows else [])}
    required = {"frame", "visibility", "x", "y"}
    if missing := required - names.keys():
        raise ValueError(f"TrackNet CSV is missing columns: {', '.join(sorted(missing))}")
    upstream_frames = [int(row[names["frame"]]) for row in rows]
    repeated_window_indices = len(set(upstream_frames)) != len(upstream_frames)

    observations: list[BallObservation] = []
    for row_number, row in enumerate(rows):
        frame_index = row_number if repeated_window_indices else int(row[names["frame"]])
        visible = str(row[names["visibility"]]).strip().lower() in {"1", "true", "yes"}
        confidence_name = names.get("confidence")
        confidence = (
            float(row[confidence_name]) if confidence_name and row[confidence_name] else None
        )
        observations.append(
            BallObservation(
                frame_index=frame_index,
                timestamp_ms=round(frame_index * 1000 / fps),
                visible=visible,
                x_px=float(row[names["x"]]) if visible else None,
                y_px=float(row[names["y"]]) if visible else None,
                confidence=confidence,
            )
        )
    write_observations(output_path, observations)

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "ball_predictions",
        "created_at": datetime.now(UTC).isoformat(),
        "model": {
            "name": "TrackNetV4",
            "revision": model_version,
            "checkpoint_sha256": _sha256(checkpoint_path) if checkpoint_path else None,
        },
        "preprocessing": {
            "input_width_px": 512,
            "input_height_px": 288,
            "window_frames": 3,
            "source_fps": fps,
        },
        "record_count": len(observations),
        "source_csv_sha256": _sha256(csv_path),
        "predictions_sha256": _sha256(output_path),
        "upstream_frame_column_repeated": repeated_window_indices,
    }
    if source_video is not None:
        manifest["source_video"] = str(source_video)
        manifest["source_video_sha256"] = _sha256(source_video)
    manifest_path = output_path.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def run_tracknet(
    *,
    video_path: Path,
    repository_path: Path,
    weights_path: Path,
    output_dir: Path,
    fps: float,
    python_executable: Path | None = None,
    allow_revision_mismatch: bool = False,
) -> tuple[Path, Path, Path]:
    _require_file(video_path, "video")
    _require_file(weights_path, "model weights")
    runner = Path(__file__).with_name("tracknet_runner.py")
    if not (repository_path / "src" / "models" / "TrackNetV4.py").is_file():
        raise ValueError(f"not a TrackNetV4 repository: {repository_path}")
    revision = _git_revision(repository_path)
    if revision != PINNED_TRACKNET_REVISION and not allow_revision_mismatch:
        raise ValueError(
            f"TrackNetV4 revision is {revision}, expected {PINNED_TRACKNET_REVISION}; "
            "use --allow-revision-mismatch only for an intentional experiment"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_csv = output_dir / "tracknet_raw.csv"
    upstream_overlay = output_dir / "tracknet_upstream_overlay.mp4"
    command = [
        str(python_executable or Path(sys.executable)),
        str(runner),
        "--repository",
        str(repository_path),
        "--video",
        str(video_path),
        "--weights",
        str(weights_path),
        "--csv-output",
        str(raw_csv),
        "--video-output",
        str(upstream_overlay),
    ]
    subprocess.run(command, check=True)
    resolved_fps = fps if fps is not None else _probe_video_fps(video_path)
    predictions = output_dir / "ball_predictions.jsonl"
    manifest = normalize_tracknet_csv(
        raw_csv,
        predictions,
        fps=resolved_fps,
        source_video=video_path,
        checkpoint_path=weights_path,
        model_version=revision,
    )
    return predictions, manifest, upstream_overlay


def _git_revision(repository_path: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repository_path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError(f"cannot determine TrackNetV4 revision at {repository_path}") from exc
    return completed.stdout.strip()


def _probe_video_fps(video_path: Path) -> float:
    try:
        completed = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=avg_frame_rate",
                "-of",
                "json",
                str(video_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        streams = json.loads(completed.stdout).get("streams", [])
        fps = float(Fraction(streams[0]["avg_frame_rate"]))
    except (OSError, subprocess.CalledProcessError, IndexError, KeyError, ValueError) as exc:
        raise ValueError(f"cannot determine FPS for {video_path}; pass --fps explicitly") from exc
    if fps <= 0:
        raise ValueError(f"video has invalid FPS {fps}; pass --fps explicitly")
    return fps


def _require_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise ValueError(f"{label} not found: {path}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
