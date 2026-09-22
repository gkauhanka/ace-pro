import SwiftUI
import AVFoundation
import PhotosUI
import UniformTypeIdentifiers

@main
struct AceProApp: App {
    @StateObject private var store = PlayerStore()

    var body: some Scene {
        WindowGroup {
            RootView().environmentObject(store).preferredColorScheme(.light)
        }
    }
}

struct LocalSession: Codable, Identifiable {
    var id = UUID()
    var title: String
    var date = Date()
    var type: String
    var focus: String
    var filename: String
    var duration: Double
    var notes: [String: String] = [:]
}

enum PlayerError: LocalizedError {
    case message(String)

    var errorDescription: String? {
        guard case .message(let message) = self else { return nil }
        return message
    }
}

struct PickedMovie: Transferable {
    let url: URL

    static var transferRepresentation: some TransferRepresentation {
        FileRepresentation(importedContentType: .movie) { received in
            let url = FileManager.default.temporaryDirectory
                .appendingPathComponent(UUID().uuidString)
                .appendingPathExtension(received.file.pathExtension)
            try FileManager.default.copyItem(at: received.file, to: url)
            return PickedMovie(url: url)
        }
    }
}

@MainActor
final class PlayerStore: ObservableObject {
    @Published var sessions: [LocalSession] = []
    @Published var error: String?

    let directory: URL

    init() {
        directory = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("AcePro", isDirectory: true)
        do {
            try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
            var localDirectory = directory
            var values = URLResourceValues()
            values.isExcludedFromBackup = true
            try localDirectory.setResourceValues(values)
            let libraryURL = directory.appendingPathComponent("library.json")
            if FileManager.default.fileExists(atPath: libraryURL.path) {
                sessions = try JSONDecoder().decode([LocalSession].self, from: Data(contentsOf: libraryURL))
            }
        } catch {
            self.error = "Your local library could not be loaded: \(error.localizedDescription)"
        }
    }

    func save() throws {
        try JSONEncoder().encode(sessions).write(
            to: directory.appendingPathComponent("library.json"),
            options: [.atomic, .completeFileProtection]
        )
    }

    func url(for session: LocalSession) -> URL {
        directory.appendingPathComponent(session.filename)
    }

    func importVideo(_ source: URL, title: String, type: String, focus: String) async throws -> UUID {
        let asset = AVURLAsset(url: source)
        let duration = try await asset.load(.duration).seconds
        let tracks = try await asset.loadTracks(withMediaType: .video)
        guard duration.isFinite, duration >= 1, duration <= 21_600, !tracks.isEmpty else {
            throw PlayerError.message("Choose a playable video between 1 second and 6 hours.")
        }

        let filename = UUID().uuidString + "." + (source.pathExtension.isEmpty ? "mov" : source.pathExtension)
        let destination = directory.appendingPathComponent(filename)
        try FileManager.default.copyItem(at: source, to: destination)
        do {
            try FileManager.default.setAttributes(
                [.protectionKey: FileProtectionType.complete],
                ofItemAtPath: destination.path
            )
        } catch {
            try? FileManager.default.removeItem(at: destination)
            throw error
        }

        let cleanedTitle = title.trimmingCharacters(in: .whitespacesAndNewlines)
        let session = LocalSession(
            title: cleanedTitle.isEmpty ? "\(type) session" : cleanedTitle,
            type: type,
            focus: focus,
            filename: filename,
            duration: duration
        )
        sessions.insert(session, at: 0)
        do {
            try save()
        } catch {
            sessions.removeAll { $0.id == session.id }
            try? FileManager.default.removeItem(at: destination)
            throw error
        }
        return session.id
    }

    func updateObservation(_ text: String, sessionID: UUID) throws {
        guard let index = sessions.firstIndex(where: { $0.id == sessionID }) else { return }
        sessions[index].notes["session"] = text
        try save()
    }

    func remove(_ id: UUID) throws {
        guard let session = sessions.first(where: { $0.id == id }) else { return }
        let previous = sessions
        sessions.removeAll { $0.id == id }
        do {
            try save()
            let videoURL = url(for: session)
            if FileManager.default.fileExists(atPath: videoURL.path) {
                try FileManager.default.removeItem(at: videoURL)
            }
        } catch {
            sessions = previous
            try? save()
            throw error
        }
    }

    func deleteAll() throws {
        for file in try FileManager.default.contentsOfDirectory(at: directory, includingPropertiesForKeys: nil) {
            try FileManager.default.removeItem(at: file)
        }
        sessions = []
    }
}

func videoTime(_ seconds: Double) -> String {
    let value = Int(max(0, seconds))
    return value >= 3_600
        ? String(format: "%d:%02d:%02d", value / 3_600, value / 60 % 60, value % 60)
        : String(format: "%d:%02d", value / 60, value % 60)
}
