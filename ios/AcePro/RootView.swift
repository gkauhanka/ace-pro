import SwiftUI
import AVKit
import PhotosUI

struct RootView: View {
    @EnvironmentObject var store: PlayerStore
    @State private var tab = 0
    @State private var importing = false
    var body: some View {
        Group {
            if store.unlocked || store.guest {
                TabView(selection: $tab) {
                    NavigationStack { PlayerHome(importing: $importing) }.tabItem { Label("Today", systemImage: "sun.max") }.tag(0)
                    NavigationStack { VideoLibrary(importing: $importing) }.tabItem { Label("Library", systemImage: "play.rectangle.on.rectangle") }.tag(1)
                    NavigationStack { PracticePlan() }.tabItem { Label("Improve", systemImage: "figure.tennis") }.tag(2)
                    NavigationStack { DeviceSettings() }.tabItem { Label("Profile", systemImage: "person.crop.circle") }.tag(3)
                }
                .sheet(isPresented: $importing) { ImportSessionView() }
            } else { WelcomePlayer() }
        }
        .tint(AceTheme.forest)
        .alert("Something needs attention", isPresented: Binding(get: { store.error != nil }, set: { if !$0 { store.error = nil } })) { Button("OK") { store.error = nil } } message: { Text(store.error ?? "") }
    }
}

struct CourtArtwork: View {
    var body: some View {
        GeometryReader { geometry in
            let w = geometry.size.width; let h = geometry.size.height
            Path { p in
                p.addRect(CGRect(x: w * 0.12, y: h * 0.12, width: w * 0.76, height: h * 0.76))
                p.move(to: CGPoint(x: w * 0.22, y: h * 0.12)); p.addLine(to: CGPoint(x: w * 0.22, y: h * 0.88))
                p.move(to: CGPoint(x: w * 0.78, y: h * 0.12)); p.addLine(to: CGPoint(x: w * 0.78, y: h * 0.88))
                for y in [0.32, 0.68] { p.move(to: CGPoint(x: w * 0.22, y: h * y)); p.addLine(to: CGPoint(x: w * 0.78, y: h * y)) }
                p.move(to: CGPoint(x: w * 0.5, y: h * 0.32)); p.addLine(to: CGPoint(x: w * 0.5, y: h * 0.68))
                p.move(to: CGPoint(x: w * 0.08, y: h * 0.5)); p.addLine(to: CGPoint(x: w * 0.92, y: h * 0.5))
            }.stroke(.white.opacity(0.4), lineWidth: 1.5)
            Circle().fill(AceTheme.lime).frame(width: 22, height: 22).position(x: w * 0.65, y: h * 0.32)
        }.background(AceTheme.forest).accessibilityHidden(true)
    }
}
struct PrimaryAction: ViewModifier {
    func body(content: Content) -> some View { content.font(.headline).frame(maxWidth: .infinity).padding(17).foregroundStyle(.white).background(AceTheme.forest, in: RoundedRectangle(cornerRadius: 17)) }
}
struct SimulationNotice: View {
    var body: some View { Label("Simulated insights · your video stays on this device", systemImage: "lock.shield").font(.caption).foregroundStyle(AceTheme.muted).fixedSize(horizontal: false, vertical: true) }
}
struct WelcomePlayer: View {
    @EnvironmentObject var store: PlayerStore
    @State private var auth: String?
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 25) {
                HStack { Image(systemName: "tennisball.fill"); Text("ACE PRO").tracking(4).fontWeight(.heavy) }.foregroundStyle(AceTheme.forest)
                CourtArtwork().frame(height: 260).clipShape(RoundedRectangle(cornerRadius: 28))
                Text("Your game.\nA clearer perspective.").font(.system(size: 38, weight: .bold, design: .rounded)).tracking(-1.5)
                Text("Keep your tennis videos close. Review the moments. Build a better next session.").font(.title3).foregroundStyle(AceTheme.muted)
                VStack(spacing: 12) {
                    Button("Create a device account") { auth = "Create account" }.modifier(PrimaryAction())
                    Button("Already have an account? Log in") { auth = "Log in" }.font(.subheadline.weight(.semibold))
                    Button("Explore without an account") { store.guest = true }.padding(.top, 5)
                }
                Text("This experience uses random coaching examples, not video analysis. Accounts and videos are stored only on this device; there is no cloud login or recovery.").font(.caption).foregroundStyle(AceTheme.muted)
            }.padding(25)
        }.background(AceTheme.cream)
        .sheet(isPresented: Binding(get: { auth != nil }, set: { if !$0 { auth = nil } })) { DeviceAuth(isCreating: auth == "Create account") }
    }
}
struct DeviceAuth: View {
    @EnvironmentObject var store: PlayerStore
    @Environment(\.dismiss) var dismiss
    let isCreating: Bool
    @State private var name = ""; @State private var email = ""; @State private var password = ""; @State private var message = ""
    var body: some View {
        NavigationStack {
            Form {
                Section {
                    if isCreating { TextField("Your name", text: $name).textContentType(.givenName) }
                    TextField("Email", text: $email).keyboardType(.emailAddress).textContentType(.username).textInputAutocapitalization(.never).autocorrectionDisabled()
                    SecureField("Password · 8+ characters", text: $password).textContentType(isCreating ? .newPassword : .password)
                } footer: { Text("Local device account. Your email is not verified or sent anywhere. Passwords are secured in this device’s Keychain. No cloud sync or password recovery.") }
                if !message.isEmpty { Text(message).foregroundStyle(.red) }
                Button(isCreating ? "Create account" : "Log in") {
                    do { if isCreating { try store.createProfile(name: name, email: email, password: password) } else { try store.login(email: email, password: password) }; dismiss() }
                    catch { message = error.localizedDescription }
                }
                if !isCreating { Text("Forgot your password? You can continue as a guest from the welcome screen. Resetting the device account in Profile deletes its local library.").font(.caption) }
            }.navigationTitle(isCreating ? "Make it yours" : "Welcome back")
            .toolbar { ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } } }
        }
    }
}
struct PlayerHome: View {
    @EnvironmentObject var store: PlayerStore
    @Binding var importing: Bool
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 23) {
                HStack { Text("YOUR PERSONAL COURTSIDE").font(.caption2.weight(.bold)).tracking(2); Spacer(); Image(systemName: "tennisball.fill").foregroundStyle(AceTheme.forest) }
                Text("Let’s build\nyour next best.").font(.system(size: 37, weight: .bold, design: .rounded)).tracking(-1)
                ZStack(alignment: .bottomLeading) {
                    CourtArtwork().frame(height: 225)
                    LinearGradient(colors: [.clear, AceTheme.forest], startPoint: .top, endPoint: .bottom)
                    VStack(alignment: .leading, spacing: 8) { Text("A little review.\nA lot to play for.").font(.title2.bold()); Text("Bring your last session into focus.").font(.subheadline) }.foregroundStyle(.white).padding(22)
                }.clipShape(RoundedRectangle(cornerRadius: 25))
                Button { importing = true } label: { Label("Add a tennis video", systemImage: "plus.circle.fill") }.modifier(PrimaryAction())
                SimulationNotice()
                HStack(spacing: 12) {
                    summary("\(store.sessions.count)", "Local videos", "video")
                    summary("\(store.savedDrills.count)", "Saved drills", "target")
                }
                HStack { Text("Your latest session").font(.title3.bold()); Spacer() }
                if let session = store.sessions.first {
                    NavigationLink { SessionReportView(sessionID: session.id) } label: { SessionRow(session: session) }.buttonStyle(.plain)
                } else {
                    Card { VStack(alignment: .leading, spacing: 12) { Label("Every improvement starts somewhere", systemImage: "figure.tennis").font(.headline); Text("Add a match or practice video. Keep your footage private and explore a sample coaching report.").foregroundStyle(AceTheme.muted) } }
                }
                Card { VStack(alignment: .leading, spacing: 10) { Text("01  REVIEW   →   02  PRACTICE   →   03  REPEAT").font(.caption2.bold()).foregroundStyle(AceTheme.forest); Text("One focus is enough.").font(.headline); Text("Pick a single cue, take it to the court, and use your own notes to track what changes.").font(.subheadline).foregroundStyle(AceTheme.muted) } }
            }.padding(22)
        }.background(AceTheme.cream).navigationTitle("Hi, \(store.guest ? "player" : store.profile?.name ?? "player")").navigationBarTitleDisplayMode(.inline)
    }
    func summary(_ value: String, _ label: String, _ icon: String) -> some View { Card { VStack(alignment: .leading, spacing: 8) { Image(systemName: icon).foregroundStyle(AceTheme.forest); Text(value).font(.title.bold()); Text(label).font(.caption).foregroundStyle(AceTheme.muted) } } }
}
struct SessionRow: View {
    let session: LocalSession
    var body: some View { Card { HStack(spacing: 14) { LocalVideoThumbnail(session: session); VStack(alignment: .leading, spacing: 6) { Text(session.title).font(.headline); Text("\(session.type) · \(session.date.matchDate) · \(videoTime(session.duration))").font(.caption).foregroundStyle(AceTheme.muted); Text(session.report == nil ? "Ready for sample insights" : "Sample report ready").font(.caption2.bold()).foregroundStyle(AceTheme.forest) }; Spacer(); Image(systemName: "chevron.right").font(.caption) } } }
}
struct LocalVideoThumbnail: View {
    @EnvironmentObject var store: PlayerStore
    let session: LocalSession
    @State private var thumbnail: CGImage?
    var body: some View {
        ZStack {
            AceTheme.cream
            if let thumbnail {
                Image(decorative: thumbnail, scale: 1).resizable().scaledToFill()
            } else {
                Image(systemName: session.type == "Match" ? "tennisball" : "figure.tennis").font(.title2).foregroundStyle(AceTheme.forest)
            }
        }
        .frame(width: 58, height: 72).clipShape(RoundedRectangle(cornerRadius: 12)).accessibilityHidden(true)
        .task(id: session.id) {
            let generator = AVAssetImageGenerator(asset: AVURLAsset(url: store.url(for: session)))
            generator.appliesPreferredTrackTransform = true
            generator.maximumSize = CGSize(width: 180, height: 220)
            do { let frame = try await generator.image(at: .zero); try Task.checkCancellation(); thumbnail = frame.image }
            catch { /* Keep the local placeholder when a thumbnail cannot be decoded. */ }
        }
    }
}
struct VideoLibrary: View {
    @EnvironmentObject var store: PlayerStore
    @Binding var importing: Bool
    @State private var query = ""; @State private var filter = "All"
    var body: some View {
        ScrollView { VStack(spacing: 16) {
            Picker("Session type", selection: $filter) { ForEach(["All", "Match", "Practice"], id: \.self) { Text($0) } }.pickerStyle(.segmented)
            SimulationNotice().frame(maxWidth: .infinity, alignment: .leading)
            let filtered = store.sessions.filter { (filter == "All" || $0.type == filter) && (query.isEmpty || $0.title.localizedCaseInsensitiveContains(query)) }
            if filtered.isEmpty { ContentUnavailableView("Your court-side collection", systemImage: "video.badge.plus", description: Text(query.isEmpty ? "Add a video to start your local library." : "No sessions match your search.")) }
            ForEach(filtered) { session in NavigationLink { SessionReportView(sessionID: session.id) } label: { SessionRow(session: session) }.buttonStyle(.plain) }
            Button { importing = true } label: { Label("Add video", systemImage: "plus") }.modifier(PrimaryAction())
        }.padding(20) }.background(AceTheme.cream).navigationTitle("Your library").searchable(text: $query, prompt: "Find a session")
    }
}
struct ImportSessionView: View {
    @EnvironmentObject var store: PlayerStore
    @Environment(\.dismiss) var dismiss
    @State private var item: PhotosPickerItem?; @State private var title = ""; @State private var type = "Practice"; @State private var focus = "All-round"
    @State private var source: URL?; @State private var sessionID: UUID?; @State private var busy = false; @State private var stage = ""; @State private var message = ""; @State private var progress = 0.0
    @State private var task: Task<Void, Never>?; @State private var files = false
    var body: some View {
        NavigationStack {
            ScrollView { VStack(alignment: .leading, spacing: 23) {
                Text("Your next breakthrough\nstarts with a replay.").font(.largeTitle.bold())
                SimulationNotice()
                Text("Choose a match or practice video. We copy it into your private on-device library. Only duration, session type and focus go to the insights service.").foregroundStyle(AceTheme.muted)
                if busy { Card { VStack(alignment: .leading, spacing: 16) { ProgressView(value: progress).tint(AceTheme.forest); Text(stage).font(.headline); Text("Simulated processing · no video upload").font(.caption).foregroundStyle(AceTheme.muted) } } }
                if !busy && sessionID == nil {
                    PhotosPicker(selection: $item, matching: .videos) { Label(source == nil ? "Select from Photos" : "Video selected ✓ · change", systemImage: "photo.on.rectangle") }.modifier(PrimaryAction())
                    Button("Choose from Files") { files = true }.frame(maxWidth: .infinity)
                    TextField("Session name", text: $title).textFieldStyle(.roundedBorder)
                    Picker("Session", selection: $type) { Text("Practice").tag("Practice"); Text("Match").tag("Match") }.pickerStyle(.segmented)
                    Picker("Focus", selection: $focus) { ForEach(["All-round", "Footwork", "Technique", "Serve", "Tactics"], id: \.self) { Text($0) } }
                }
                if !message.isEmpty { Text(message).font(.subheadline).foregroundStyle(.red) }
                if !busy {
                    if let id = sessionID, store.sessions.first(where: { $0.id == id })?.report != nil {
                        Label("Your sample report is ready", systemImage: "checkmark.circle.fill").font(.title2.bold()).foregroundStyle(AceTheme.forest)
                        NavigationLink("Open report") { SessionReportView(sessionID: id) }.modifier(PrimaryAction())
                    } else {
                        Button(sessionID == nil ? "Save & generate sample insights" : "Retry insights") { run() }.modifier(PrimaryAction()).disabled(source == nil && sessionID == nil).opacity(source == nil && sessionID == nil ? 0.5 : 1)
                    }
                }
                Text("Example statistics and review points are randomly generated. They do not describe your actual technique or identify mistakes in your video.").font(.caption).foregroundStyle(AceTheme.muted)
            }.padding(24) }.background(AceTheme.cream).navigationTitle("Add session").navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .cancellationAction) { Button(busy ? "Cancel" : "Done") { task?.cancel(); dismiss() } } }
            .onChange(of: item) { _, newItem in
                task = Task { busy = true; stage = "Preparing your selection…"; defer { busy = false }
                    do { guard let movie = try await newItem?.loadTransferable(type: PickedMovie.self) else { return }; if let source { try? FileManager.default.removeItem(at: source) }; source = movie.url; message = "" } catch { message = error.localizedDescription }
                }
            }
            .fileImporter(isPresented: $files, allowedContentTypes: [.movie]) { result in
                do { let url = try result.get(); let access = url.startAccessingSecurityScopedResource(); defer { if access { url.stopAccessingSecurityScopedResource() } }; let destination = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString).appendingPathExtension(url.pathExtension); try FileManager.default.copyItem(at: url, to: destination); if let source { try? FileManager.default.removeItem(at: source) }; source = destination; message = "" } catch { message = error.localizedDescription }
            }
            .onDisappear { task?.cancel(); if let source { try? FileManager.default.removeItem(at: source) } }
        }
    }
    func run() {
        task = Task {
            busy = true; message = ""; progress = 0.1; defer { busy = false }
            do {
                if sessionID == nil, let source { stage = "Saving video on this device…"; sessionID = try await store.importVideo(source, title: title, type: type, focus: focus) }
                for (i, text) in ["Preparing session…", "Simulating movement review…", "Building coaching priorities…"].enumerated() { stage = text; progress = Double(i + 1) / 4; try await Task.sleep(for: .seconds(1)) }
                stage = "Getting sample insights…"; if let id = sessionID { try await store.analyze(id) }; progress = 1
            } catch is CancellationError { } catch { message = error.localizedDescription }
        }
    }
}
struct SessionReportView: View {
    @EnvironmentObject var store: PlayerStore
    @Environment(\.dismiss) var dismiss
    let sessionID: UUID
    @State private var deleting = false; @State private var busy = false; @State private var message = ""
    var session: LocalSession? { store.sessions.first { $0.id == sessionID } }
    var body: some View {
        ScrollView { if let session { VStack(alignment: .leading, spacing: 20) {
            Text("\(session.type.uppercased()) · \(session.date.matchDate) · \(videoTime(session.duration))").font(.caption.bold()).foregroundStyle(AceTheme.muted)
            Text(session.title).font(.largeTitle.bold())
            NavigationLink { LocalPlayback(session: session, seconds: 0) } label: { Label("Play your video", systemImage: "play.circle.fill") }.modifier(PrimaryAction())
            Card { VStack(alignment: .leading, spacing: 8) { Label("Sample coaching report", systemImage: "sparkles").font(.headline); Text(session.report?.disclosure ?? "Your video is saved locally. Generate a sample report to explore coaching ideas.").font(.caption).foregroundStyle(AceTheme.muted) } }
            if let report = session.report {
                Text("Three ideas for your next session").font(.title2.bold())
                ForEach(report.insights) { insight in NavigationLink { CoachingDetail(insight: insight, sessionID: session.id) } label: { Card { VStack(alignment: .leading, spacing: 12) {
                    HStack { PriorityBadge(priority: insight.priority); Spacer(); Text(insight.category).font(.caption) }
                    Text(insight.title).font(.title3.bold())
                    HStack(alignment: .firstTextBaseline) { Text("\(insight.value)\(insight.unit)").font(.system(size: 35, weight: .bold, design: .rounded)); Text(insight.metric).font(.caption).foregroundStyle(AceTheme.muted) }
                    Text("Example statistic · \(insight.moments.count) review points").font(.caption2).foregroundStyle(AceTheme.muted)
                    Label("Explore & practice", systemImage: "arrow.up.right").font(.subheadline.bold()).foregroundStyle(AceTheme.forest)
                } } }.buttonStyle(.plain) }
            } else {
                Button { Task { busy = true; defer { busy = false }; do { try await store.analyze(session.id) } catch { message = error.localizedDescription } } } label: { if busy { ProgressView() } else { Text("Generate sample insights") } }.modifier(PrimaryAction()).disabled(busy)
                if !message.isEmpty { Text(message).foregroundStyle(.red) }
            }
        }.padding(22) } }.background(AceTheme.cream).navigationTitle("Session review").navigationBarTitleDisplayMode(.inline)
        .toolbar { ToolbarItem(placement: .topBarTrailing) { Button(role: .destructive) { deleting = true } label: { Image(systemName: "trash") }.accessibilityLabel("Delete session") } }
        .confirmationDialog("Delete this session and its local video copy? Your original in Photos is unchanged.", isPresented: $deleting, titleVisibility: .visible) { Button("Delete session", role: .destructive) { do { try store.remove(sessionID); dismiss() } catch { store.error = error.localizedDescription } } }
    }
}
struct LocalPlayback: View {
    @EnvironmentObject var store: PlayerStore
    let session: LocalSession; let seconds: Double
    @State private var player: AVPlayer?
    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            if let player { VideoPlayer(player: player).frame(minHeight: 230, maxHeight: 370) }
            Text(session.title).font(.title2.bold())
            Text("Review from \(videoTime(seconds))").font(.headline)
            Text("This is an illustrative review point, not a detected mistake. Use the video controls to inspect your own technique.").foregroundStyle(AceTheme.muted)
            Spacer()
        }.padding().navigationTitle("On-device replay").navigationBarTitleDisplayMode(.inline)
        .onAppear {
            let url = store.url(for: session)
            guard FileManager.default.fileExists(atPath: url.path) else { store.error = "This local video is missing. Import the original again."; return }
            let p = AVPlayer(url: url); player = p; p.seek(to: CMTime(seconds: seconds, preferredTimescale: 600), toleranceBefore: .zero, toleranceAfter: .zero); p.play()
        }.onDisappear { player?.pause(); player = nil }
    }
}
struct CoachingDetail: View {
    @EnvironmentObject var store: PlayerStore
    let insight: CoachingInsight; let sessionID: UUID
    @State private var note = ""
    var related: [LocalSession] { store.sessions.filter { $0.report?.insights.contains(where: { $0.key == insight.key }) == true } }
    var body: some View {
        ScrollView { VStack(alignment: .leading, spacing: 22) {
            PriorityBadge(priority: insight.priority)
            Text(insight.title).font(.largeTitle.bold())
            Text(insight.description).font(.title3).foregroundStyle(AceTheme.muted)
            Card { VStack(alignment: .leading, spacing: 10) { Text("TAKE THIS TO THE COURT").font(.caption2.bold()).tracking(1); Text(insight.cue).font(.title2.bold()); Text(insight.drill).foregroundStyle(AceTheme.muted); Button(store.savedDrills.contains(insight.key) ? "Saved to your practice plan ✓" : "Save drill to practice plan") { store.toggleDrill(insight.key) }.font(.headline) } }
            if let url = URL(string: insight.youtubeURL), url.scheme == "https", url.host == "www.youtube.com" { Link(destination: url) { Label(insight.youtubeURL.contains("/watch?") ? "Watch the technique lesson ↗" : "Find this drill on YouTube ↗", systemImage: "play.rectangle").font(.headline) }; Text(insight.youtubeURL.contains("/watch?") ? "Opens a technique lesson on YouTube." : "Opens YouTube search results for this technique.").font(.caption).foregroundStyle(AceTheme.muted) }
            Text("Review across your videos").font(.title2.bold())
            Text("Sample timestamps help you explore playback. They are not verified evidence of a mistake.").font(.caption).foregroundStyle(AceTheme.muted)
            ForEach(related) { session in
                Card { VStack(alignment: .leading, spacing: 12) {
                    Text(session.title).font(.headline)
                    Text("\(session.date.matchDate) · \(session.type)").font(.caption).foregroundStyle(AceTheme.muted)
                    if let match = session.report?.insights.first(where: { $0.key == insight.key }) { ForEach(Array(match.moments.enumerated()), id: \.offset) { _, moment in
                        NavigationLink { LocalPlayback(session: session, seconds: moment.seconds) } label: { HStack { Image(systemName: "play.circle.fill"); Text(videoTime(moment.seconds)).monospacedDigit(); Text(moment.label).font(.subheadline); Spacer(); Image(systemName: "chevron.right") }.padding(.vertical, 6) }
                    } }
                } }
            }
            Text("Your own observations").font(.headline)
            TextEditor(text: $note).frame(minHeight: 100).padding(8).background(.white, in: RoundedRectangle(cornerRadius: 14)).overlay(RoundedRectangle(cornerRadius: 14).stroke(AceTheme.sand)).accessibilityLabel("Notes about this technique")
            Button("Save note") { store.note(note, sessionID: sessionID, key: insight.key) }.modifier(PrimaryAction())
            SimulationNotice()
        }.padding(22) }.background(AceTheme.cream).navigationTitle(insight.category).navigationBarTitleDisplayMode(.inline)
        .onAppear { note = store.sessions.first(where: { $0.id == sessionID })?.notes[insight.key] ?? "" }
    }
}
struct PracticePlan: View {
    @EnvironmentObject var store: PlayerStore
    var drills: [CoachingInsight] {
        var seen = Set<String>()
        return store.sessions.flatMap { $0.report?.insights ?? [] }.filter { store.savedDrills.contains($0.key) && seen.insert($0.key).inserted }
    }
    var body: some View {
        ScrollView { VStack(alignment: .leading, spacing: 20) {
            Text("Small habits.\nStronger tennis.").font(.largeTitle.bold())
            Text("Your saved cues, ready for the court.").foregroundStyle(AceTheme.muted)
            if drills.isEmpty { ContentUnavailableView("One focus at a time", systemImage: "target", description: Text("Save a drill from a session report to build your next practice.")) }
            ForEach(drills) { insight in Card { VStack(alignment: .leading, spacing: 12) { Text(insight.category.uppercased()).font(.caption.bold()).foregroundStyle(AceTheme.forest); Text(insight.cue).font(.title2.bold()); Text(insight.drill); if let url = URL(string: insight.youtubeURL), url.host == "www.youtube.com", url.scheme == "https" { Link("Find a tutorial on YouTube ↗", destination: url) }; Button("Remove from plan", role: .destructive) { store.toggleDrill(insight.key) }.font(.caption) } } }
            SimulationNotice()
        }.padding(22) }.background(AceTheme.cream).navigationTitle("Improve")
    }
}
struct DeviceSettings: View {
    @EnvironmentObject var store: PlayerStore
    @State private var deleting = false; @State private var creating = false
    var body: some View {
        Form {
            Section { Label(store.guest ? "Guest player" : store.profile?.name ?? "Player", systemImage: "person.crop.circle.fill").font(.title2.bold()); Text("Device-only profile · no cloud sync").font(.caption).foregroundStyle(AceTheme.muted) }
            Section("Your privacy") {
                Label("Videos stay on this device", systemImage: "lock.shield")
                Text("Only video duration, session type and selected focus are sent to the insights API. No video, audio, filename, email or notes are sent. The service host may receive ordinary connection data such as your IP address.")
                Text("The library is shared by guest mode and the single profile on this device. Login is an experience demo, not a privacy boundary. Local app videos are excluded from iCloud backup. Deleting the app may permanently remove the library; keep originals in Photos.")
                Text("All statistics and timestamps are random examples. No AI or video analysis is performed.")
            }.font(.subheadline)
            Section("Insights service") {
                TextField("https://your-project.vercel.app/api/insights", text: $store.endpoint).keyboardType(.URL).textInputAutocapitalization(.never).autocorrectionDisabled()
                    .onChange(of: store.endpoint) { _, value in UserDefaults.standard.set(value, forKey: "insightsEndpoint") }
                Text("For Simulator use http://localhost:8787/api/insights. Physical devices need an accessible HTTPS deployment.").font(.caption)
            }
            Section("Account") {
                if store.profile == nil { Button("Create device account") { creating = true } }
                Button("Sign out") { store.unlocked = false; store.guest = false }
                Button("Delete account & all local data", role: .destructive) { deleting = true }
            }
            Section("About Ace Pro") { Text("A private tennis video journal with simulated coaching inspiration. Version 0.2.0."); Text("General practice suggestions are educational. Adapt drills to your level and stop if you feel pain.") }.font(.caption)
        }.navigationTitle("Your profile")
        .sheet(isPresented: $creating) { DeviceAuth(isCreating: true) }
        .confirmationDialog("Permanently delete your device account, imported video copies, reports, notes and saved drills? Originals in Photos remain.", isPresented: $deleting, titleVisibility: .visible) { Button("Delete everything", role: .destructive) { do { try store.deleteAll() } catch { store.error = error.localizedDescription } } }
    }
}
