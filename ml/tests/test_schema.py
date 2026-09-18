import json
from pathlib import Path

import pytest

from ace_pro_eval.schema import (
    BallObservation,
    SchemaError,
    load_dataset_manifest,
    load_observations,
    validate_dataset,
    write_observations,
)


def test_observation_round_trip(tmp_path: Path):
    path = tmp_path / "observations.jsonl"
    expected = [
        BallObservation(0, 0, True, 12.5, 14.0, 0.8),
        BallObservation(1, 33, False, None, None, 0.1),
    ]
    write_observations(path, expected)

    assert load_observations(path) == expected


def test_visible_observation_requires_coordinates():
    with pytest.raises(SchemaError, match="require x_px"):
        BallObservation.from_dict(
            {"frame_index": 0, "timestamp_ms": 0, "visible": True, "x_px": None, "y_px": 1}
        )


def test_observations_must_be_contiguous(tmp_path: Path):
    path = tmp_path / "observations.jsonl"
    write_observations(
        path,
        [
            BallObservation(3, 100, False, None, None),
            BallObservation(5, 167, False, None, None),
        ],
    )

    with pytest.raises(SchemaError, match="must be contiguous"):
        load_observations(path)


def test_dataset_validation_rejects_player_leakage(tmp_path: Path):
    manifest_path = tmp_path / "dataset.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "dataset_name": "test",
                "dataset_version": "1",
                "annotation_guide_version": "1",
                "sequences": [
                    _sequence("a", "match-a", "player-a", "train"),
                    _sequence("b", "match-b", "player-a", "test"),
                ],
            }
        ),
        encoding="utf-8",
    )

    errors = validate_dataset(load_dataset_manifest(manifest_path), require_files=False)

    assert errors == ["player 'player-a' leaks across 'train' and 'test' splits"]


def _sequence(sequence_id: str, match_id: str, player_id: str, split: str):
    return {
        "sequence_id": sequence_id,
        "match_id": match_id,
        "player_id": player_id,
        "split": split,
        "video_path": f"{sequence_id}.mp4",
        "ground_truth_path": f"{sequence_id}.jsonl",
        "fps": 30,
        "width_px": 320,
        "height_px": 180,
        "annotator_ids": ["annotator-1"],
        "review_status": "reviewed",
    }
