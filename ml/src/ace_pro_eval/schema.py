from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"


class SchemaError(ValueError):
    """Raised when an artifact or dataset manifest is invalid."""


@dataclass(frozen=True)
class BallObservation:
    frame_index: int
    timestamp_ms: int
    visible: bool
    x_px: float | None
    y_px: float | None
    confidence: float | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any], *, line_number: int | None = None):
        location = f" on line {line_number}" if line_number is not None else ""
        try:
            frame_index = int(value["frame_index"])
            timestamp_ms = int(value["timestamp_ms"])
            visible = value["visible"]
        except (KeyError, TypeError, ValueError) as exc:
            raise SchemaError(f"invalid ball observation{location}: {exc}") from exc

        if not isinstance(visible, bool):
            raise SchemaError(f"visible must be a boolean{location}")
        if frame_index < 0 or timestamp_ms < 0:
            raise SchemaError(f"frame_index and timestamp_ms must be non-negative{location}")

        x_px = _optional_float(value.get("x_px"), "x_px", location)
        y_px = _optional_float(value.get("y_px"), "y_px", location)
        confidence = _optional_float(value.get("confidence"), "confidence", location)
        if visible and (x_px is None or y_px is None):
            raise SchemaError(f"visible observations require x_px and y_px{location}")
        if not visible and (x_px is not None or y_px is not None):
            raise SchemaError(f"invisible observations must have null coordinates{location}")
        if confidence is not None and not 0 <= confidence <= 1:
            raise SchemaError(f"confidence must be between 0 and 1{location}")

        return cls(frame_index, timestamp_ms, visible, x_px, y_px, confidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_index": self.frame_index,
            "timestamp_ms": self.timestamp_ms,
            "visible": self.visible,
            "x_px": self.x_px,
            "y_px": self.y_px,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class DatasetSequence:
    sequence_id: str
    match_id: str
    player_id: str
    split: str
    video_path: Path
    ground_truth_path: Path
    fps: float
    width_px: int
    height_px: int
    annotator_ids: tuple[str, ...]
    review_status: str


@dataclass(frozen=True)
class DatasetManifest:
    dataset_name: str
    dataset_version: str
    annotation_guide_version: str
    sequences: tuple[DatasetSequence, ...]


def load_observations(path: Path) -> list[BallObservation]:
    observations: list[BallObservation] = []
    seen_frames: set[int] = set()
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SchemaError(f"invalid JSON on line {line_number} of {path}: {exc}") from exc
            if not isinstance(raw, dict):
                raise SchemaError(f"line {line_number} of {path} must be a JSON object")
            observation = BallObservation.from_dict(raw, line_number=line_number)
            if observation.frame_index in seen_frames:
                raise SchemaError(f"duplicate frame_index {observation.frame_index} in {path}")
            seen_frames.add(observation.frame_index)
            observations.append(observation)
    if not observations:
        raise SchemaError(f"no observations found in {path}")
    ordered = sorted(observations, key=lambda item: item.frame_index)
    for previous, current in zip(ordered, ordered[1:], strict=False):
        if current.frame_index != previous.frame_index + 1:
            raise SchemaError(
                f"frame indices must be contiguous in {path}: "
                f"{previous.frame_index} is followed by {current.frame_index}"
            )
        if current.timestamp_ms < previous.timestamp_ms:
            raise SchemaError(f"timestamps must be monotonic in {path}")
    return ordered


def write_observations(path: Path, observations: list[BallObservation]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for observation in observations:
            handle.write(json.dumps(observation.to_dict(), separators=(",", ":"), sort_keys=True))
            handle.write("\n")


def load_dataset_manifest(path: Path) -> DatasetManifest:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SchemaError(f"cannot read dataset manifest {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise SchemaError(f"dataset manifest {path} must be a JSON object")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise SchemaError(
            f"unsupported schema_version {raw.get('schema_version')!r}; expected {SCHEMA_VERSION!r}"
        )
    base = path.parent
    sequences: list[DatasetSequence] = []
    raw_sequences = raw.get("sequences", [])
    if not isinstance(raw_sequences, list):
        raise SchemaError("dataset sequences must be a list")
    for index, item in enumerate(raw_sequences):
        try:
            annotator_ids = item["annotator_ids"]
            if not isinstance(annotator_ids, list):
                raise SchemaError(f"sequence {index} annotator_ids must be a list")
            split = str(item["split"])
            if split not in {"train", "validation", "test"}:
                raise SchemaError(f"sequence {index} has unsupported split {split!r}")
            sequences.append(
                DatasetSequence(
                    sequence_id=str(item["sequence_id"]),
                    match_id=str(item["match_id"]),
                    player_id=str(item["player_id"]),
                    split=split,
                    video_path=(base / item["video_path"]).resolve(),
                    ground_truth_path=(base / item["ground_truth_path"]).resolve(),
                    fps=float(item["fps"]),
                    width_px=int(item["width_px"]),
                    height_px=int(item["height_px"]),
                    annotator_ids=tuple(str(value) for value in annotator_ids),
                    review_status=str(item["review_status"]),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SchemaError(f"invalid sequence at index {index}: {exc}") from exc
    if not sequences:
        raise SchemaError("dataset manifest must contain at least one sequence")
    return DatasetManifest(
        dataset_name=str(raw["dataset_name"]),
        dataset_version=str(raw["dataset_version"]),
        annotation_guide_version=str(raw["annotation_guide_version"]),
        sequences=tuple(sequences),
    )


def validate_dataset(manifest: DatasetManifest, *, require_files: bool = True) -> list[str]:
    errors: list[str] = []
    sequence_ids: set[str] = set()
    match_splits: dict[str, str] = {}
    player_splits: dict[str, str] = {}
    for sequence in manifest.sequences:
        if sequence.sequence_id in sequence_ids:
            errors.append(f"duplicate sequence_id: {sequence.sequence_id}")
        sequence_ids.add(sequence.sequence_id)
        if sequence.fps <= 0 or sequence.width_px <= 0 or sequence.height_px <= 0:
            errors.append(f"{sequence.sequence_id}: fps and dimensions must be positive")
        if not sequence.annotator_ids:
            errors.append(f"{sequence.sequence_id}: annotator_ids must not be empty")
        if sequence.review_status not in {"draft", "reviewed", "adjudicated"}:
            errors.append(
                f"{sequence.sequence_id}: unsupported review_status {sequence.review_status!r}"
            )
        if sequence.split in {"validation", "test"} and sequence.review_status == "draft":
            errors.append(f"{sequence.sequence_id}: held-out ground truth must be reviewed")
        _record_split(errors, match_splits, sequence.match_id, sequence.split, "match")
        _record_split(errors, player_splits, sequence.player_id, sequence.split, "player")
        if require_files:
            if not sequence.video_path.is_file():
                errors.append(f"{sequence.sequence_id}: video not found: {sequence.video_path}")
            if not sequence.ground_truth_path.is_file():
                errors.append(
                    f"{sequence.sequence_id}: ground truth not found: {sequence.ground_truth_path}"
                )
            else:
                try:
                    load_observations(sequence.ground_truth_path)
                except SchemaError as exc:
                    errors.append(f"{sequence.sequence_id}: {exc}")
    return errors


def _record_split(
    errors: list[str], seen: dict[str, str], entity_id: str, split: str, entity: str
) -> None:
    previous = seen.setdefault(entity_id, split)
    if previous != split:
        errors.append(f"{entity} {entity_id!r} leaks across {previous!r} and {split!r} splits")


def _optional_float(value: Any, name: str, location: str) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise SchemaError(f"{name} must be numeric or null{location}") from exc
