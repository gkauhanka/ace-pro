# 04: Vision Inference

## Purpose

Produce versioned spatial and temporal observations for the court, players, poses, and ball. This layer describes what appears in the video; it does not calculate tennis insights.

## Execution model

Inference runs offline against the normalized proxy in chunked windows with overlap. Chunk boundaries must not break tracks or hide events. A reconciliation pass merges overlapping predictions into match-level tracks.

## Court calibration

Detect court-line intersections and fit a homography from image pixels to canonical court coordinates. Persist:

- Keypoint coordinates and confidence
- Homography and inverse homography
- Reprojection residual
- Valid frame interval
- Camera-motion alarms
- Court-model version

Use normalized court coordinates in which the regulation court geometry is stable across camera resolutions. Calibration must be invalidated when camera motion exceeds the configured tolerance.

## Player tracking

For each frame or sampled timestamp, persist detections and stable track IDs:

```json
{
  "timestamp_ms": 754200,
  "track_id": "near-1",
  "bbox_xywh": [412, 530, 138, 291],
  "court_xy": [0.43, 0.87],
  "role": "near_player",
  "confidence": 0.97
}
```

Near/far roles derive from calibrated court position and temporal continuity. Identity is assigned from match metadata or explicit user confirmation, never inferred from appearance alone.

## Pose estimation

Estimate body landmarks around candidate contacts and serves. Retain raw landmark confidence. Pose features may support stroke classification, but low-confidence or occluded joints must be represented as missing rather than zero.

## Ball tracking

The tracker operates on temporal frame windows and emits a heatmap or coordinate with visibility confidence. Tennis balls can be tiny, blurred, or absent for several frames, so independent frame detection is insufficient; TrackNet is a relevant baseline specifically designed for high-speed small sports objects.

Persist:

```json
{
  "timestamp_ms": 755030,
  "image_xy": [1062.4, 611.7],
  "court_xy": [0.58, 0.31],
  "visible": true,
  "interpolated": false,
  "confidence": 0.84
}
```

Interpolation across short gaps is allowed only when the method, source observations, and reduced confidence are recorded. Long gaps remain missing.

### Initial baseline

The first implemented baseline is the official TensorFlow TrackNetV4 repository pinned to commit
`cb7eea7988474771ceac7e880bbffc35bfa87bca`. The model executes outside the API process through the
[`ml`](../../ml/README.md) adapter. The adapter preserves the upstream 512×288, three-frame input,
normalizes output to real sequential frame indices and integer timestamps, and records source and
artifact checksums.

The checkpoint is a separate immutable dependency. The pinned upstream results page contains
placeholder checkpoint links, so no checkpoint is considered approved until its source and SHA-256
are recorded in `ml/models.lock.json`. This is an integration baseline, not evidence that the model
works on Ace Pro capture conditions.

## Artifact format

Use a columnar representation such as Parquet for dense frame predictions and JSON manifests for metadata. PostgreSQL stores artifact references and extracted event-level results, not every raw frame observation.

## Model versioning

Every artifact records:

- Model name and immutable version
- Container image digest
- Preprocessing version
- Configuration hash
- Input artifact checksum
- Hardware and runtime metadata
- Calibration metrics

Changing weights, preprocessing, thresholds, or label definitions produces a new version.

## Failure behavior

A component can fail independently. Court-calibration failure disables court-coordinate capabilities. Ball failure disables bounce-based capabilities but need not prevent coarse point segmentation. Partial output must not be presented as complete.

## Acceptance criteria

- Court overlays align with annotated intersections within the evaluation tolerance.
- Near and far player tracks maintain stable roles across rallies.
- Ball artifacts distinguish observed, interpolated, and missing positions.
- Repeated runs with the same versions produce materially equivalent predictions.
- Dense artifacts remain inspectable with a frame-overlay debugging tool.

## Reference

- [TrackNet paper](https://arxiv.org/abs/1907.03698)
