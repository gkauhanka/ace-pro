# 14: On-Device Video Analysis

## Purpose

Define a phased path from Ace Pro's current metadata-only iOS experience to real, structured tennis
observations produced on the phone. The first automated phase uses Apple's supported Vision
trajectory detector. Later phases add body pose, a tennis-specific Core ML detector, action
classification, and deterministic event fusion.

This design keeps source video on the device. The phone sends versioned observations, events,
quality measurements, and confidence values to the insights service. It does not send video frames,
audio, filenames, notes, account credentials, or generated claims about player performance.

## Status and relationship to the server pipeline

This is an incremental client-side complement to the hybrid pipeline in
[ADR-0001](../adr/0001-hybrid-evidence-backed-video-analysis.md), not a replacement for its evidence,
versioning, evaluation, or correction requirements.

The phone is responsible for decoding local media and producing measurements. The insights service
is responsible for validating those measurements, calculating versioned patterns, and returning
reports. Numeric insights must come from structured evidence and deterministic rules, not from a
language model.

TrackNetV4 remains a server/evaluation comparison lane. It is not the initial phone model because
the repository does not yet have an approved tennis checkpoint, its current adapter targets a
TensorFlow worker environment, and it has not been converted or benchmarked on supported iPhones.

## Decision summary

Ace Pro will not treat video analysis as one opaque model. It will introduce independently
measurable components in this order:

| Phase | Device capability | Model or framework | Primary output |
| --- | --- | --- | --- |
| 0 | Capture validation and court setup | AVFoundation plus manual calibration | media quality and court homography |
| 1 | Ball-motion candidates | Apple Vision `VNDetectTrajectoriesRequest` | timestamped image-space trajectories |
| 2 | Player geometry | Apple Vision `VNDetectHumanBodyPoseRequest` | timestamped joints and confidence |
| 3 | Tennis-specific object detection | Custom Core ML object detector | ball/player boxes and class confidence |
| 4 | Stroke and action candidates | Create ML `MLActionClassifier` or equivalent Core ML temporal model | serve/forehand/backhand/other windows |
| 5 | Tennis-event fusion | Versioned deterministic Swift rules | contacts, bounces, shots, points, and evidence ranges |
| 6 | Insight calculation | Versioned server rules | confidence-gated, evidence-backed coaching patterns |

Each phase must remain useful and inspectable without requiring all later phases to be complete.

## Shared on-device execution model

The app reads the imported local asset with AVFoundation and processes decoded pixel buffers on a
background task while the app is active. Analysis progress and cancellation are persistent user
states. A cancelled or interrupted job retains the local video and any complete, versioned
artifacts; it never publishes a partial artifact as a complete report.

Frame processing rates are component-specific:

- Preserve native timestamps rather than deriving time from a frame counter.
- Run ball trajectory processing at the highest evaluated rate the supported device can sustain,
  targeting 30 fps initially and evaluating 60 fps sources separately.
- Run pose estimation at a lower sampled rate, then increase sampling around candidate contacts.
- Use regions of interest after court calibration to reduce noise and device load.
- Record skipped frames, thermal interruptions, elapsed time, and model latency as quality data.

Core ML models should start with `MLModelConfiguration.computeUnits = .all` so the system can choose
the CPU, GPU, or Neural Engine. The release process must still benchmark each supported device class;
the selected compute units do not guarantee acceptable full-match latency or battery use.

## Phase 0: Capture quality and manual court calibration

### Goal

Establish whether the footage can support analysis before producing tennis claims.

### Implementation

Inspect the local asset and record:

- Duration, dimensions, nominal frame rate, orientation, and HDR state
- Decode failures and timestamp discontinuities
- Camera-motion score
- Exposure, blur, and usable-court coverage estimates
- Whether the recording is a fixed-camera singles match

Ask the user to identify the four court corners or another validated set of court intersections on a
representative frame. Fit and persist the image-to-court homography with its reprojection residual.
Manual calibration is preferred over an unvalidated court model in the first release because it is
inspectable and avoids silently assigning the wrong court geometry.

### Exit gate

- Calibration can be replayed as an overlay on the source video.
- Invalid or moving-camera footage produces an unsupported result, not inferred statistics.
- The same saved calibration maps identical image points to materially identical court coordinates.

## Phase 1: Apple Vision trajectory detection

### Goal

Produce real on-device candidates for the tennis ball's motion without adding a downloadable model.

### Model

Use Apple's `VNDetectTrajectoriesRequest`. Vision describes trajectory detection as suitable for
small moving objects in sports footage and notes that tennis-ball work may require 1080p input. It
also requires a stable scene, which aligns with Ace Pro's fixed-camera capture boundary.

Configure and version:

- Analysis frame spacing
- Court-derived region of interest
- Minimum and maximum object dimensions
- Direction and duration filters
- Confidence and trajectory-length thresholds
- Camera-motion rejection threshold

Do not call every Vision trajectory a tennis ball. This phase produces `ball_candidate` tracks.
Filter candidates using court bounds, plausible speed and acceleration, continuity, bounce-shaped
direction changes, color only when reliable, and proximity to later player-contact evidence.

### Artifact

```json
{
  "producer": "apple-vision-trajectory",
  "producer_version": "1",
  "timestamp_ms": 13110,
  "track_id": "trajectory-27",
  "image_xy": [1062.4, 611.7],
  "image_velocity_xy": [418.2, -193.6],
  "candidate_type": "ball_candidate",
  "confidence": 0.79,
  "observed": true
}
```

Observed and interpolated positions must be distinguishable. Gaps beyond a versioned limit remain
missing.

### Known limitations

- The detector follows motion; it does not semantically identify a tennis ball.
- Shadows, players, rackets, flags, and background motion can create false trajectories.
- Motion blur, occlusion, compression, and a very small far-court ball reduce coverage.
- Camera movement invalidates assumptions and must disable the capability.

### Exit gate

Compare on complete held-out matches, not selected successful clips. Report ball-candidate precision,
recall, coordinate error, frame coverage, false tracks per minute, device runtime, peak memory,
thermal state, and battery use. Phase 1 may support review-point suggestions before it supports
bounce-zone statistics.

## Phase 2: Apple Vision body pose

### Goal

Add real player geometry that helps assign near/far roles and localize potential contacts.

### Model

Use `VNDetectHumanBodyPoseRequest`, which produces recognized body joints and confidence values. Run
it on court regions and retain missing or low-confidence joints as missing values rather than zeros.
The near player can be selected from calibrated court position and temporal continuity; identity is
never inferred from appearance.

Initially retain:

- Wrists, elbows, shoulders, hips, knees, ankles, neck, and root
- Pose bounding box and per-joint confidence
- Near/far court role and role confidence
- Sampling timestamp and source orientation

Pose is supporting evidence, not a technique diagnosis. Consumer baseline footage may not contain
enough pixels for reliable far-player pose, and one camera view cannot establish every 3D movement.

### Exit gate

- Near/far role accuracy meets the gate in
  [evaluation and rollout](./12-evaluation-and-rollout.md).
- Contact-window recall improves over trajectory-only heuristics on held-out matches.
- Low-confidence and occluded joints do not create confident stroke labels.

## Phase 3: Tennis-specific Core ML detector

### Goal

Semantically distinguish the ball and players, improve reacquisition after occlusion, and reject
non-ball trajectories.

### Model strategy

Train a compact object detector with Ace Pro footage and export it as a Core ML model. Apple's
Create ML `MLObjectDetector` is the simplest supported training path. A separately trained compact
detector may also be converted to Core ML if its license, operators, preprocessing, and conversion
are documented and reproducible.

Initial labels:

- `ball`
- `near_player`
- `far_player`

The training data must contain empty frames, hard negatives, blurred balls, occlusion, different
court surfaces, lighting, devices, orientations, and ball sizes. Split by match and player.
Ordinary user corrections do not enter training automatically.

Run the detector periodically and around low-confidence intervals. Use its ball box to seed or
reacquire temporal tracking between detector frames. Preserve detector observations separately from
tracker interpolation so evaluation can attribute errors correctly.

### Exit gate

- The detector-plus-tracker pipeline materially improves downstream bounce and contact accuracy over
  Phase 1 on the same held-out set.
- Model size, load time, memory, thermals, and full-match duration meet declared device budgets.
- Every shipped model records training dataset version, weights checksum, preprocessing version,
  label schema, license, and evaluation report.

If it does not improve downstream events, retain Phase 1 and continue using the custom model only in
shadow evaluation.

## Phase 4: Stroke and action classification

### Goal

Classify candidate action windows without attempting unconstrained technique diagnosis.

### Model strategy

Train a Create ML `MLActionClassifier` or an equivalently versioned Core ML temporal classifier on
pose sequences. Initial classes should stay narrow:

- `serve`
- `forehand`
- `backhand`
- `other`

Use candidate contact windows from the ball and pose pipeline rather than scanning every frame at
maximum rate. Training and inference frame rates must match. Include a substantial negative class
and variation in handedness, camera position, clothing, skill level, and occlusion. Apple's guidance
suggests beginning with at least 50 representative videos per action; Ace Pro must determine the
actual required dataset size through held-out evaluation.

### Exit gate

- Macro precision, recall, and calibration are reported by match, player, handedness, and capture
  slice.
- Unknown or low-confidence windows remain `unknown`.
- Stroke classification improves the first target insight without reducing its precision gate.

## Phase 5: Deterministic on-device event fusion

### Goal

Convert independent observations into inspectable tennis-event candidates before upload.

Versioned Swift logic combines:

- Court calibration
- Ball observations and candidate tracks
- Player roles and pose windows
- Candidate contacts and bounces
- Stroke probabilities
- Footage and component quality

The initial event vocabulary is:

- `rally_start_candidate`
- `serve_contact_candidate`
- `return_contact_candidate`
- `ball_contact_candidate`
- `bounce_candidate`
- `forehand_candidate`
- `backhand_candidate`
- `rally_end_candidate`

Each event contains source observation IDs, timestamp bounds, confidence, producer version, and an
evidence range that the user can replay locally. A later correction is stored as an overlay and does
not erase the machine event.

## Phase 6: Insights service integration

The iOS app uploads a compact analysis envelope after the user has opted to analyze the session:

```json
{
  "schema_version": 1,
  "analysis_id": "8a9a96f8-7af3-4fea-bfc4-07828f03547a",
  "duration_ms": 542000,
  "capture": {
    "width": 1920,
    "height": 1080,
    "nominal_fps": 60
  },
  "producers": {
    "trajectory": "apple-vision-trajectory/1",
    "pose": "apple-vision-body-pose/1",
    "fusion": "ace-ios-event-fusion/1"
  },
  "quality": {
    "camera_stable": true,
    "calibration_valid": true,
    "ball_frame_coverage": 0.81
  },
  "events": [
    {
      "event_id": "event-123",
      "type": "bounce_candidate",
      "timestamp_ms": 13110,
      "court_xy": [0.62, 0.34],
      "confidence": 0.79,
      "evidence_start_ms": 12610,
      "evidence_end_ms": 13610,
      "source_observation_ids": ["trajectory-27:94", "trajectory-27:95"]
    }
  ]
}
```

The production schema should use bounded arrays or a compressed artifact upload rather than an
unbounded JSON request. The server validates schema, sizes, timestamps, finite numeric values,
coordinate ranges, unique IDs, producer versions, and capability prerequisites before calculating
anything.

The service returns derived patterns plus the event IDs that support them. The iOS app resolves those
IDs to local playback ranges; raw video is not required by the service.

## Privacy and integrity requirements

- Analysis is opt-in per session and cancelable.
- The request preview states exactly which structured fields leave the phone.
- No raw frame, thumbnail, audio, filename, note, email, or credential is included.
- Local dense observations can be deleted independently after a report is created, subject to the
  product's correction and replay requirements.
- The service treats device analysis as untrusted input and performs strict validation.
- Reports identify their model and rule versions and never claim a capability whose quality gate
  failed.
- The product may call results video-derived only after the corresponding on-device component has
  passed held-out evaluation.

## Rollout plan

1. **Developer overlays:** render trajectory, pose, calibration, and event overlays locally.
2. **Internal shadow mode:** upload artifacts but keep current reports hidden from users.
3. **Review-point beta:** show local candidate timestamps without performance statistics.
4. **Review-required insights:** calculate the first server insight after manual event confirmation.
5. **Confidence-gated insights:** automatically publish only matches meeting all component gates.
6. **Broader release:** expand devices, capture conditions, and insights only from measured results.

At every stage, unsupported footage produces a clear quality result and retains the original local
video. Coverage is secondary to precision.

## Initial implementation slice

The first code slice should contain:

1. An `OnDeviceAnalysisJob` persisted alongside `LocalSession`.
2. An AVFoundation frame reader that preserves presentation timestamps and orientation.
3. Manual four-corner court calibration with a replayable overlay.
4. A versioned `VNDetectTrajectoriesRequest` runner.
5. A local JSONL trajectory artifact and debug overlay.
6. Component metrics for one short annotated clip.
7. A new development-only insights endpoint that accepts a bounded analysis envelope.
8. No replacement of the current user-facing report until the evaluation gate passes.

## References

- [Apple: Identifying trajectories in video](https://developer.apple.com/documentation/vision/identifying-trajectories-in-video)
- [Apple: Detecting human body poses in images](https://developer.apple.com/documentation/vision/detecting-human-body-poses-in-images)
- [Apple: MLObjectDetector](https://developer.apple.com/documentation/createml/mlobjectdetector)
- [Apple: Creating an action classifier model](https://developer.apple.com/documentation/createml/creating-an-action-classifier-model)
- [Apple: MLComputeUnits](https://developer.apple.com/documentation/coreml/mlcomputeunits)
- [Ace Pro vision inference](./04-vision-inference.md)
- [Ace Pro evaluation and rollout](./12-evaluation-and-rollout.md)
- [Ace Pro TrackNetV4 baseline](./13-tracknetv4-baseline-evaluation.md)
