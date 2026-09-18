# Ace Pro insights experience

Run from the repository root:

```sh
node insights-api/server.mjs
```

Open http://localhost:8787. No install, API key, database, video server or ML service is required. Node 22+ is required. Stop the process with Ctrl-C.

The browser preview mirrors the native iOS product flow. It uses IndexedDB for video blobs, reports, profile and notes; credentials use a random salt and PBKDF2-SHA256 with 210,000 iterations. Browser storage can be cleared/evicted, so retain original videos. Native iOS uses app-private file storage, file protection, backup exclusion, and Keychain credentials instead.

## Try it

1. Choose guest mode or create a device account. Accounts are local demonstrations, not cloud authentication. Guest and the single device account share one library.
2. Add a video, choose Match/Practice and a focus. Without a video, the browser can create a short labeled court animation locally.
3. Watch simulated processing. The app makes one POST request to `/api/insights` for each analysis attempt. Video bytes never enter the request.
4. Open an insight, save its drill, play a sample timestamp, and write a real observation.
5. Add another session with the same focus to see related timestamps grouped across videos.
6. Reload and enter again to verify persistence. Review saved drills under Improve.
7. Delete individual sessions or all local data from Profile. Original input files are never modified.

## API contract

`POST /api/insights`, `Content-Type: application/json`:

```json
{"durationSeconds":90,"sessionType":"Practice","focus":"Footwork"}
```

Allowed focus values: All-round, Footwork, Technique, Serve, Tactics. Duration: 1 second–6 hours. Additional properties are rejected, as are non-JSON payloads. The local HTTP server rejects bodies over 1 KB before parsing. The Vercel handler rejects oversized parsed metadata; the platform handles request parsing before invocation.

The response has `schemaVersion: 1`, `simulated: true`, a disclosure, and three randomized coaching examples. Review times are illustrative and bounded to the selected duration. Neither observations nor performance improvements are inferred from video. No request body or account details are logged by application code. Hosting infrastructure may retain normal request/IP logs.

## Vercel deployment, next phase

Import this repository in Vercel, set Root Directory to `insights-api`, and use the included configuration. Static preview assets are in `preview`; the single Node function is `api/insights.mjs`. Set the iOS Profile service URL to `https://YOUR-PROJECT.vercel.app/api/insights`. No video upload service or secret is required. Deployment has not been performed as part of local implementation.

Before public release, configure a production HTTPS endpoint as the default, remove developer endpoint editing, configure host-level abuse protection and retention, and publish owner-specific support/privacy URLs. The API is deliberately public and stores no user records.

## Verification

```sh
node --test insights-api/tests/*.test.mjs
node --check insights-api/preview/app.js
```

Contract tests cover duration boundaries, bounded timestamps, category selection, rejection of video/personal-data fields, HTTP methods, malformed JSON, content type, and request size. Browser manual verification covers local demo video generation, API reports, timestamp playback, saved drills, notes, reload persistence device account creation, sign-out, invalid-password rejection and successful login. The reproducible Playwright walkthrough additionally verifies actual MP4 import, two-session review, browser error checks, and metadata-only request payloads. Native Photos/Files selection remains an iOS QA item. Native verification limitations are described in `../ios/README.md`.
