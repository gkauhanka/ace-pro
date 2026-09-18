# ADR-0001: Hybrid, evidence-backed video analysis

- **Status:** Proposed
- **Date:** September 3, 2026
- **Owners:** Ace Pro engineering
- **Related design:** [Video analysis specification set](../video-analysis/README.md)
- **Upstream dependency:** [Video storage design](../video-storage-design.md)

## Context

Ace Pro needs to convert an uploaded tennis match into prioritized findings such as:

> The player lost 64% of points when a backhand return landed short.

The result must be useful even when individual model predictions are imperfect. A player or coach must be able to inspect the points behind a conclusion, see uncertainty, correct errors, and have affected statistics recalculated.

Long-form tennis video presents several separate problems: inconsistent phone media, court geometry, small and intermittently invisible ball tracking, player and pose tracking, temporal event recognition, point outcomes, statistical aggregation, explanation, and clip delivery. Treating this as one opaque model call would make accuracy difficult to measure and conclusions difficult to audit.

The existing system already uploads originals directly to S3 through a FastAPI control plane and records video metadata in PostgreSQL. Analysis must extend that boundary without sending video bytes through the API.

## Decision

Ace Pro will use an asynchronous hybrid pipeline with four logical layers:

1. **Media and quality layer:** validate, inspect, normalize, and determine whether the footage supports requested analyses.
2. **Perception layer:** calibrate the court and produce versioned player, pose, ball, and temporal-event predictions.
3. **Reasoning layer:** fuse predictions into structured tennis events, then calculate candidate patterns with deterministic, versioned rules.
4. **Presentation layer:** create evidence clips and optionally use constrained language generation to explain already-calculated results.

The database, rather than generated prose, is the source of truth. Every published insight must identify its supporting events and clips, calculation version, model versions, sample size, and confidence.

Human corrections will be stored as overlays on immutable machine predictions. Corrections will trigger deterministic recalculation and must not erase the original prediction.

Analysis will initially be an offline job, not a real-time endpoint. Local development will use containerized workers. The intended production shape is S3, a durable queue, PostgreSQL, versioned containers, and scale-to-zero GPU batch compute.

The first existing-model experiment will use TrackNetV4 for ball tracking behind an out-of-process
adapter pinned by repository revision and checkpoint checksum. Its output is normalized into an Ace
Pro-owned artifact schema and measured on a match/player-isolated evaluation dataset before it can
replace any manual label. The adapter is implemented under [`ml`](../../ml/README.md). A candidate
court detector was reviewed but is not integrated because its upstream repository does not state a
license; model availability does not override provenance and deployment requirements.

## Decision boundaries

### In scope

- Fixed-camera, singles matches recorded approximately behind a baseline.
- Full-match asynchronous analysis.
- One initial automated pattern: backhand return depth and subsequent point outcome.
- Traceable evidence clips and user correction.
- Component-level and end-to-end evaluation against annotated footage.

### Out of scope for the first implementation

- Live line calling or real-time feedback.
- Technique diagnosis from a single consumer camera.
- Doubles, moving cameras, broadcast edits, and arbitrary camera angles.
- Generating facts or numeric results with a language model.
- Automatically training production models from unreviewed user corrections.
- Guaranteeing officiating-grade in/out decisions.

## Component flow

```text
completed upload
  -> idempotent analysis job
  -> media inspection and normalized proxy
  -> footage quality gate
  -> court/player/pose/ball inference
  -> temporal event fusion
  -> point and shot records
  -> deterministic pattern calculation
  -> evidence clip generation
  -> constrained narrative rendering
  -> user review and correction
  -> affected insight recalculation
```

## Alternatives considered

### Send the entire video to a general-purpose multimodal model

Rejected as the primary approach. It provides weak control over temporal sampling, geometry, numeric reproducibility, and evidence lineage. It may still assist with experiments or presentation after structured facts exist.

### Build one end-to-end custom tennis model

Deferred. An end-to-end model might eventually improve performance, but the project does not yet have the labeled data or evaluation suite required to make it dependable. Modular predictions expose where failures occur and allow individual components to improve independently.

### Fully manual annotation

Retained as the phase-one baseline, not the final product. Manual annotations allow the product value and pattern logic to be tested before model automation is trusted.

### Always-on inference endpoint

Rejected for the initial workload. Full matches are offline, long-running jobs, and early traffic is expected to be bursty. Batch compute can scale down while idle.

## Consequences

### Positive

- Every insight can be reproduced and audited.
- Model failures can be isolated by component.
- User corrections can repair a report without rerunning every model.
- Models and calculation logic can evolve independently.
- Evidence-first UX aligns with the product positioning.

### Negative

- More artifacts, schemas, and versioning must be maintained.
- Confidence propagation across components requires careful calibration.
- Offline processing introduces latency and job orchestration complexity.
- Court and ball annotations are costly to create.

### Risks

- Ordinary footage may not support reliable ball localization.
- Error rates can compound across return detection, stroke classification, bounce localization, and point outcome.
- A statistically correct pattern may still be misleading with a small sample.
- User corrections could introduce noisy labels if reused without review.

## Validation required before acceptance

This ADR becomes **Accepted** only when a local vertical slice can:

1. Process at least five representative fixed-camera singles matches.
2. Produce structured return events and court-coordinate overlays.
3. Reproduce the return-depth statistic from annotated ground truth.
4. Link every aggregate result to reviewable evidence clips.
5. Recalculate the result after a correction without destroying the machine prediction.
6. Meet the evaluation gates in the [evaluation and rollout spec](../video-analysis/12-evaluation-and-rollout.md), or document revised gates supported by observed data.

## References

- [TrackNet: tracking high-speed and tiny objects in sports applications](https://arxiv.org/abs/1907.03698)
- [Amazon S3 event notification ordering and duplicate behavior](https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-how-to-event-types-and-destinations.html)
- [AWS Batch GPU jobs](https://docs.aws.amazon.com/batch/latest/userguide/gpu-jobs.html)
- [MediaConvert job progress](https://docs.aws.amazon.com/mediaconvert/latest/ug/how-mediaconvert-jobs-progress.html)
- [SageMaker Model Registry](https://docs.aws.amazon.com/sagemaker/latest/dg/model-registry.html)
