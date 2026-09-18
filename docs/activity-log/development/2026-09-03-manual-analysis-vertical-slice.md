# Manual return-depth analysis vertical slice

**Date:** September 3, 2026  
**Phase:** Development

## Goal

Implement the smallest evidence-backed analysis path that can validate the product workflow before investing in automated court, player, pose, and ball tracking.

## What I did

Implemented a backend vertical slice that:

- Creates an idempotent, versioned analysis job for a completed video.
- Downloads and inspects stored media with ffprobe.
- Accepts manually annotated point boundaries, winners, return timestamps, stroke sides, and landing zones.
- Calculates short-versus-deep backhand return loss rates with deterministic rules.
- Enforces initial sample and effect-size publication thresholds.
- Generates per-point MP4 evidence clips with FFmpeg and uploads them to object storage.
- Returns insights, evidence, clip URLs, confidence, and event revisions through FastAPI.
- Stores human corrections separately from machine/manual predictions.
- Recalculates affected insight metrics after a correction.
- Rejects stale concurrent corrections through event revision checks.

Added a database migration, sample annotation payload, API instructions, service and HTTP tests, and a test exercising the real FFmpeg adapter against generated video.

Applied the migration to the local PostgreSQL development database and ran the existing real PostgreSQL/MinIO upload integration test to confirm that the storage extensions did not regress multipart upload behavior.

## Key findings

- The evidence and correction workflow can be implemented independently of computer-vision accuracy.
- Keeping numeric insight calculation deterministic makes correction behavior simple to test and audit.
- Clip generation and media inspection fit behind an adapter, so synchronous local execution can later be replaced by queued workers without changing client contracts.
- A useful comparative insight needs both short and deep samples; reporting only the short-return loss rate would lack context.

## What changed

Before this activity, Ace Pro had upload/storage infrastructure, a mocked iOS experience, and a proposed video-analysis architecture, but no executable path from stored video to evidence-backed insight.

After this activity, the backend can complete that path using human annotations and real media clips. The product workflow can now be tested with players and coaches before the perception layer is automated.

Because of this, the next technical work should create a small ground-truth dataset and use the manual reports in product tests. Computer vision should automate the most costly annotation step only after the report itself proves useful.

## Open questions

- How long does it take to annotate one full match accurately?
- Are the initial sample and effect-size thresholds understandable and useful?
- Should an unpublished low-sample result appear in the player UI or remain reviewer-only?
- Does the current evidence-clip padding provide enough context?
- Which manual label consumes the most reviewer time and should be automated first?

## Next steps

- Upload one representative match and annotate it using the sample schema.
- Connect the iOS report and correction screens to the new API.
- Test the resulting report with a player and coach.
- Record annotation time, corrections, and any change in practice decision.
