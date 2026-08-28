# Ace Pro

Ace Pro is an early-stage tennis match analysis project. The goal is to turn ordinary match video into useful statistics and searchable clips that help players understand patterns in their game without manually reviewing an entire recording.

The initial direction is to focus on full-match analysis for players, with coaches as a secondary user group. Before defining the MVP, the project will validate which insights are genuinely useful and which tennis events current AI video models can detect reliably.

## Video storage implementation

The first backend slice implements resumable direct-to-object-storage video transfer with FastAPI, PostgreSQL, local MinIO testing, and production-shaped AWS Terraform. See the [backend runbook](./backend/README.md) and [storage design](./docs/video-storage-design.md).

## iOS UX prototype

The first SwiftUI app prototype lives in [`ios`](./ios). It uses mocked match data and covers prioritized insights, supporting clips, detection correction, match history, team context, and the upload experience without requiring the backend.

## Next action items

- Interview a tennis coach about how they evaluate players and review match footage.
- Interview at least one additional player about useful post-match information.
- Research comparable sports analytics products and how they provide value.
- Select three to five candidate statistics for the first feasibility tests.
- Find or record representative tennis match footage from realistic camera angles.
- Test multiple AI/video models on specific tennis events.
- Document model accuracy, limitations, and camera requirements.
- Use the discovery and experiment results to define the MVP scope.

## Project activity log

Discovery notes, technical experiments, and development milestones are documented in the [activity log](./docs/activity-log/README.md).
