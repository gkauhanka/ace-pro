# 06: Pattern and Insight Engine

## Purpose

Calculate statistically defensible, prioritized findings from effective events. This component owns numeric truth and evidence selection.

## Initial pattern

The first rule evaluates backhand return depth for the target player.

Eligible points must contain:

1. A valid serve and target-player return.
2. A backhand classification above the configured threshold or human confirmation.
3. A short/deep landing classification above threshold or human confirmation.
4. A known point outcome.

Calculation:

```text
short_count = count(eligible short backhand returns)
short_losses = count(short backhand returns followed by point loss)
short_loss_rate = short_losses / short_count

deep_count = count(eligible deep backhand returns)
deep_losses = count(deep backhand returns followed by point loss)
deep_loss_rate = deep_losses / deep_count

effect_difference = short_loss_rate - deep_loss_rate
```

Display integer counts alongside percentages to prevent false precision.

## Publication gate

Initial configurable defaults:

```text
short_count >= 6
eligible event confidence >= 0.80
insight confidence >= 0.80
effect_difference >= 0.15
known point outcome coverage >= 0.90
```

These values are hypotheses to validate, not permanent constants. When the baseline group is too small, the engine may publish a neutral observation with explicit limitations, but must not claim a comparative effect.

## Ranking

Rank candidate patterns with a versioned score based on:

- Estimated effect size
- Sample sufficiency
- Confidence and correction coverage
- Recurrence across sets or match phases
- Actionability taxonomy
- Novelty relative to recent matches

Ranking is not causal inference. Copy must say that the pattern was associated with outcomes, not that it caused them.

## Insight record

```json
{
  "insight_type": "backhand_return_depth",
  "rule_version": "return-depth-1",
  "rank": 1,
  "metrics": {
    "short_count": 11,
    "short_losses": 7,
    "short_loss_rate": 0.636,
    "deep_count": 8,
    "deep_losses": 3,
    "deep_loss_rate": 0.375
  },
  "confidence": 0.84,
  "evidence_event_ids": ["..."],
  "limitations": []
}
```

## Evidence selection

Include all eligible events in the calculation lineage. The UI may initially show a representative subset, but must let the user reach the complete set. Select representative clips across sets and confidence levels; do not cherry-pick only dramatic examples.

## Recalculation

Rules operate on an effective-event snapshot version. When a correction changes an eligible field, enqueue only the affected match and pattern families. Retain prior insight versions for audit but expose the latest valid version by default.

## Acceptance criteria

- Given the same effective-event snapshot and rule version, output is deterministic.
- Percentages always reconcile with displayed counts.
- Every metric can be traced to included and excluded event IDs with reason codes.
- Insufficient samples do not produce a ranked performance claim.
- Corrections produce a new insight version and preserve the old calculation.

