from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Any

from .schema import BallObservation


@dataclass(frozen=True)
class BallEvaluation:
    ground_truth_frames: int
    prediction_frames: int
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    localization_misses: int
    missing_prediction_frames: int
    unexpected_prediction_frames: int
    visible_pair_errors_px: tuple[float, ...]

    def to_dict(self, *, tolerance_px: float) -> dict[str, Any]:
        precision = _divide(self.true_positives, self.true_positives + self.false_positives)
        recall = _divide(self.true_positives, self.true_positives + self.false_negatives)
        f1 = _divide(2 * precision * recall, precision + recall)
        return {
            "tolerance_px": tolerance_px,
            "frame_coverage": _divide(
                self.ground_truth_frames - self.missing_prediction_frames,
                self.ground_truth_frames,
            ),
            "counts": {
                "true_positives": self.true_positives,
                "true_negatives": self.true_negatives,
                "false_positives": self.false_positives,
                "false_negatives": self.false_negatives,
                "localization_misses": self.localization_misses,
                "missing_prediction_frames": self.missing_prediction_frames,
                "unexpected_prediction_frames": self.unexpected_prediction_frames,
            },
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "visible_pair_coordinate_error_px": _summarize(self.visible_pair_errors_px),
        }


def evaluate_ball_tracking(
    ground_truth: list[BallObservation],
    predictions: list[BallObservation],
    *,
    tolerance_px: float,
) -> BallEvaluation:
    if tolerance_px <= 0:
        raise ValueError("tolerance_px must be positive")
    truth_by_frame = {item.frame_index: item for item in ground_truth}
    prediction_by_frame = {item.frame_index: item for item in predictions}
    true_positives = true_negatives = false_positives = false_negatives = 0
    localization_misses = missing_prediction_frames = 0
    visible_pair_errors: list[float] = []

    for frame_index, truth in truth_by_frame.items():
        prediction = prediction_by_frame.get(frame_index)
        if prediction is None:
            missing_prediction_frames += 1
            if truth.visible:
                false_negatives += 1
            continue
        if not truth.visible and not prediction.visible:
            true_negatives += 1
        elif not truth.visible and prediction.visible:
            false_positives += 1
        elif truth.visible and not prediction.visible:
            false_negatives += 1
        else:
            assert truth.x_px is not None and truth.y_px is not None
            assert prediction.x_px is not None and prediction.y_px is not None
            error = math.hypot(prediction.x_px - truth.x_px, prediction.y_px - truth.y_px)
            visible_pair_errors.append(error)
            if error <= tolerance_px:
                true_positives += 1
            else:
                localization_misses += 1
                false_positives += 1
                false_negatives += 1

    unexpected_prediction_frames = len(prediction_by_frame.keys() - truth_by_frame.keys())
    false_positives += sum(
        prediction_by_frame[index].visible
        for index in prediction_by_frame.keys() - truth_by_frame.keys()
    )
    return BallEvaluation(
        ground_truth_frames=len(truth_by_frame),
        prediction_frames=len(prediction_by_frame),
        true_positives=true_positives,
        true_negatives=true_negatives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        localization_misses=localization_misses,
        missing_prediction_frames=missing_prediction_frames,
        unexpected_prediction_frames=unexpected_prediction_frames,
        visible_pair_errors_px=tuple(visible_pair_errors),
    )


def combine_evaluations(evaluations: list[BallEvaluation]) -> BallEvaluation:
    return BallEvaluation(
        ground_truth_frames=sum(item.ground_truth_frames for item in evaluations),
        prediction_frames=sum(item.prediction_frames for item in evaluations),
        true_positives=sum(item.true_positives for item in evaluations),
        true_negatives=sum(item.true_negatives for item in evaluations),
        false_positives=sum(item.false_positives for item in evaluations),
        false_negatives=sum(item.false_negatives for item in evaluations),
        localization_misses=sum(item.localization_misses for item in evaluations),
        missing_prediction_frames=sum(item.missing_prediction_frames for item in evaluations),
        unexpected_prediction_frames=sum(item.unexpected_prediction_frames for item in evaluations),
        visible_pair_errors_px=tuple(
            error for evaluation in evaluations for error in evaluation.visible_pair_errors_px
        ),
    )


def _summarize(values: tuple[float, ...]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "mean": None, "median": None, "p95": None}
    ordered = sorted(values)
    p95_index = max(0, math.ceil(0.95 * len(ordered)) - 1)
    return {
        "count": len(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "p95": ordered[p95_index],
    }


def _divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
