# 08: Evidence Clips and Playback

## Purpose

Make every published insight reviewable without requiring the iOS app to download or seek through the full original match.

## Clip boundaries

Each evidence clip references an event or point and uses original-video milliseconds. Initial policy:

- Start 3–5 seconds before the relevant return or at point start, whichever is later.
- End at the detected point end plus up to 2 seconds.
- Cap normal clip length and flag abnormally long points for special handling.
- Include enough lead-in to understand serve, score context, and player position.

Clip policy is versioned. Changing padding does not change the underlying tennis event.

## Generation

Generate clips server-side from the normalized playback rendition or original when frame accuracy requires it. Prefer keyframe-aware extraction with a short re-encode when stream copy would produce inaccurate boundaries.

Generate:

- MP4 clip suitable for `AVPlayer`
- Poster thumbnail
- Optional contact/bounce overlay for debugging or reviewer mode
- Manifest with source, time range, checksum, and generator version

## Object layout

```text
videos/{video_id}/analysis/{job_id}/clips/{clip_id}.mp4
videos/{video_id}/analysis/{job_id}/clips/{clip_id}.jpg
videos/{video_id}/analysis/{job_id}/clips/{clip_id}.json
```

Do not include user names or original filenames in object keys.

## Delivery

Deliver derived clips through CloudFront. Access policy must match the product’s video privacy decision. The current storage design uses unlisted public URLs; this is not confidential access and must be revisited before storing sensitive annotations or enabling broader sharing.

The API returns a playback URL, thumbnail URL, duration, and time range. Clients must not receive S3 credentials or internal bucket names.

## Idempotency and lifecycle

Clip identity is derived from event, boundary policy version, source rendition, and overlay mode. Repeated requests reuse a valid existing artifact. When an event correction changes boundaries, create a new clip version and retire the old reference.

Deleting an original schedules deletion of all associated clips, thumbnails, and manifests followed by applicable CDN invalidation.

## Failure behavior

Clip generation failure does not change numeric insight truth, but an insight cannot be marked fully publishable until its required evidence is playable. Retry transient encoding and storage failures independently of vision inference.

## Acceptance criteria

- Clip playback begins before the relevant action and ends after the point result.
- Displayed timestamps map to the original within the evaluation tolerance.
- Correcting point boundaries creates updated evidence.
- Missing clips cannot leave a report claiming evidence is available.
- Video deletion removes original and derived playback paths.

