# TrackNetV4 baseline harness

**Date:** September 3, 2026  
**Phase:** Experiment

## Goal

Use an existing ball-tracking model before considering custom training, and create the evaluation
path needed to determine whether it works on Ace Pro footage.

## What I did

- Inspected the official TrackNetV4 source, prediction entrypoint, environment, results, and license.
- Pinned the current source revision and separated its TensorFlow runtime from the API.
- Implemented a compatibility runner, standardized JSONL artifact, provenance manifest, FFmpeg
  overlay, dataset validator, ball metrics, CLI, synthetic fixture, and automated tests.
- Installed a pinned TensorFlow/Metal environment on an Apple-silicon Mac and ran the complete
  TrackNetV4 architecture plus a three-frame end-to-end adapter smoke test with temporary random
  weights.
- Reviewed a candidate court-keypoint repository and recorded it as blocked because the repository
  does not state a license.

## Key findings

- TrackNetV4 is a plausible first ball-tracking baseline and its source is MIT-licensed.
- At the pinned revision, advertised model-download links are placeholders, so a reproducible tennis
  checkpoint is not yet available from the repository.
- The upstream prediction entrypoint references undefined custom-layer names and its three output
  rows share one frame-window index. A compatibility boundary is necessary before evaluation.
- The upstream loss helper also imports a nonexistent model module; the compatibility runner owns
  the equivalent loss definition and successfully executes TrackNetV4 on the Mac's Metal GPU.
- Ball coordinates alone do not supply contacts, bounces, stroke side, or point outcome.

## What changed

Before this activity, the next step was broadly described as using existing models and then building
an evaluation dataset.

After inspecting the actual upstream artifacts, the work is now a concrete, pinned TrackNetV4
experiment with explicit provenance, output, evaluation, and review contracts. A real checkpoint is
the remaining prerequisite for footage inference, while the evaluation workflow can already be
tested independently.

Because of this, the project should obtain and checksum a checkpoint, annotate a small pilot set,
and measure it before connecting model output to the user-visible analysis API.

## Open questions

- Can the TrackNetV4 authors provide the tennis checkpoint used for their reported results?
- What pixel/court-coordinate error still permits reliable short/deep bounce classification?
- Which licensed court-calibration baseline best fits fixed phone video behind the baseline?

## Next steps

- Obtain the checkpoint and update `ml/models.lock.json` with its provenance and checksum.
- Run one representative clip and inspect the overlay.
- Write the ball annotation guide and label the first pilot sequences.
- Generate the first held-out evaluation report and decide whether to adopt, fine-tune, or replace
  the model.
