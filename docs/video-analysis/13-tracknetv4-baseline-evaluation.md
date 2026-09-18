# 13: TrackNetV4 Baseline Evaluation

## Purpose

Test an existing tennis-ball tracker on Ace Pro footage before investing in a custom model. This
experiment measures whether TrackNetV4 provides enough ball observations for later contact and bounce
detection; it does not claim to detect tennis events or produce product insights by itself.

## Pinned inputs

- Source: [official TrackNetV4 repository](https://github.com/TrackNetV4/TrackNetV4)
- Revision: `cb7eea7988474771ceac7e880bbffc35bfa87bca`
- License: MIT
- Production runtime: upstream Python 3.9/TensorFlow 2.17 Linux environment
- Verified local runtime: Python 3.11, TensorFlow 2.17, and TensorFlow Metal 1.1 on Apple silicon
- Input preprocessing: RGB, 512×288, three non-overlapping frames per inference call
- Model checkpoint: `.keras`, source and SHA-256 required before evaluation

The upstream repository advertises pretrained models, but the download entries in its pinned results
document point to placeholders. The first prerequisite is therefore to obtain a checkpoint from the
authors or reproduce training. The repository revision and checkpoint checksum form one experiment
version; changing either creates a new result set.

The local Metal runtime was verified with the complete TrackNetV4 architecture and a three-frame
end-to-end adapter smoke test using random weights. That proves runtime compatibility only; random
weights are never a model-quality result and are not retained as an approved checkpoint.

## Adapter contract

The `ace-eval run-tracknet` command invokes a compatibility runner in the isolated TrackNet
environment. The compatibility runner is required because the upstream prediction entrypoint at the
pinned revision references undefined custom-layer names and repeats a window index for all three CSV
rows. Ace Pro keeps the model and its intended preprocessing while producing one observation per real
frame:

```json
{
  "frame_index": 152,
  "timestamp_ms": 5067,
  "visible": true,
  "x_px": 1062.4,
  "y_px": 611.7,
  "confidence": 0.84
}
```

The artifact manifest records model revision, preprocessing constants, source FPS, source checksum,
prediction checksum, creation time, and record count. The model-rendered MP4 and an independent
FFmpeg overlay make output visually reviewable.

## Dataset contract

Each sequence declares a stable sequence, match, and player ID; split; video path; ground-truth path;
FPS; and dimensions. A validation command rejects duplicate sequence IDs, invalid truth artifacts,
missing media, and any match or player assigned to multiple splits.

Ground truth uses the same per-frame JSONL shape. Reviewers label ball center and visibility, with
occluded or indeterminate frames marked invisible. The annotation guide must define how motion blur,
partial balls, replay graphics, and uncertain centers are handled. Dataset version and annotation
guide version are immutable report inputs.

## Metrics

Report for every sequence and for the complete held-out split:

- frame coverage;
- visible-ball precision, recall, and F1;
- localization misses outside the declared pixel tolerance;
- mean, median, and 95th-percentile coordinate error for visible/visible pairs; and
- raw TP, TN, FP, and FN counts.

A mislocalized visible prediction counts as one FP and one FN. This follows object-detection matching
semantics and prevents a confidently wrong location from receiving detection credit. Slice reports
for device, resolution, lighting, surface, near/far court region, and blur severity should be added
once the pilot dataset contains enough examples.

## Experiment procedure

1. Obtain a tennis checkpoint and record its provenance and SHA-256 in `ml/models.lock.json`.
2. Select 5–10 fixed-camera singles matches representative of the intended capture workflow.
3. Assign whole matches and players to train, validation, or test without leakage.
4. Annotate representative rally windows, double-review a sample, and resolve disagreements.
5. Run the pinned adapter for every sequence and inspect overlays for systematic failures.
6. Freeze the pixel tolerance based on downstream bounce-zone sensitivity, not model performance.
7. Generate and commit a metadata-only evaluation report; keep private video and dense labels outside
   Git unless their rights and privacy policy permit storage.
8. Decide: adopt in shadow mode, test another baseline, fine-tune, or stop the capability.

## Decision gate

There is deliberately no numeric release threshold before pilot annotation. The experiment passes to
shadow-mode integration only if the measured error supports return-contact and first-bounce candidate
generation with an acceptable review burden. The product must continue using manual labels until
that downstream validation exists.

## Known limitations

- Published TrackNetV4 benchmarks are not Ace Pro capture-condition benchmarks.
- The upstream runtime is Linux/CUDA-oriented and is not suitable for the FastAPI process or iOS.
- The model emits ball locations, not bounce, contact, stroke side, or point outcome.
- Fixed thresholds may be sensitive to compression, glare, court color, distance, and motion blur.
- Court coordinates require a separately licensed and validated court-calibration component.
