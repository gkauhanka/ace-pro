import csv
import json
from pathlib import Path

from ace_pro_eval.schema import load_observations
from ace_pro_eval.tracknet import normalize_tracknet_csv


def test_normalizer_repairs_repeated_upstream_window_indices(tmp_path: Path):
    source = tmp_path / "tracknet.csv"
    with source.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Frame", "Visibility", "X", "Y"])
        writer.writerows(
            [
                [0, 1, 10, 11],
                [0, 0, 0, 0],
                [0, 1, 12, 13],
                [1, 1, 14, 15],
            ]
        )
    output = tmp_path / "predictions.jsonl"

    manifest_path = normalize_tracknet_csv(source, output, fps=25)
    predictions = load_observations(output)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert [item.frame_index for item in predictions] == [0, 1, 2, 3]
    assert [item.timestamp_ms for item in predictions] == [0, 40, 80, 120]
    assert predictions[1].x_px is None
    assert manifest["upstream_frame_column_repeated"] is True
    assert manifest["model"]["name"] == "TrackNetV4"


def test_normalizer_preserves_unique_frame_indices(tmp_path: Path):
    source = tmp_path / "tracknet.csv"
    source.write_text(
        "Frame,Visibility,X,Y,Confidence\n10,1,5,6,0.75\n11,0,0,0,0.1\n",
        encoding="utf-8",
    )
    output = tmp_path / "predictions.jsonl"

    normalize_tracknet_csv(source, output, fps=50)
    predictions = load_observations(output)

    assert [item.frame_index for item in predictions] == [10, 11]
    assert predictions[0].timestamp_ms == 200
    assert predictions[0].confidence == 0.75
