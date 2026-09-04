# 02: Media Inspection and Preprocessing

## Purpose

Convert allowed phone video into a deterministic representation for analysis while preserving an exact mapping to the original timeline.

## Inputs

- Original S3 object produced by the confirmed upload flow.
- Client-declared filename, size, duration, container, and codec.
- Analysis job and pipeline version.

## Authoritative inspection

Run `ffprobe` against the stored object or a local worker copy. Capture:

- Container and stream count
- Video and audio codecs
- Width, height, pixel aspect ratio, and display rotation
- Nominal and average frame rate
- Duration and start time
- Color transfer characteristics and HDR metadata
- Whether timestamps are variable or discontinuous
- Final object byte size

Reject corrupt media and authoritative values outside accepted product limits. Differences from client declarations are recorded as validation events.

## Analysis proxy

Produce a versioned proxy with this initial profile:

```text
container: MP4
video: H.264, yuv420p
resolution: fit within 1920x1080 without cropping
frame rate: constant 30 fps
orientation: pixels physically rotated upright
audio: AAC or omitted when event models do not use audio
keyframe interval: no more than 2 seconds
```

The profile is an implementation default, not a product promise. Ball-tracking experiments may require a higher frame rate or a full-resolution proxy; such a change must create a new preprocessing version.

## Timeline mapping

Write a manifest that maps proxy frame numbers and presentation timestamps to original-video milliseconds. Downstream components use original milliseconds in persisted events so evidence clips remain correct if the proxy changes.

## Derived objects

```text
videos/{video_id}/analysis/{job_id}/media/proxy.mp4
videos/{video_id}/analysis/{job_id}/media/manifest.json
videos/{video_id}/analysis/{job_id}/media/poster.jpg
```

Objects include checksums and content metadata. The original is never overwritten.

## Security and resource controls

- Treat media as untrusted input.
- Run tooling in a constrained container without public network access.
- Limit CPU, memory, local disk, output dimensions, and execution time.
- Never interpolate user-supplied filenames into commands or paths.
- Remove temporary worker files after success or failure.

## Failure behavior

Use `source_corrupt`, `unsupported_media`, `duration_exceeded`, `size_exceeded`, or `normalization_failed`. Preserve inspection output for internal debugging when retention policy permits.

## Acceptance criteria

- MOV/MP4 and H.264/HEVC samples produce the same proxy profile.
- Rotation and variable-frame-rate fixtures map to correct original timestamps.
- Corrupt and oversized inputs fail before GPU inference.
- Reprocessing with the same version produces equivalent media and manifest metadata.

