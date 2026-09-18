# 12: Evaluation and Rollout

## Purpose

Establish ground truth, evaluate each component and the complete insight, and prevent unreliable model output from becoming a confident product claim.

## Evaluation dataset

Begin with at least 5–10 representative fixed-camera singles matches. Expand before production to cover:

- Near and far target players
- Left- and right-handed players
- Different devices, resolutions, and frame rates
- Indoor and outdoor lighting
- Multiple court surfaces and colors
- Clothing and skin-tone variation
- Occlusion, shadows, and ball-color variation
- Competitive and practice-style match pacing

Split by complete match and player, never by random frames, to avoid leakage from adjacent video and repeated identities.

The first automated component dataset targets ball tracking. Dataset construction, validation, and
report generation use the CLI in [`ml`](../../ml/README.md). Internal team members or contracted
reviewers create the reviewed ground truth. Ordinary app users are not required to annotate footage;
their corrections remain a separate product record unless later reviewed and explicitly admitted to
a versioned dataset.

## Annotation schema

Label:

- Court keypoints and calibration-valid intervals
- Player boxes, roles, and selected pose frames
- Ball coordinates and visibility state
- Point start/end and winner
- Serve and return contacts
- Forehand/backhand/unknown
- First post-return bounce and short/deep/unknown zone
- Inclusion eligibility for the initial insight

Annotations include annotator ID, guide version, review status, and disagreement resolution. Measure inter-annotator agreement before treating labels as ground truth.

## Metrics and initial gates

These are proposed gates to revise from observed data:

| Component | Metric | Proposed gate |
| --- | --- | --- |
| Court calibration | median/95th percentile reprojection error | defined after pilot annotation |
| Player role tracking | role accuracy per point | at least 0.98 |
| Ball tracking | detection F1 and coordinate error | defined by bounce-zone needs |
| Point boundaries | segment F1 | at least 0.95 |
| Return identification | precision and recall | precision at least 0.95 |
| Stroke side | macro accuracy/F1 | at least 0.90 |
| Short/deep zone | macro accuracy/F1 | at least 0.90 |
| Point winner | accuracy | at least 0.95 |
| Complete insight | agreement with manual calculation | at least 0.90 |

For ball experiments, a prediction is a true positive only when both labels are visible and their
Euclidean pixel distance is within the declared tolerance. A visible prediction outside tolerance is
one false positive and one false negative and is also reported as a localization miss. Reports must
include frame coverage and the coordinate-error distribution for every visible/visible pair. The
tolerance must be derived from the downstream court-coordinate and bounce-zone error budget before a
release gate is accepted; 10 pixels is only the initial debugging default.

Publication thresholds should favor precision over coverage. An unknown or review-required result is preferable to an incorrect confident claim.

## End-to-end tests

For each held-out match:

1. Run the complete pinned pipeline.
2. Compare eligible event sets with manual ground truth.
3. Recalculate the insight from both sets.
4. Compare counts, rates, effect direction, and publication decision.
5. Review every false supporting clip.
6. Apply representative corrections and verify deterministic recalculation.

Measure both event accuracy and decision accuracy. A pipeline can have acceptable average event accuracy while still ranking the wrong pattern.

## Rollout stages

### Stage 0: manual product validation

Populate reports from manual annotations and test whether players or coaches use the insight to make a practice decision.

### Stage 1: internal shadow mode

Run automation without showing results. Compare against ground truth and investigate failures.

### Stage 2: review-required beta

Show results only after a reviewer confirms all events affecting the top insight.

### Stage 3: confidence-gated beta

Automatically publish high-confidence matches; route remaining matches to review or return an unsupported explanation.

### Stage 4: broader release

Expand only after accuracy, correction burden, latency, cost, and product-usefulness targets are met.

## Release report

Each pipeline release records dataset version, annotation guide, component metrics, slice metrics, end-to-end insight agreement, confidence calibration, known limitations, cost, latency, and approval decision.

## Stop conditions

Pause expansion if:

- Complete-insight agreement falls below the gate.
- A demographic, device, or capture slice materially underperforms.
- More than the agreed fraction of matches require burdensome correction.
- Users do not understand or act on the validated manual insight.
- Processing cost or latency makes repeated use impractical.

## Acceptance criteria

- The dataset split prevents player and match leakage.
- Every release has a reproducible evaluation report.
- No unsupported capability is presented as successful.
- The first automated insight agrees with manual ground truth on held-out matches.
- Product rollout advances based on both technical quality and observed usefulness.
