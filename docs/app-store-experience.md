# Ace Pro release boundary

## Public product

The App Store build is a private, on-device tennis video review and journaling application. It imports a user-selected local video, runs supported Apple Vision measurements on the iPhone, links measurements to reviewable frames or time ranges, and lets the user record personal observations.

It does not claim to identify tennis balls, classify strokes, score technique, or provide evidence-backed coaching conclusions. Those capabilities remain research work until separately trained models pass the evaluation gates documented in `docs/video-analysis`.

The randomized `insights-api` remains a browser prototype only. It is not called by, configured in, or presented as functionality of the App Store build.

## Release data boundary

| Information | Storage | Network |
| --- | --- | --- |
| Imported video | Protected app-private file, excluded from backup | Never sent by Ace Pro |
| Session title, type, focus, and date | Local app JSON | Never sent |
| Apple Vision measurements | Processed on device; current screen state only | Never sent |
| User observations | Local app JSON | Never sent |
| Apple Intelligence description | Generated on device on eligible systems | Not sent by Ace Pro |

Ace Pro has no account, analytics SDK, advertising SDK, tracking code, or production backend connection. The system Photos picker may download an iCloud-backed original after the user selects it; that is an Apple service interaction rather than an Ace Pro upload.

## User-facing limitations

The release UI states that motion candidates are generic trajectories, pose measurements are not technique diagnoses, and Apple Intelligence availability varies by device. The UI avoids simulated percentages, fake timestamps, and claims unsupported by measured results.

## Public documents

- Privacy policy: https://github.com/gkauhanka/ace-pro/blob/main/docs/privacy-policy.md
- Support: https://github.com/gkauhanka/ace-pro/blob/main/docs/support.md
- Support requests: https://github.com/gkauhanka/ace-pro/issues

## Owner-controlled release work

The repository can prepare and validate the application, but the owner must provide a paid Apple Developer Program team, accept current Apple agreements, create the App Store Connect record, complete tax/banking information when applicable, upload screenshots, answer age-rating and privacy questions, and submit the signed archive.

Apple approval is never guaranteed. Review guidance should be checked again immediately before submission:

- https://developer.apple.com/app-store/review/guidelines/
- https://developer.apple.com/help/app-store-connect/manage-app-information/manage-app-privacy
- https://developer.apple.com/news/upcoming-requirements/
