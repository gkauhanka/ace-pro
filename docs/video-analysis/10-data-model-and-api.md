# 10: Data Model and API

## Purpose

Define the persistent entities and external contracts needed to expose analysis without coupling the iOS app to model-specific artifacts.

## Core relational entities

### `analysis_jobs`

```text
id UUID PK
video_id UUID FK videos
pipeline_version VARCHAR
status VARCHAR
stage VARCHAR
stage_progress NUMERIC
overall_progress NUMERIC
attempt INTEGER
failure_code VARCHAR NULL
failure_message VARCHAR NULL
created_at, started_at, completed_at, updated_at TIMESTAMPTZ
UNIQUE(video_id, pipeline_version)
```

### `analysis_artifacts`

```text
id UUID PK
job_id UUID FK
artifact_type VARCHAR
component_name VARCHAR
component_version VARCHAR
object_key VARCHAR
checksum VARCHAR
metadata JSONB
created_at TIMESTAMPTZ
```

### `points`

```text
id UUID PK
job_id UUID FK
sequence_number INTEGER
start_ms BIGINT
end_ms BIGINT
winner_role VARCHAR NULL
confidence NUMERIC
prediction_revision INTEGER
UNIQUE(job_id, sequence_number)
```

### `events`

```text
id UUID PK
point_id UUID FK
event_type VARCHAR
timestamp_ms BIGINT
player_role VARCHAR
attributes JSONB
confidence NUMERIC
model_version VARCHAR
prediction_revision INTEGER
created_at TIMESTAMPTZ
```

### `event_corrections`

```text
id UUID PK
event_id UUID FK
base_event_revision INTEGER
corrected_fields JSONB
actor_id VARCHAR
actor_role VARCHAR
reason VARCHAR NULL
created_at TIMESTAMPTZ
```

### `insights` and evidence

```text
insights: id, job_id, type, rule_version, snapshot_version, rank,
          metrics JSONB, confidence, status, title, summary,
          limitations JSONB, created_at

insight_evidence: insight_id, event_id, clip_id, inclusion_role

clips: id, job_id, start_ms, end_ms, object_key, thumbnail_key,
       generator_version, status, created_at
```

Use typed columns for identities, filtering, ordering, timestamps, status, and confidence. JSONB is limited to evolving component-specific attributes and metrics.

## API resources

Suggested endpoints under `/api/v1`:

```text
POST   /videos/{video_id}/analyses
GET    /videos/{video_id}/analyses/latest
GET    /analyses/{analysis_id}
POST   /analyses/{analysis_id}/retry
DELETE /analyses/{analysis_id}

GET    /analyses/{analysis_id}/insights
GET    /insights/{insight_id}
GET    /insights/{insight_id}/evidence

GET    /events/{event_id}
POST   /events/{event_id}/corrections
GET    /analyses/{analysis_id}/review-queue
```

Creating an analysis is idempotent and may return the existing job for the selected pipeline version.

## Example analysis response

```json
{
  "id": "analysis-id",
  "video_id": "video-id",
  "status": "detecting",
  "stage": "ball_tracking",
  "progress": 0.58,
  "capabilities": {
    "return_depth": "supported",
    "point_outcome": "review_required"
  },
  "pipeline_version": "analysis-1"
}
```

## Example insight response

```json
{
  "id": "insight-id",
  "type": "backhand_return_depth",
  "rank": 1,
  "title": "Short backhand returns were costly",
  "metrics": {
    "short": {"points": 11, "losses": 7, "loss_rate": 0.636},
    "deep": {"points": 8, "losses": 3, "loss_rate": 0.375}
  },
  "confidence": 0.84,
  "evidence_count": 11,
  "review_required_count": 2,
  "snapshot_version": 3
}
```

## API rules

- Enforce video ownership on every analysis resource.
- Use stable enum values and additive API evolution.
- Return opaque identifiers and playback URLs, not object keys.
- Use cursor pagination for events and evidence.
- Include `ETag` or revision values for correction concurrency.
- Keep internal stack traces, model paths, and provider responses out of public errors.

## Retention and deletion

Video deletion marks dependent resources unavailable immediately, cancels active jobs, and asynchronously removes derived objects. Relational data may be hard-deleted or retained in de-identified audit form only after a separate retention decision.

## Acceptance criteria

- Ownership cannot be bypassed through event or insight IDs.
- The client can render all UX states without reading raw model artifacts.
- API percentages reconcile with integer counts.
- Concurrent corrections produce an explicit conflict.
- Video deletion makes all playback resources inaccessible after the documented propagation window.

