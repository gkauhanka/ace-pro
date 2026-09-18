from ace_pro_eval.overlay import _drawbox_filter
from ace_pro_eval.schema import BallObservation


def test_drawbox_overlay_contains_visible_points_only():
    filters = _drawbox_filter(
        [
            BallObservation(0, 0, True, 20, 30, 0.9),
            BallObservation(1, 40, False, None, None, 0.1),
        ],
        width=320,
        height=180,
    )

    assert "x=14.00:y=24.00" in filters
    assert filters.count("drawbox=") == 1
    assert "between(t,0.0000,0.0500)" in filters
