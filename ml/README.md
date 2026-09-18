# Ace Pro model evaluation

This directory is the reproducible boundary between research models and the Ace Pro API. The
first baseline is TrackNetV4 ball tracking. It runs out of process in its own TensorFlow
environment, then converts its output to an Ace Pro artifact that can be inspected and evaluated
without TensorFlow.

The API does not import model code. A later worker can call this CLI and store its immutable
artifacts in object storage.

## What works now

- Pin and verify the TrackNetV4 source revision.
- Run a compatibility inference script using an externally supplied `.keras` checkpoint.
- Normalize TrackNet CSV output to one JSONL observation per real video frame.
- Record model revision, preprocessing settings, source checksums, and artifact checksum.
- Render a review overlay with FFmpeg.
- Validate evaluation manifests, including match/player split leakage.
- Calculate detection precision, recall, F1, frame coverage, and coordinate error.
- Produce per-sequence and micro-aggregated dataset reports.

The pinned upstream TrackNetV4 revision does **not** contain working checkpoint links. A checkpoint
must be obtained from the authors or trained using their repository, then its SHA-256 should be
recorded in `models.lock.json` before results are compared. Do not substitute an untracked file and
call the outcome reproducible.

The candidate court-keypoint repository is listed but disabled because it does not include a
license. Ace Pro must get permission or choose a licensed alternative before incorporating or
deploying that code.

## Setup

Install the lightweight evaluation CLI:

```bash
python3.11 -m venv ml/.venv
source ml/.venv/bin/activate
python -m pip install -e 'ml[dev]'
```

TrackNetV4 stays in a separate environment because it pins TensorFlow, CUDA, and OpenCV. Clone the
pinned revision and create the upstream environment:

```bash
git clone https://github.com/TrackNetV4/TrackNetV4.git ml/vendor/TrackNetV4
git -C ml/vendor/TrackNetV4 checkout cb7eea7988474771ceac7e880bbffc35bfa87bca
conda env create -f ml/vendor/TrackNetV4/environment.yml
```

`vendor/` and model weights should not be committed to this repository.

On an Apple-silicon Mac, the upstream Conda file cannot be installed because it pins Linux CUDA
packages. Use the checked-in Metal-compatible runtime instead:

```bash
python3.11 -m venv ml/.venv-tracknet
ml/.venv-tracknet/bin/python -m pip install -r ml/requirements-tracknet-macos.txt
```

This environment uses Apple's TensorFlow Metal plugin because TrackNetV4's NCHW convolutions are not
implemented by TensorFlow's macOS CPU backend. It is appropriate for local smoke tests and short clips. Production/full-match
inference should use the pinned Linux GPU environment after the baseline passes evaluation.

## Run TrackNetV4

Use `ffprobe` to obtain the real video frame rate, then run:

```bash
ace-eval run-tracknet \
  --video /data/match.mp4 \
  --repository ml/vendor/TrackNetV4 \
  --weights /models/tracknet-v4-tennis.keras \
  --python ml/.venv-tracknet/bin/python \
  --output-dir runs/match-001
```

The runner reads FPS with `ffprobe`; `--fps` is available only as an explicit override.

The command refuses a different source revision unless `--allow-revision-mismatch` is supplied for
an intentional experiment. It creates raw output, a model-rendered video,
`ball_predictions.jsonl`, and `ball_predictions.manifest.json`.

If TrackNet was run separately, normalize its CSV with:

```bash
ace-eval normalize-tracknet \
  --csv ml/examples/tracknet_raw.csv \
  --fps 30 \
  --weights /models/tracknet-v4-tennis.keras \
  --output /tmp/ball_predictions.jsonl
```

## Evaluate one clip

```bash
ace-eval evaluate \
  --ground-truth ml/examples/ground-truth.jsonl \
  --predictions /tmp/ball_predictions.jsonl \
  --tolerance-px 10 \
  --output /tmp/ball-report.json
```

A visible prediction outside the tolerance counts as both a false positive and a false negative,
and is reported separately as a localization miss. Coordinate-error statistics include every
frame where both prediction and truth say the ball is visible, so poor localizations cannot
disappear from the error distribution.

Render an evidence overlay:

```bash
ace-eval render-overlay \
  --video /data/match.mp4 \
  --predictions /tmp/ball_predictions.jsonl \
  --output /tmp/ball-overlay.mp4
```

## Build and evaluate the dataset

Ground truth is created by the Ace Pro development/evaluation team or contracted reviewers—not by
ordinary app users. Users may later correct their own match results, but those corrections remain
separate until reviewed for dataset inclusion.

Follow [`ANNOTATION_GUIDE.md`](./ANNOTATION_GUIDE.md), copy `examples/dataset.json`, and create one
reviewed JSONL truth artifact per sequence. Keep whole
matches and players in exactly one split. Validate before inference:

```bash
ace-eval validate-dataset --dataset /data/ace-pro-ball-v0.1/dataset.json
```

Write each model artifact as `<sequence_id>.jsonl` in one predictions directory, then evaluate the
held-out split:

```bash
ace-eval evaluate-dataset \
  --dataset /data/ace-pro-ball-v0.1/dataset.json \
  --predictions-dir runs/tracknet-v4-v0.1 \
  --split test \
  --tolerance-px 10 \
  --output reports/tracknet-v4-v0.1-test.json
```

The 10-pixel tolerance is only an initial debugging value. The final threshold must be derived from
the downstream bounce-zone error budget and reported in the release evaluation.

## Tests

```bash
PYTHONPATH=ml/src python3.11 -m pytest ml/tests
```
