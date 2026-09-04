# 07: Narrative Generation

## Purpose

Render structured insights into concise player- and coach-facing language without creating new facts, statistics, evidence, or diagnoses.

## Default implementation

Start with deterministic templates. A language model is optional and should be introduced only when templates demonstrably limit comprehension or useful personalization.

Example template:

```text
You lost {short_losses} of {short_count} points ({short_loss_rate}%)
after a short backhand return, compared with {deep_losses} of
{deep_count} ({deep_loss_rate}%) after a deep return.
```

## Language-model contract

If enabled, the model receives only a validated structured insight and an allowed vocabulary. It returns JSON matching a strict schema:

```json
{
  "title": "Short backhand returns were costly",
  "summary": "You lost 7 of 11 points after a short backhand return.",
  "review_prompt": "Review return position and contact point with your coach.",
  "cited_event_ids": ["evt-1", "evt-8"]
}
```

The service validates that:

- All numbers occur in the input metrics.
- Cited events are a subset of supplied evidence.
- Required counts appear when a percentage is mentioned.
- Disallowed medical, injury, or technique diagnoses are absent.
- The output does not claim causation.

Invalid output falls back to a deterministic template; it does not trigger repeated open-ended regeneration.

## Copy principles

- State observations before suggestions.
- Use “was associated with” or direct counts, not “caused.”
- Distinguish player-facing practice prompts from coach interpretation.
- Include uncertainty or sample limitations when supplied by the rule engine.
- Never hide corrected or disputed evidence.

## Versioning and audit

Persist prompt/template version, provider/model identifier when applicable, structured input hash, validated output, and validation outcome. Narrative changes do not require rerunning vision inference.

Do not send original video, faces, filenames, or unnecessary personal data to a language-model provider. Provider retention and data-processing terms require a separate privacy decision before production use.

## Acceptance criteria

- Removing the language model still yields a complete usable report.
- Generated numbers and cited IDs exactly match structured input.
- Invalid or unavailable generation falls back without blocking analysis.
- Identical template input produces identical copy for the same version.

