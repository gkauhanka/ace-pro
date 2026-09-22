# Ace Pro App Store submission checklist

## Recommended listing

**Name:** Ace Pro

**Subtitle:** Private tennis video review

**Promotional text:** Review your tennis sessions privately with on-device motion and pose measurements. Your videos never leave your iPhone.

**Description:**

Ace Pro helps you revisit tennis sessions without uploading your footage. Build a private local library, run Apple Vision measurements directly on your iPhone, jump to detected motion ranges and pose frames, and keep your own observations in a session journal.

Ace Pro reports generic motion and pose measurements. It does not identify tennis balls, classify strokes, diagnose technique, or replace a coach. Results depend on video quality, camera position, lighting, and how clearly the player is visible.

Features:

- Import from Photos or Files
- Protected on-device video library
- Motion-candidate time ranges
- 2D and 3D body-pose samples
- Hand-pose and scene-motion samples
- Exact-frame and bounded-clip review
- Optional on-device Apple Intelligence descriptions on eligible devices
- Private session observations
- No account, ads, tracking, analytics, or video upload

**Keywords:** tennis,video,review,practice,pose,motion,journal,training

**Category:** Sports

**Privacy Policy URL:** https://github.com/gkauhanka/ace-pro/blob/main/docs/privacy-policy.md

**Support URL:** https://github.com/gkauhanka/ace-pro/blob/main/docs/support.md

## App Review notes

Ace Pro requires no account. On first launch, tap **Add a tennis video**, select any local video from Photos or Files, save it, open the session, and choose **On-device video analysis**. Select 15 seconds for the fastest review path.

All video decoding and Apple Vision processing occurs on the device. The app has no production server connection and does not upload video or session metadata. Motion candidates are generic Apple Vision trajectories and are intentionally not labeled as tennis balls. Pose results are measurements, not technique diagnoses.

The optional **Generate description** action requires an Apple Intelligence-eligible device, a supported iOS version, and Apple Intelligence enabled. The rest of the application does not require Apple Intelligence.

Individual sessions can be deleted from the session screen. All app data can be deleted under **Settings → Delete all app data**. Original source files are not modified.

## App privacy answers

For the current offline release, select **Data Not Collected** only after verifying the final archive contains no added analytics, advertising, crash-reporting, or networking SDK. The support and privacy links open GitHub in the user's browser; routine website data is handled by GitHub rather than collected by the iOS application or developer.

Tracking: **No**

## Age rating

Answer the current App Store Connect questionnaire based on the shipped binary. The present app has no user-generated content sharing, web browsing inside the app, gambling, contests, violence, mature content, or unrestricted app-to-app messaging. External support links open a browser.

## Export compliance

`ITSAppUsesNonExemptEncryption` is set to `false`. Reconfirm this answer if future versions add custom cryptography, VPN functionality, or non-system encryption beyond Apple's operating-system services.

## Screenshots to capture

1. Today screen with the private on-device positioning.
2. Local video library.
3. Session review with the on-device analysis entry.
4. Analysis summary with measured results and limitations visible.
5. Motion candidate bounded playback or an exact pose frame.
6. Local journal.

Do not use the browser prototype walkthrough, simulated reports, development endpoint screens, or unsupported tennis-performance claims in screenshots or listing text.

## Before uploading

- [ ] Enroll in the paid Apple Developer Program and select its distribution team.
- [ ] Confirm `com.glebkauhanka.acepro` is registered to that team, or replace it consistently with an owned identifier.
- [ ] Increment `CURRENT_PROJECT_VERSION` for every uploaded build.
- [ ] Run a signed Release archive and **Validate App** in Xcode Organizer.
- [ ] Test importing, analysis cancellation, deletion, low storage, backgrounding, and relaunch on physical devices.
- [ ] Profile a 60-second analysis for heat, memory, and battery use on the oldest supported iPhone.
- [ ] Test VoiceOver, Dynamic Type, Reduce Motion, and light-mode contrast.
- [ ] Confirm the public privacy and support URLs load without authentication.
- [ ] Capture screenshots from the exact submitted build.
- [ ] Complete the latest age-rating, content-rights, privacy, and export-compliance questions.
- [ ] Add the App Review notes above and submit.
