# 03: Footage Quality Gate

## Purpose

Determine which analysis capabilities a recording can support before expensive inference or user-visible conclusions are produced.

## Initial supported capture envelope

- Singles match
- One continuous, fixed camera
- Camera approximately behind one baseline
- Full singles court visible for most points
- Both players visible during rallies
- No broadcast cuts, zooming, or replay inserts
- At least 1080p preferred

Inputs outside this envelope may be stored and played, but automated match insights are not promised.

## Checks

Sample frames throughout the match and calculate:

- Court keypoint coverage and calibration residual
- Camera motion and scene-cut frequency
- Near/far player visibility
- Ball detectability on representative rally segments
- Effective resolution of the court region
- Blur, exposure, and occlusion rates
- Fraction of time the full court remains visible

## Capability result

The gate returns a decision per capability rather than one global boolean:

```json
{
  "capture_profile": "fixed_baseline_singles",
  "overall": "limited",
  "capabilities": {
    "court_calibration": {"enabled": true, "confidence": 0.96},
    "player_tracking": {"enabled": true, "confidence": 0.93},
    "return_depth": {"enabled": false, "reason": "far_baseline_cropped"},
    "point_segmentation": {"enabled": true, "confidence": 0.82}
  }
}
```

## Decision policy

- `supported`: capability may proceed automatically.
- `limited`: capability may proceed but results require review.
- `unsupported`: skip the dependent models and do not publish the insight.

Thresholds are versioned configuration and must be calibrated against labeled matches. They must not be silently relaxed to increase apparent completion rates.

## User-facing failures

Translate technical results into actionable guidance:

- “The far baseline is outside the frame, so return depth cannot be measured reliably.”
- “The camera moved during the match. Use a fixed mount for automatic analysis.”
- “The ball is too small in this recording for reliable bounce locations.”

Do not expose raw confidence values without a meaningful explanation.

## Artifacts and metrics

Store the quality report, representative thumbnails, keypoint overlays, gate version, and reason codes. Track pass rate by device profile, resolution, and capture configuration to improve the recording guide.

## Acceptance criteria

- Known good fixtures enable the initial return-depth capability.
- Cropped, moving, blurred, and broadcast-edited fixtures are rejected with the correct reason.
- A rejected capability cannot produce a publishable dependent insight.
- Gate decisions are reproducible for the same component version.

