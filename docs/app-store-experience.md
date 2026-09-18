# Ace Pro: product and release boundary

## Product design

Ace Pro is a private tennis video journal with clearly labeled, randomly generated coaching inspiration. The core loop is **save a session → review local footage → choose one focus → practice → record your observations**.

The visual direction is warm white, deep court green and tennis-ball lime; generous rounded cards, restrained statistics and a four-tab native navigation: Today, Library, Improve, Profile. Real utility comes from keeping videos organized, playing review points, writing personal notes and carrying a practice plan onto the court.

Example coaching topics: split-step timing, contact spacing, recovery position, second-serve consistency and rally depth. Each report has three priorities, a sample percentage, a cue, an actionable drill, a YouTube tutorial link and three illustrative timestamps. Related topics are grouped across sessions. Random percentages must never become a claimed progress trend or evidence of an actual error.

## Data boundary

| Information | Native storage | Network |
| --- | --- | --- |
| Videos | Protected app-private files, excluded from backup | Never sent |
| Profile/email/password derivative | Device-only Keychain | Never sent |
| Reports, observations | Local JSON | Never sent |
| Saved drill IDs, service setting | UserDefaults | Never sent |
| Duration, session type, focus | Included in local report context | One JSON request per analysis attempt |
| Connection information | Host-dependent | IP/request logs may be retained by hosting infrastructure |

PhotosPicker can download an iCloud-backed original through Apple's photo system when a user chooses it. Ace Pro itself does not upload the video. Imported copies are separate from Photos. Keep originals: app deletion removes the library, and no recovery/sync service is implemented.

## Review position

This is a local experience implementation, **not a claim of App Store readiness or guaranteed approval**. A random video analysis demo cannot be marketed as an AI coach that actually measures performance. Keep simulation disclosures visible in product, screenshots, description and review notes. Position any public release as a useful private video journal and coaching-practice tool; reviewers assess completeness and minimum functionality independently.

Apple requires accurate descriptions, a complete working app, a privacy policy, and an in-app deletion path when account creation is offered. Optional guest access avoids blocking local video features behind an unnecessary account. Current accounts are explicitly local, and guest access is not protected by the demonstration login.

Sources checked for this implementation:
- https://developer.apple.com/app-store/review/guidelines/
- https://developer.apple.com/support/offering-account-deletion-in-your-app/
- https://developer.apple.com/documentation/technotes/tn3183-adding-required-reason-api-entries-to-your-privacy-manifest
- https://vercel.com/docs/functions/runtimes/node-js

## Before submission, in the publishing phase

1. Install current Xcode and required iOS SDK, build on Simulator, and test real iPhones, large videos, low storage, cancellation, backgrounding, offline API failures, accessibility and deletion.
2. Set Apple Developer team/bundle ownership and production signing; archive and validate.
3. Deploy the metadata API to Vercel; configure its HTTPS address as the release default and remove the developer URL field. Decide host retention/abuse settings and reconcile App Privacy disclosures with those settings.
4. Decide whether to retain the optional device-profile demo or simplify to a guest-only private journal. Real cross-device authentication would require scope beyond the single insights endpoint.
5. Publish final owner-specific privacy and support pages and link them inside the native app. The in-app privacy explanation is implemented; published legal/contact details are not yet supplied.
6. Validate the privacy manifest and app icon in the actual archive; confirm required-reason API usage against the final binary and SDK.
7. Prepare accurate screenshots, description, age rating and review instructions emphasizing random coaching examples and no video analysis. Never hide demo behavior from reviewers or users.

No cloud deployment, signing, App Store Connect changes or submission was performed in this implementation phase.

Tutorial references verified during implementation:
- Split-step timing, Essential Tennis: https://www.youtube.com/watch?v=jtWMP75377k
- Consistent second serve, Tom Avery Tennis: https://www.youtube.com/watch?v=aGwJlCrwZ90

Other technique links open labeled YouTube search results rather than inventing a specific video URL. External videos are linked, never downloaded or embedded automatically.
