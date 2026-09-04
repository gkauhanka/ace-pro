# 05: Temporal Event Fusion

## Purpose

Convert perception outputs into tennis-domain events: point boundaries, serves, racket contacts, bounces, strokes, landing zones, and point outcomes.

## Inputs

- Court calibration and validity intervals
- Player tracks and court positions
- Pose landmarks
- Ball trajectory with visibility metadata
- Optional audio features
- Match metadata identifying the target player and court end

## Processing stages

### Candidate contacts

Find abrupt ball-velocity changes near a player, then score candidates with distance, pose, temporal motion, and optional audio evidence. One observation alone must not establish contact.

### Bounces

Detect trajectory changes consistent with court impact, project them into canonical court coordinates, and assign a named zone. For return depth, initial labels are:

```text
short: first post-return bounce inside the opponent service box
deep: first post-return bounce beyond the service line and inside the baseline
unknown: trajectory or calibration insufficient
```

Do not infer an in/out officiating call from an `unknown` or low-confidence bounce.

### Stroke classification

Classify serve, return, forehand, backhand, volley, and unknown over a temporal window around contact. The first opponent contact after a valid serve is the return. Handedness must be confirmed in player metadata or included as uncertainty.

### Points and outcomes

Group serve, contact, and bounce events into point intervals. Point outcome may initially come from manual annotation or user confirmation until automated winner detection meets its quality gate.

## Event schema

```json
{
  "event_id": "uuid",
  "point_id": "uuid",
  "event_type": "return_contact",
  "timestamp_ms": 754210,
  "player_role": "target",
  "attributes": {
    "stroke_side": "backhand",
    "landing_zone": "short"
  },
  "confidence": 0.86,
  "evidence_refs": ["player-track:...", "ball-track:..."],
  "fusion_version": "events-1"
}
```

Each field with independent uncertainty should retain component confidence internally. A single combined confidence is provided for filtering but must not erase diagnostic detail.

## Confidence combination

Do not multiply uncalibrated model scores. Calibrate each component against validation data, then train or define an event-level confidence function. Evaluate calibration with reliability diagrams and expected calibration error.

Events below the automatic threshold are stored but marked `review_required`. Events below the minimum usable threshold receive `unknown` labels and cannot support an insight.

## Corrections

Fusion reads immutable predictions. The effective event view applies the latest accepted human correction from the correction store. A correction to a point boundary can invalidate or reassign child events and must enqueue recalculation.

## Acceptance criteria

- Every return links to a serve, player, point, contact timestamp, and landing result or explicit unknown.
- Every landing zone links to a ball trajectory and valid court calibration.
- Events crossing inference chunks are neither duplicated nor dropped.
- Low-confidence fields remain unknown rather than receiving a forced label.
- Event outputs can be compared deterministically with annotated ground truth.

