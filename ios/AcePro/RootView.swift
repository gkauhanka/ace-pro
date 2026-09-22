import SwiftUI
import AVKit
import PhotosUI

private func initialRootTab() -> Int {
#if DEBUG
    Int(ProcessInfo.processInfo.environment["ACEPRO_SCREENSHOT_TAB"] ?? "") ?? 0
#else
    0
#endif
}

struct RootView: View {
    @EnvironmentObject private var store: PlayerStore
    @State private var tab = initialRootTab()
    @State private var importing = false

    var body: some View {
        TabView(selection: $tab) {
            NavigationStack { PlayerHome(importing: $importing) }
                .tabItem { Label("Today", systemImage: "sun.max") }.tag(0)
            NavigationStack { VideoLibrary(importing: $importing) }
                .tabItem { Label("Library", systemImage: "play.rectangle.on.rectangle") }.tag(1)
            NavigationStack { SessionJournal() }
                .tabItem { Label("Journal", systemImage: "note.text") }.tag(2)
            NavigationStack { AppSettings() }
                .tabItem { Label("Settings", systemImage: "gearshape") }.tag(3)
        }
        .sheet(isPresented: $importing) { ImportSessionView() }
        .tint(AceTheme.forest)
        .alert(
            "Something needs attention",
            isPresented: Binding(get: { store.error != nil }, set: { if !$0 { store.error = nil } })
        ) {
            Button("OK") { store.error = nil }
        } message: {
            Text(store.error ?? "")
        }
    }
}

struct CourtArtwork: View {
    var body: some View {
        GeometryReader { geometry in
            let width = geometry.size.width
            let height = geometry.size.height
            Path { path in
                path.addRect(CGRect(x: width * 0.12, y: height * 0.12, width: width * 0.76, height: height * 0.76))
                path.move(to: CGPoint(x: width * 0.22, y: height * 0.12)); path.addLine(to: CGPoint(x: width * 0.22, y: height * 0.88))
                path.move(to: CGPoint(x: width * 0.78, y: height * 0.12)); path.addLine(to: CGPoint(x: width * 0.78, y: height * 0.88))
                for y in [0.32, 0.68] {
                    path.move(to: CGPoint(x: width * 0.22, y: height * y)); path.addLine(to: CGPoint(x: width * 0.78, y: height * y))
                }
                path.move(to: CGPoint(x: width * 0.5, y: height * 0.32)); path.addLine(to: CGPoint(x: width * 0.5, y: height * 0.68))
                path.move(to: CGPoint(x: width * 0.08, y: height * 0.5)); path.addLine(to: CGPoint(x: width * 0.92, y: height * 0.5))
            }
            .stroke(.white.opacity(0.4), lineWidth: 1.5)
            Circle().fill(AceTheme.lime).frame(width: 22, height: 22).position(x: width * 0.65, y: height * 0.32)
        }
        .background(AceTheme.forest)
        .accessibilityHidden(true)
    }
}

struct PrimaryAction: ViewModifier {
    func body(content: Content) -> some View {
        content.font(.headline).frame(maxWidth: .infinity).padding(17).foregroundStyle(.white)
            .background(AceTheme.forest, in: RoundedRectangle(cornerRadius: 17))
    }
}

struct PlayerHome: View {
    @EnvironmentObject private var store: PlayerStore
    @Binding var importing: Bool

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 23) {
                HStack {
                    Text("YOUR PERSONAL COURTSIDE").font(.caption2.weight(.bold)).tracking(2)
                    Spacer()
                    Image(systemName: "tennisball.fill").foregroundStyle(AceTheme.forest)
                }
                Text("Review your game.\nKeep the evidence close.")
                    .font(.system(size: 37, weight: .bold, design: .rounded)).tracking(-1)
                ZStack(alignment: .bottomLeading) {
                    CourtArtwork().frame(height: 225)
                    LinearGradient(colors: [.clear, AceTheme.forest], startPoint: .top, endPoint: .bottom)
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Private video review.\nMeasured on your iPhone.").font(.title2.bold())
                        Text("Inspect motion and poses, then record what you notice.").font(.subheadline)
                    }
                    .foregroundStyle(.white).padding(22)
                }
                .clipShape(RoundedRectangle(cornerRadius: 25))
                Button { importing = true } label: { Label("Add a tennis video", systemImage: "plus.circle.fill") }
                    .modifier(PrimaryAction())
                Label("Videos and analysis stay on this device.", systemImage: "lock.shield")
                    .font(.caption).foregroundStyle(AceTheme.muted)
                Text("Latest session").font(.title3.bold())
                if let session = store.sessions.first {
                    NavigationLink { SessionReviewView(sessionID: session.id) } label: { SessionRow(session: session) }
                        .buttonStyle(.plain)
                } else {
                    Card {
                        VStack(alignment: .leading, spacing: 12) {
                            Label("Every improvement starts with a replay", systemImage: "figure.tennis").font(.headline)
                            Text("Add a match or practice video to begin your private library.").foregroundStyle(AceTheme.muted)
                        }
                    }
                }
            }
            .padding(22)
        }
        .background(AceTheme.cream)
        .navigationTitle("Ace Pro")
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct SessionRow: View {
    let session: LocalSession

    var body: some View {
        Card {
            HStack(spacing: 14) {
                LocalVideoThumbnail(session: session)
                VStack(alignment: .leading, spacing: 6) {
                    Text(session.title).font(.headline)
                    Text("\(session.type) · \(session.date.matchDate) · \(videoTime(session.duration))")
                        .font(.caption).foregroundStyle(AceTheme.muted)
                    Text(session.focus).font(.caption2.bold()).foregroundStyle(AceTheme.forest)
                }
                Spacer()
                Image(systemName: "chevron.right").font(.caption)
            }
        }
    }
}

struct LocalVideoThumbnail: View {
    @EnvironmentObject private var store: PlayerStore
    let session: LocalSession
    @State private var thumbnail: CGImage?

    var body: some View {
        ZStack {
            AceTheme.cream
            if let thumbnail {
                Image(decorative: thumbnail, scale: 1).resizable().scaledToFill()
            } else {
                Image(systemName: session.type == "Match" ? "tennisball" : "figure.tennis")
                    .font(.title2).foregroundStyle(AceTheme.forest)
            }
        }
        .frame(width: 58, height: 72).clipShape(RoundedRectangle(cornerRadius: 12)).accessibilityHidden(true)
        .task(id: session.id) {
            let generator = AVAssetImageGenerator(asset: AVURLAsset(url: store.url(for: session)))
            generator.appliesPreferredTrackTransform = true
            generator.maximumSize = CGSize(width: 180, height: 220)
            do {
                let frame = try await generator.image(at: .zero)
                try Task.checkCancellation()
                thumbnail = frame.image
            } catch { }
        }
    }
}

struct VideoLibrary: View {
    @EnvironmentObject private var store: PlayerStore
    @Binding var importing: Bool
    @State private var query = ""
    @State private var filter = "All"

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                Picker("Session type", selection: $filter) {
                    ForEach(["All", "Match", "Practice"], id: \.self) { Text($0) }
                }
                .pickerStyle(.segmented)
                let filtered = store.sessions.filter {
                    (filter == "All" || $0.type == filter) && (query.isEmpty || $0.title.localizedCaseInsensitiveContains(query))
                }
                if filtered.isEmpty {
                    ContentUnavailableView(
                        "Your courtside collection",
                        systemImage: "video.badge.plus",
                        description: Text(query.isEmpty ? "Add a video to start your local library." : "No sessions match your search.")
                    )
                }
                ForEach(filtered) { session in
                    NavigationLink { SessionReviewView(sessionID: session.id) } label: { SessionRow(session: session) }
                        .buttonStyle(.plain)
                }
                Button { importing = true } label: { Label("Add video", systemImage: "plus") }.modifier(PrimaryAction())
            }
            .padding(20)
        }
        .background(AceTheme.cream)
        .navigationTitle("Your library")
        .searchable(text: $query, prompt: "Find a session")
    }
}

struct ImportSessionView: View {
    @EnvironmentObject private var store: PlayerStore
    @Environment(\.dismiss) private var dismiss
    @State private var item: PhotosPickerItem?
    @State private var title = ""
    @State private var type = "Practice"
    @State private var focus = "All-round"
    @State private var source: URL?
    @State private var busy = false
    @State private var message = ""
    @State private var task: Task<Void, Never>?
    @State private var files = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 23) {
                    Text("Bring a session\ninto focus.").font(.largeTitle.bold())
                    Label("Your selected video is copied into protected app storage and never uploaded.", systemImage: "lock.shield")
                        .font(.subheadline).foregroundStyle(AceTheme.muted)
                    if busy { ProgressView("Saving your video…") }
                    PhotosPicker(selection: $item, matching: .videos) {
                        Label(source == nil ? "Select from Photos" : "Video selected · change", systemImage: "photo.on.rectangle")
                    }
                    .modifier(PrimaryAction()).disabled(busy)
                    Button("Choose from Files") { files = true }.frame(maxWidth: .infinity).disabled(busy)
                    TextField("Session name", text: $title).textFieldStyle(.roundedBorder)
                    Picker("Session", selection: $type) {
                        Text("Practice").tag("Practice"); Text("Match").tag("Match")
                    }
                    .pickerStyle(.segmented)
                    Picker("Review focus", selection: $focus) {
                        ForEach(["All-round", "Footwork", "Technique", "Serve", "Tactics"], id: \.self) { Text($0) }
                    }
                    if !message.isEmpty { Text(message).foregroundStyle(.red) }
                    Button("Save session") { saveSession() }.modifier(PrimaryAction())
                        .disabled(source == nil || busy).opacity(source == nil || busy ? 0.5 : 1)
                }
                .padding(24)
            }
            .background(AceTheme.cream)
            .navigationTitle("Add session")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .cancellationAction) { Button("Cancel") { task?.cancel(); dismiss() } } }
            .onChange(of: item) { _, newItem in
                task = Task {
                    busy = true
                    defer { busy = false }
                    do {
                        guard let movie = try await newItem?.loadTransferable(type: PickedMovie.self) else { return }
                        if let source { try? FileManager.default.removeItem(at: source) }
                        source = movie.url
                        message = ""
                    } catch { message = error.localizedDescription }
                }
            }
            .fileImporter(isPresented: $files, allowedContentTypes: [.movie]) { result in
                do {
                    let url = try result.get()
                    let access = url.startAccessingSecurityScopedResource()
                    defer { if access { url.stopAccessingSecurityScopedResource() } }
                    let destination = FileManager.default.temporaryDirectory
                        .appendingPathComponent(UUID().uuidString).appendingPathExtension(url.pathExtension)
                    try FileManager.default.copyItem(at: url, to: destination)
                    if let source { try? FileManager.default.removeItem(at: source) }
                    source = destination
                    message = ""
                } catch { message = error.localizedDescription }
            }
            .onDisappear {
                task?.cancel()
                if let source { try? FileManager.default.removeItem(at: source) }
            }
        }
    }

    private func saveSession() {
        guard let source else { return }
        task = Task {
            busy = true
            defer { busy = false }
            do {
                _ = try await store.importVideo(source, title: title, type: type, focus: focus)
                dismiss()
            } catch is CancellationError { } catch { message = error.localizedDescription }
        }
    }
}

struct SessionReviewView: View {
    @EnvironmentObject private var store: PlayerStore
    @Environment(\.dismiss) private var dismiss
    let sessionID: UUID
    @State private var deleting = false
    @State private var observation = ""
    @State private var saved = false

    private var session: LocalSession? { store.sessions.first { $0.id == sessionID } }

    var body: some View {
        ScrollView {
            if let session {
                VStack(alignment: .leading, spacing: 20) {
                    Text("\(session.type.uppercased()) · \(session.date.matchDate) · \(videoTime(session.duration))")
                        .font(.caption.bold()).foregroundStyle(AceTheme.muted)
                    Text(session.title).font(.largeTitle.bold())
                    Text("Review focus: \(session.focus)").font(.headline).foregroundStyle(AceTheme.forest)
                    NavigationLink { LocalPlayback(session: session, seconds: 0) } label: {
                        Label("Play your video", systemImage: "play.circle.fill")
                    }
                    .modifier(PrimaryAction())
                    NavigationLink { VideoAnalysisView(session: session) } label: {
                        Card {
                            HStack {
                                VStack(alignment: .leading, spacing: 5) {
                                    Label("On-device video analysis", systemImage: "waveform.path.ecg.rectangle").font(.headline)
                                    Text("Measure motion, body poses, hand poses, and scene movement without uploading footage.")
                                        .font(.caption).foregroundStyle(AceTheme.muted)
                                }
                                Spacer()
                                Image(systemName: "chevron.right").font(.caption)
                            }
                        }
                    }
                    .buttonStyle(.plain)
                    Text("Your observation").font(.title2.bold())
                    Text("Record what you notice while reviewing the video. Ace Pro does not diagnose technique or identify strokes.")
                        .font(.caption).foregroundStyle(AceTheme.muted)
                    TextEditor(text: $observation)
                        .frame(minHeight: 130).padding(8)
                        .background(.white, in: RoundedRectangle(cornerRadius: 14))
                        .overlay(RoundedRectangle(cornerRadius: 14).stroke(AceTheme.sand))
                        .accessibilityLabel("Session observation")
                    Button(saved ? "Saved" : "Save observation") {
                        do {
                            try store.updateObservation(observation, sessionID: sessionID)
                            saved = true
                        } catch { store.error = error.localizedDescription }
                    }
                    .modifier(PrimaryAction())
                }
                .padding(22)
            }
        }
        .background(AceTheme.cream)
        .navigationTitle("Session review")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button(role: .destructive) { deleting = true } label: { Image(systemName: "trash") }
                    .accessibilityLabel("Delete session")
            }
        }
        .confirmationDialog(
            "Delete this session and its local video copy? Your original is unchanged.",
            isPresented: $deleting,
            titleVisibility: .visible
        ) {
            Button("Delete session", role: .destructive) {
                do { try store.remove(sessionID); dismiss() }
                catch { store.error = error.localizedDescription }
            }
        }
        .onAppear { observation = session?.notes["session"] ?? "" }
        .onChange(of: observation) { _, _ in saved = false }
    }
}

struct LocalPlayback: View {
    @EnvironmentObject private var store: PlayerStore
    let session: LocalSession
    let startSeconds: Double
    let endSeconds: Double?
    let autoplay: Bool
    @State private var player: AVPlayer?
    @State private var boundaryObserver: Any?

    init(session: LocalSession, seconds: Double) {
        self.session = session
        startSeconds = seconds
        endSeconds = nil
        autoplay = true
    }

    init(session: LocalSession, startSeconds: Double, endSeconds: Double?, autoplay: Bool = true) {
        self.session = session
        self.startSeconds = startSeconds
        self.endSeconds = endSeconds
        self.autoplay = autoplay
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            if let player { VideoPlayer(player: player).frame(minHeight: 230, maxHeight: 370) }
            Text(session.title).font(.title2.bold())
            if let endSeconds {
                Text("Clip \(videoTime(startSeconds)) – \(videoTime(endSeconds))").font(.headline).monospacedDigit()
                Text("Playback pauses automatically at the end of the detected motion candidate.").foregroundStyle(AceTheme.muted)
            } else if autoplay {
                Text("Review from \(videoTime(startSeconds))").font(.headline)
            } else {
                Text("Measured frame at \(videoTime(startSeconds))").font(.headline).monospacedDigit()
                Text("Playback is paused on the analyzed frame.").foregroundStyle(AceTheme.muted)
            }
            Spacer()
        }
        .padding()
        .navigationTitle("Video review")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            let url = store.url(for: session)
            guard FileManager.default.fileExists(atPath: url.path) else {
                store.error = "This local video is missing. Import the original again."
                return
            }
            let newPlayer = AVPlayer(url: url)
            player = newPlayer
            if let endSeconds, endSeconds > startSeconds {
                boundaryObserver = newPlayer.addBoundaryTimeObserver(
                    forTimes: [NSValue(time: CMTime(seconds: endSeconds, preferredTimescale: 600))], queue: .main
                ) { [weak newPlayer] in newPlayer?.pause() }
            }
            newPlayer.seek(
                to: CMTime(seconds: startSeconds, preferredTimescale: 600), toleranceBefore: .zero, toleranceAfter: .zero
            ) { completed in
                guard completed else { return }
                if autoplay { newPlayer.play() } else { newPlayer.pause() }
            }
        }
        .onDisappear {
            player?.pause()
            if let boundaryObserver, let player { player.removeTimeObserver(boundaryObserver) }
            boundaryObserver = nil
            player = nil
        }
    }
}

struct SessionJournal: View {
    @EnvironmentObject private var store: PlayerStore

    private var entries: [LocalSession] {
        store.sessions.filter { !($0.notes["session"] ?? "").trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                Text("Your observations").font(.largeTitle.bold())
                Text("Notes you made while reviewing your own sessions.").foregroundStyle(AceTheme.muted)
                if entries.isEmpty {
                    ContentUnavailableView(
                        "No observations yet", systemImage: "note.text",
                        description: Text("Open a session, review the video, and save what you notice.")
                    )
                }
                ForEach(entries) { session in
                    NavigationLink { SessionReviewView(sessionID: session.id) } label: {
                        Card {
                            VStack(alignment: .leading, spacing: 8) {
                                Text(session.title).font(.headline)
                                Text(session.notes["session"] ?? "").lineLimit(4).foregroundStyle(AceTheme.muted)
                                Text(session.date.matchDate).font(.caption).foregroundStyle(AceTheme.forest)
                            }
                        }
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(22)
        }
        .background(AceTheme.cream)
        .navigationTitle("Journal")
    }
}

struct AppSettings: View {
    @EnvironmentObject private var store: PlayerStore
    @State private var deleting = false

    var body: some View {
        Form {
            Section("Privacy") {
                NavigationLink("Privacy policy") { PrivacyPolicyView() }
                Link("Read privacy policy online", destination: URL(string: "https://github.com/gkauhanka/ace-pro/blob/main/docs/privacy-policy.md")!)
                Label("No account or sign-in", systemImage: "person.crop.circle.badge.checkmark")
                Label("No analytics, tracking, ads, or video uploads", systemImage: "lock.shield")
                Text("Imported videos, analysis measurements, and observations remain in this app on this device. The app has no server connection.")
            }
            Section("Support") { NavigationLink("Help and contact") { SupportView() } }
            Section("Your data") {
                Text("Deleting a session removes Ace Pro’s protected local copy. Your original in Photos or Files is unchanged.")
                Button("Delete all app data", role: .destructive) { deleting = true }
            }
            Section("About") {
                Text("Ace Pro 1.0")
                Text("Apple Vision measurements can suggest moments to review, but do not identify a tennis ball, classify strokes, diagnose technique, or replace a coach.")
                Text("Adapt practice to your ability and stop if you feel pain.")
            }
        }
        .navigationTitle("Settings")
        .confirmationDialog(
            "Delete every imported video copy and observation from Ace Pro? Originals remain unchanged.",
            isPresented: $deleting,
            titleVisibility: .visible
        ) {
            Button("Delete all app data", role: .destructive) {
                do { try store.deleteAll() }
                catch { store.error = error.localizedDescription }
            }
        }
    }
}

struct PrivacyPolicyView: View {
    var body: some View {
        List {
            Section("Summary") {
                Text("Ace Pro stores videos you choose, on-device analysis measurements, and written observations locally on this device. Ace Pro does not transmit this information to a server.")
            }
            Section("Data stored on your device") {
                Text("Imported video copies are kept in protected app storage and excluded from device backups. Session titles, dates, review focus, and observations are stored with the app. Analysis measurements remain in memory while the analysis screen is open.")
            }
            Section("Data collection") {
                Text("Ace Pro does not create an account, collect personal information, run third-party analytics, display advertising, track you, or sell data.")
            }
            Section("Your controls") {
                Text("Delete individual sessions from their review screen or delete all app data in Settings. Removing the app also removes its local data. Original source videos are not changed.")
            }
            Section("Apple services") {
                Text("When available, Apple Intelligence can create a description from numeric analysis measurements on your device. Ace Pro does not send the original video to a language-model provider.")
            }
        }
        .navigationTitle("Privacy policy")
    }
}

struct SupportView: View {
    var body: some View {
        List {
            Section("Using Ace Pro") {
                Text("Add a video from Photos or Files, open the saved session, and choose On-device video analysis. Stable landscape footage with the full court visible generally produces the clearest measurements.")
            }
            Section("Important limitations") {
                Text("Motion candidates are generic trajectories, not confirmed tennis balls. Pose results identify visible body landmarks but do not assess whether technique is correct.")
            }
            Section("Troubleshooting") {
                Text("If analysis finds no results, try a brighter, steadier clip with the player and ball visible. Keep the app open while analysis runs.")
                Text("If a saved video is missing, import the original again. Ace Pro does not synchronize or recover deleted videos.")
            }
            Section("Contact") {
                Link("Read support guide online", destination: URL(string: "https://github.com/gkauhanka/ace-pro/blob/main/docs/support.md")!)
                Link("Contact support on GitHub", destination: URL(string: "https://github.com/gkauhanka/ace-pro/issues")!)
                Text("Support requests on GitHub are public. Do not include personal information or private video.")
            }
        }
        .navigationTitle("Help and contact")
    }
}
