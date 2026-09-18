from ace_pro_eval.metrics import evaluate_ball_tracking
from ace_pro_eval.schema import BallObservation


def observation(frame: int, visible: bool, x: float | None = None, y: float | None = None):
    return BallObservation(frame, frame * 40, visible, x, y)


def test_ball_metrics_treat_localization_miss_as_fp_and_fn():
    truth = [
        observation(0, True, 10, 10),
        observation(1, True, 20, 20),
        observation(2, False),
        observation(3, True, 40, 40),
        observation(4, False),
    ]
    predictions = [
        observation(0, True, 12, 11),
        observation(1, True, 50, 50),
        observation(2, True, 15, 15),
        observation(3, False),
    ]

    result = evaluate_ball_tracking(truth, predictions, tolerance_px=5)
    report = result.to_dict(tolerance_px=5)

    assert result.true_positives == 1
    assert result.true_negatives == 0
    assert result.false_positives == 2
    assert result.false_negatives == 2
    assert result.localization_misses == 1
    assert result.missing_prediction_frames == 1
    assert report["frame_coverage"] == 0.8
    assert report["visible_pair_coordinate_error_px"]["count"] == 2


def test_unexpected_visible_prediction_is_a_false_positive():
    result = evaluate_ball_tracking(
        [observation(0, False)],
        [observation(0, False), observation(1, True, 1, 1)],
        tolerance_px=5,
    )

    assert result.true_negatives == 1
    assert result.false_positives == 1
    assert result.unexpected_prediction_frames == 1
