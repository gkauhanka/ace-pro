# Ace Pro · native iOS experience

SwiftUI, iOS 17+. The application now opens the local-video coaching experience in `RootView.swift`. Earlier mock screens remain in the repository for reference but are not part of the active navigation.

Implemented:

- Onboarding, optional single device account, login, guest mode, sign-out and in-app deletion.
- Salted PBKDF2-SHA256 password derivation (210,000 iterations); profile credentials in device-only Keychain.
- PhotosPicker and Files import. App-private protected video copies excluded from device backup; originals remain unchanged.
- Persistent library with local video thumbnails, search and Match/Practice filters.
- Simulated processing followed by one real metadata-only insights request per attempt.
- Explicit random-example disclosure, three coaching priorities, example statistics, practice drills, YouTube links, saved plans and personal notes.
- AVPlayer playback at sample timestamps and related technique review points across videos.
- Failure/retry states, pending sessions retained after service failures, local deletion, privacy explanation, app icon and UserDefaults privacy manifest.

Accounts are intentionally a device experience, not a cloud identity system. Guest mode and the account share one device library; login is not a privacy boundary. There is no email verification, remote account service, synchronization or password recovery.

## Run locally

Full Xcode and an iOS Simulator runtime are required. This machine currently has only Command Line Tools, so a native build/Simulator launch could not be performed.

1. Install Xcode from Apple and complete its first-launch setup, including an iOS Simulator runtime.
2. Start `node insights-api/server.mjs` from the repository root.
3. Open `ios/AcePro.xcodeproj`, select the AcePro scheme and an iPhone Simulator, and run.
4. Simulator defaults to `http://localhost:8787/api/insights`. For a physical device, deploy the API to Vercel and use its HTTPS URL in Profile.
5. Import an actual video into Simulator Photos or use Files. Explore the full flow.

The checked-in Xcode project and `project.yml` include the privacy manifest and app icon. Info.plist permits local-network HTTP for development; release app code requires HTTPS for the insights endpoint. No Photos full-library permission is requested: the system picker grants selected-file access.

## Checks performed

- Swift syntax parsed with `swiftc -frontend -parse ios/AcePro/*.swift`.
- Storage, networking, crypto and profile types type-checked against the available macOS SDK (shared frameworks only).
- Xcode project, Info.plist and privacy manifest validated with `plutil`.
- API tests and browser end-to-end verification passed.

These are not substitutes for an iOS SDK build, device testing, VoiceOver/Dynamic Type testing, or an App Store archive validation. See `../docs/app-store-experience.md` for the remaining release work.
