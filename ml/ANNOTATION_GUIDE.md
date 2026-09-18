# Ball annotation guide v0.1.0

## Scope

Label the tennis ball center and visibility on selected frames for TrackNetV4 evaluation. This guide
is for trained Ace Pro reviewers or contracted annotators. App users are not asked to complete this
work.

## Unit of annotation

One JSONL row represents one decoded video frame. `frame_index` is zero-based and sequential.
`timestamp_ms` is derived as `round(frame_index × 1000 / authoritative_fps)`. Do not choose a
timestamp by scrubbing approximately.

## Visible ball

Set `visible` to `true` and label the visual center of the ball when a reviewer can distinguish the
ball from its surroundings. Use floating-point source-video pixel coordinates, with `(0, 0)` at the
top-left corner. For a motion-blurred streak, label the center of the bright ball body, not the end of
the blur trail.

```json
{"frame_index":152,"timestamp_ms":5067,"visible":true,"x_px":1062.4,"y_px":611.7,"confidence":1.0}
```

Ground-truth `confidence` is `1.0` after review. Draft annotations may use a lower value to flag
uncertainty, but they cannot enter a held-out evaluation split until resolved.

## Invisible or indeterminate ball

Set `visible` to `false` and both coordinates to `null` when the ball is fully occluded, outside the
frame, hidden by compression or glare, covered by graphics, or cannot be distinguished confidently.
Do not guess a coordinate from trajectory continuity.

```json
{"frame_index":153,"timestamp_ms":5100,"visible":false,"x_px":null,"y_px":null,"confidence":1.0}
```

## Included footage

- Annotate original-speed match footage only.
- Exclude broadcast replays, cuts, score graphics covering the court, and non-play camera views from
  the first fixed-camera dataset.
- Include both visible and invisible frames inside each selected rally window. Omitting difficult
  frames would inflate model results.
- Sample complete temporal windows, not only frames where the ball is easy to see.

## Review

Every validation and test sequence must be `reviewed` or `adjudicated` in `dataset.json`. Double-label
at least 10% of pilot frames. Resolve disagreements about visibility first, then coordinate location.
Record all participating annotator IDs in the sequence manifest; use stable pseudonymous IDs rather
than names or email addresses.

For agreement reporting:

- visibility agreement: percent agreement and Cohen's kappa;
- coordinate agreement: median and 95th-percentile Euclidean distance on frames both annotators mark
  visible; and
- adjudication rate: fraction of frames changed during review.

## Dataset hygiene

Keep all clips from the same match and all footage of the same player in one split. Run
`ace-eval validate-dataset` before every evaluation. Increment the dataset version for label changes
and the guide version for definition changes; never silently replace a published evaluation set.
