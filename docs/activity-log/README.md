# Activity Log

This folder documents the discovery, experimentation, and development process for the project. The goal is to create a clear, chronological record so the repository and its Git history tell the story of how the product evolved.

## Instructions for AI contributors

When adding to the activity log, follow these rules:

1. Create one Markdown file for each meaningful activity. An activity does not need to correspond to a single day.
2. Put the file in the category that best describes the work:
   - `discovery/` for problem exploration, interviews, user research, competitor research, and product discovery.
   - `experiments/` for feasibility tests, prototypes, model evaluations, and technical investigations.
   - `development/` for implementation milestones, integrations, testing, fixes, and substantial improvements.
3. Name files using `YYYY-MM-DD-short-description.md`, for example `2026-08-15-coach-interview.md`.
4. Write entries chronologically and describe what actually happened. Do not invent results, dates, interviews, decisions, or evidence.
5. Emphasize how the activity affected the project. The `What changed` section is required and should explain changes in assumptions, priorities, scope, design, or implementation.
6. Add each new entry to the appropriate index below, ordered by date.
7. Prefer a separate file over one large running log so each activity has its own links and Git history.
8. Keep commits focused on one meaningful activity when practical.

## Entry template

```md
# Activity title

**Date:** Month DD, YYYY  
**Phase:** Discovery | Experiment | Development

## Goal

What question, problem, or objective motivated this activity?

## What I did

What work was completed? Include enough context for someone reviewing the project later.

## Key findings

- What was learned?
- What evidence or observations support it?

## What changed

What did the project team believe or plan before this activity?

What is understood or planned differently afterward?

What change in priorities, scope, design, or implementation follows from this?

## Open questions

- What remains uncertain?

## Next steps

- What should happen next?
```

The `What changed` section should show the reasoning explicitly. A useful pattern is:

> Before this activity, I thought ...
>
> After reviewing the evidence, it appears ...
>
> Because of this, the project should ...

## Discovery

Discovery entries belong in [`discovery/`](./discovery/).

- [Initial Discovery](./discovery/2026-08-12-initial-discovery.md) — August 12, 2026
- [Competitor Research and Product Positioning](./discovery/2026-08-13-competitor-research-and-positioning.md) — August 13, 2026

## Technical experiments

Experiment entries belong in [`experiments/`](./experiments/).

<!-- Add dated experiment entries here. -->

## Development

Development entries belong in [`development/`](./development/).

<!-- Add dated development entries here. -->

## Commit message examples

Use concise messages that describe the meaningful activity:

```text
docs: add initial product discovery notes
docs: document coach interview findings
research: compare existing sports analytics products
experiment: test AI tennis video understanding
docs: define MVP based on discovery findings
feat: add video upload
feat: add match statistics view
fix: improve point boundary detection
```

The intended project timeline is:

```text
Idea
-> Problem discovery
-> User interviews
-> Research
-> Technical feasibility
-> MVP decision
-> Prototype
-> Testing
-> Improvements
```
