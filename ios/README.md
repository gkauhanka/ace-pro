# Ace Pro for iPhone

Ace Pro is a SwiftUI iOS 17+ application for private, on-device tennis video review.

## Release feature set

- Import a user-selected video from Photos or Files.
- Keep a protected app-private copy excluded from device backups.
- Organize match and practice sessions in a searchable local library.
- Run Apple Vision trajectory, 2D/3D body-pose, hand-pose, and optical-flow measurements on the iPhone.
- Open motion candidates at their measured start time and pause at their measured end.
- Open pose results paused at the measured frame.
- Optionally summarize numeric measurements with Apple Intelligence on eligible devices.
- Save the user's own session observations in a local journal.
- Delete one session or all app data in the app.

The release application has no account, server connection, video upload, analytics, advertising, or tracking. Motion candidates are not identified as tennis balls, pose measurements are not technique diagnoses, and the app does not claim to classify strokes.

## Run locally

1. Open `AcePro.xcodeproj` in a current Xcode release.
2. Select the AcePro scheme and an iPhone Simulator or connected iPhone.
3. For a physical device, select an available Apple development team under Signing & Capabilities.
4. Press Run (`Command-R`).
5. Import a video, open its session, and choose **On-device video analysis**.

No local API is required for the native application. The separate `insights-api` directory is an experimental browser prototype and is not linked into the iOS release.

## Analysis limitations

Apple Vision supplies generic measurements rather than tennis semantics:

- trajectory detections may represent a tennis ball, racket, player, camera movement, or background motion;
- pose detection depends on the player being visible and sufficiently large in the frame;
- optical flow represents overall pixel movement and is not an action classifier; and
- Foundation Models descriptions are only available on supported hardware, supported iOS versions, and devices where Apple Intelligence is enabled.

The results currently remain in memory and must be regenerated after leaving the analysis screen.

## Verification

From the repository root, run:

```sh
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer \
  xcodebuild -project ios/AcePro.xcodeproj \
  -scheme AcePro -configuration Release -sdk iphoneos \
  -destination 'generic/platform=iOS' \
  -derivedDataPath /tmp/AceProRelease \
  CODE_SIGNING_ALLOWED=NO build
```

Also validate `Info.plist` and `PrivacyInfo.xcprivacy` with `plutil -lint`. Device testing, archive signing, App Store Connect validation, accessibility review, and thermal profiling remain required release checks.

See the [submission checklist](../docs/app-store-submission.md), [privacy policy](../docs/privacy-policy.md), and [support page](../docs/support.md).
