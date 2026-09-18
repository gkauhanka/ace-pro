# Record the Ace Pro experience

A reproducible, silent mobile-browser recording using a fresh Playwright context. It never opens a real user profile or uses personal footage. The test account and generated court animation exist only in the recording context. The original app and its API run unmodified.

Requirements: Node 22+, ffmpeg, and Google Chrome on macOS (or Playwright Chromium on other platforms).

From the repository root:

```sh
node insights-api/server.mjs
```

In another terminal:

```sh
cd tools/recording
npm ci
npx playwright install ffmpeg
# On platforms other than macOS, also run: npx playwright install chromium
bash make-fixture.sh
npm run record
bash export.sh
```

The recorder captures onboarding/account creation, actual local MP4 import, processing, API insights, timestamp playback, saved drills, notes, practice plan, and related moments across two sessions. It checks for browser errors and verifies two insights calls containing only the three permitted metadata fields. It uses a 430 × 932 mobile viewport, then exports H.264 MP4 and a smaller looping GIF for GitHub README compatibility.

Outputs committed to the repository:

- `docs/media/ace-pro-walkthrough.mp4` — full video, no audio.
- `docs/media/ace-pro-preview.gif` — inline animated README preview.
- `docs/media/ace-pro-poster.png` — still image for reuse.

Raw recordings, generated fixture files, installed dependencies and verification output are gitignored. `raw/verification.json` records the successful flow checks. Set `ACE_PREVIEW_URL` or `ACE_VIDEO_FIXTURE` to override the local URL or synthetic fixture.

This is a recording of the browser experience, not an iOS Simulator recording or evidence of actual tennis analysis.
