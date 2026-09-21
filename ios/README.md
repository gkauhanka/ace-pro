# Ace Pro · native iOS experience

SwiftUI, iOS 17+. The application now opens the local-video coaching experience in `RootView.swift`. Earlier mock screens remain in the repository for reference but are not part of the active navigation.

Implemented:

- Onboarding, optional single device account, login, guest mode, sign-out and in-app deletion.
- Salted PBKDF2-SHA256 password derivation (210,000 iterations); profile credentials in device-only Keychain.
- PhotosPicker and Files import. App-private protected video copies excluded from device backup; originals remain unchanged.
- Persistent library with local video thumbnails, search and Match/Practice filters.
- Metadata-based insights requests, coaching priorities, practice drills, saved plans and personal notes.
- Apple Vision trajectory detection with start/end times, bounded AVPlayer playback and noisy-frame recovery.
- Apple Vision 2D/3D body pose, hand pose and optical-flow diagnostics, with exact-frame review links.
- Optional on-device Apple Intelligence descriptions generated only from measured debug results on eligible devices.
- Failure/retry states, pending sessions retained after service failures, local deletion, privacy explanation, app icon and UserDefaults privacy manifest.

Accounts are intentionally a device experience, not a cloud identity system. Guest mode and the account share one device library; login is not a privacy boundary. There is no email verification, remote account service, synchronization or password recovery.

## Run locally

Full Xcode is required. The app has been compiled successfully for both an iOS Simulator and a physical iPhone.

1. Install Xcode and complete its first-launch setup.
2. Start `node insights-api/server.mjs` from the repository root.
3. Open `ios/AcePro.xcodeproj`, select the AcePro scheme and an iPhone Simulator or connected iPhone, and press Run (`⌘R`). For a physical device, select your Apple development team and use a unique bundle identifier under Signing & Capabilities.
4. Simulator defaults to `http://localhost:8787/api/insights`. For a physical device, deploy the API to Vercel and use its HTTPS URL in Profile.
5. Import an actual video into Simulator Photos or use Files. Explore the full flow.

To run the on-device detectors, open a saved session, choose **Apple Vision debug**, select 15, 30 or 60 seconds, and tap **Run on-device analysis**. Motion candidates open at their detected start time and pause at the detected end. Pose, hand and optical-flow results open paused at the sampled frame. The **Generate description** action requires iOS 26 or later, an Apple Intelligence-eligible device and Apple Intelligence enabled.

All Vision processing in this debug flow happens locally. The detector intentionally calls trajectories “motion candidates”: Apple Vision does not identify tennis balls or stroke types. Tennis-specific ball/racket detection and action classification require trained Core ML assets and representative labeled footage. Debug results currently remain in memory and must be regenerated after relaunching the app.

The checked-in Xcode project and `project.yml` include the privacy manifest and app icon. Info.plist permits local-network HTTP for development; release app code requires HTTPS for the insights endpoint. No Photos full-library permission is requested: the system picker grants selected-file access.

## Checks performed

- Swift syntax parsed with `swiftc -frontend -parse ios/AcePro/*.swift`.
- Full Debug builds completed against the iPhone Simulator and physical-device SDKs.
- Xcode project, Info.plist and privacy manifest validated with `plutil`.
- API tests and browser end-to-end verification passed.

These checks are not substitutes for comprehensive device testing, Vision accuracy evaluation on labeled footage, VoiceOver/Dynamic Type testing, thermal and battery profiling, or an App Store archive validation. See `../docs/app-store-experience.md` for the remaining release work.
