# 01: Analysis Jobs and Orchestration

## Purpose

Start exactly one logical analysis for each `(video_id, pipeline_version)`, coordinate long-running stages, expose progress, and recover safely from retries or duplicate events.

## Trigger

After `CompleteUploadService` has verified the completed object and committed the video’s ready state, the application must transactionally create or enqueue an analysis request. If transactional outbox infrastructure is not yet available, the completion handler may create the `analysis_jobs` row synchronously and a sweeper may enqueue unsubmitted rows.

Raw S3 notifications must not be treated as exactly-once triggers. S3 notifications can be duplicated and arrive out of order.

## State model

```text
queued -> inspecting -> normalizing -> quality_check
       -> detecting -> fusing_events -> generating_insights
       -> generating_clips -> ready

Any active state -> failed
failed -> queued             only through an explicit retry
Any nonterminal state -> canceled
```

Persist `stage`, `stage_progress`, and `overall_progress` separately. Overall progress is an estimate for UX and must never be used as a correctness signal.

## Job identity and idempotency

- Primary identifier: opaque UUID.
- Unique key: `(video_id, pipeline_version)`.
- Each stage has a deterministic artifact namespace containing the job and component version.
- A retry first checks whether the expected artifact exists and passes integrity checks.
- Consumers acknowledge queue messages only after their database transition is durable.
- Stage transitions use compare-and-swap semantics against the expected previous state.

## Stage contract

Every stage receives:

```json
{
  "job_id": "uuid",
  "video_id": "uuid",
  "pipeline_version": "analysis-1",
  "attempt": 1,
  "input_artifacts": []
}
```

Every stage returns artifact references, metrics, component version, start/end timestamps, and either success or a typed failure.

## Retry policy

- Retry infrastructure failures with exponential backoff and jitter.
- Do not automatically retry permanent validation failures.
- Limit GPU-stage retries to avoid uncontrolled cost.
- Make `failure_code`, `failure_stage`, and a user-safe failure message available to the API.
- Keep detailed exception text in logs, not client responses.

Suggested failure classes:

```text
source_missing
source_corrupt
unsupported_media
quality_gate_failed
model_artifact_missing
gpu_capacity_timeout
inference_failed
artifact_write_failed
calculation_failed
clip_generation_failed
```

## Cancellation and deletion

A video deletion marks active jobs canceled before removing artifacts. Workers check cancellation between chunks and before publishing outputs. Cleanup must be idempotent and tolerate already-missing objects.

## Observability

Record job duration, queue wait, stage duration, retries, failure code, GPU seconds, frames processed, and artifact bytes. Every log line includes `job_id`, `video_id`, `stage`, `attempt`, and version.

## Acceptance criteria

- Duplicate triggers result in one logical job.
- A worker crash can resume from the last valid stage artifact.
- The API reports current stage and user-safe progress.
- Permanent media failures do not retry indefinitely.
- Deletion cancels work and schedules derived-artifact cleanup.

