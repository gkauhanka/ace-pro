# 09: Human Review and Corrections

## Purpose

Allow players and coaches to repair uncertain predictions, understand what changed, and improve the report without concealing model errors.

## Review queue

Prioritize review items by expected effect on published insights:

1. Events whose correction could add, remove, or reverse the top insight.
2. Low-confidence events currently included in calculations.
3. Boundary and point-outcome uncertainty.
4. Remaining optional verification items.

Do not ask users to validate high-volume frame predictions. Review tennis-domain events with the relevant clip and a small controlled set of labels.

## Correction model

Predictions are immutable. A correction records:

```json
{
  "correction_id": "uuid",
  "event_id": "uuid",
  "base_event_revision": 2,
  "fields": {
    "stroke_side": "backhand",
    "landing_zone": "deep"
  },
  "actor_id": "user-id",
  "actor_role": "player",
  "created_at": "2026-09-03T20:00:00Z",
  "reason": "user_review"
}
```

Use optimistic concurrency through `base_event_revision`. If another correction has changed the event, return a conflict and show the latest effective value.

## Permissions

- A player can correct events for their own matches.
- Coach permissions require an explicit team authorization model.
- The API records actor identity and role.
- Automated jobs cannot create human corrections.

## Recalculation

After accepting a correction:

1. Increment the effective-event snapshot version.
2. Identify dependent pattern families.
3. Mark affected insights stale.
4. Recalculate deterministically.
5. Regenerate narrative and clips only when affected.
6. Notify the client when the refreshed report is available.

The UI should explain material changes, for example: “Updated from 64% to 55% after one return was corrected.”

## Training-data use

Corrections are not automatically ground truth. Reuse for training requires user consent, privacy controls, de-identification where appropriate, and expert or dual review. Preserve provenance and avoid evaluation leakage.

## Acceptance criteria

- A correction never overwrites the original prediction.
- A stale client cannot silently replace a newer correction.
- A corrected event changes all and only dependent calculations.
- Previous report versions remain internally auditable.
- Users can distinguish machine-predicted, verified, and corrected values.

