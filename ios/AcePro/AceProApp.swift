import SwiftUI
import AVKit
import PhotosUI
import UniformTypeIdentifiers
import Security
import CommonCrypto

@main
struct AceProApp: App {
    @StateObject private var store = PlayerStore()
    var body: some Scene {
        WindowGroup { RootView().environmentObject(store).preferredColorScheme(.light) }
    }
}

struct CoachingMoment: Codable, Hashable { let seconds: Double; let label: String }
struct CoachingInsight: Codable, Identifiable, Hashable {
    var id: String { key }
    let key: String; let title: String; let category: String; let metric: String; let unit: String
    let description: String; let drill: String; let cue: String; let value: Int; let priority: Int
    let youtubeURL: String; let moments: [CoachingMoment]
}
struct CoachingReport: Codable { let schemaVersion: Int; let simulated: Bool; let disclosure: String; let insights: [CoachingInsight] }
struct LocalSession: Codable, Identifiable {
    var id = UUID(); var title: String; var date = Date(); var type: String; var focus: String
    var filename: String; var duration: Double; var report: CoachingReport?
    var notes: [String: String] = [:]
}
struct DeviceProfile: Codable { var name: String; var email: String; var salt: Data; var passwordHash: Data }
enum PlayerError: LocalizedError {
    case message(String)
    var errorDescription: String? { if case .message(let message) = self { return message }; return nil }
}
struct PickedMovie: Transferable {
    let url: URL
    static var transferRepresentation: some TransferRepresentation {
        FileRepresentation(importedContentType: .movie) { received in
            let url = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString).appendingPathExtension(received.file.pathExtension)
            try FileManager.default.copyItem(at: received.file, to: url)
            return PickedMovie(url: url)
        }
    }
}

@MainActor final class PlayerStore: ObservableObject {
    @Published var sessions: [LocalSession] = []
    @Published var profile: DeviceProfile?
    @Published var unlocked = false
    @Published var guest = false
    @Published var error: String?
    @Published var savedDrills: Set<String> = []
    @Published var endpoint: String = UserDefaults.standard.string(forKey: "insightsEndpoint") ?? "http://localhost:8787/api/insights"
    let directory: URL
    init() {
        directory = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0].appendingPathComponent("AcePro", isDirectory: true)
        do {
            try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
            var local = directory; var values = URLResourceValues(); values.isExcludedFromBackup = true; try local.setResourceValues(values)
            if FileManager.default.fileExists(atPath: directory.appendingPathComponent("library.json").path) {
                sessions = try JSONDecoder().decode([LocalSession].self, from: Data(contentsOf: directory.appendingPathComponent("library.json")))
            }
            profile = try readProfile()
            savedDrills = Set(UserDefaults.standard.stringArray(forKey: "savedDrills") ?? [])
        } catch { self.error = "Your local library could not be loaded: \(error.localizedDescription)" }
    }
    func save() throws {
        try JSONEncoder().encode(sessions).write(to: directory.appendingPathComponent("library.json"), options: [.atomic, .completeFileProtection])
    }
    func url(for session: LocalSession) -> URL { directory.appendingPathComponent(session.filename) }
    func passwordKey(_ password: String, salt: Data) throws -> Data {
        let bytes = Array(password.utf8); var result = [UInt8](repeating: 0, count: 32)
        let status = salt.withUnsafeBytes { saltBytes in
            bytes.withUnsafeBytes { passwordBytes in
                CCKeyDerivationPBKDF(CCPBKDFAlgorithm(kCCPBKDF2), passwordBytes.baseAddress!.assumingMemoryBound(to: Int8.self), bytes.count, saltBytes.baseAddress!.assumingMemoryBound(to: UInt8.self), salt.count, CCPseudoRandomAlgorithm(kCCPRFHmacAlgSHA256), 210_000, &result, 32)
            }
        }
        guard status == kCCSuccess else { throw PlayerError.message("Could not secure your profile.") }
        return Data(result)
    }
    var keychainQuery: [String: Any] { [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: "com.acepro.device-profile", kSecAttrAccount as String: "player"] }
    func readProfile() throws -> DeviceProfile? {
        var query = keychainQuery; query[kSecReturnData as String] = true
        var result: CFTypeRef?; let status = SecItemCopyMatching(query as CFDictionary, &result)
        if status == errSecItemNotFound { return nil }
        guard status == errSecSuccess, let data = result as? Data else { throw PlayerError.message("Could not open the device keychain.") }
        return try JSONDecoder().decode(DeviceProfile.self, from: data)
    }
    func createProfile(name: String, email: String, password: String) throws {
        guard profile == nil else { throw PlayerError.message("A profile already exists on this device. Sign in instead.") }
        guard !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty, email.contains("@"), email.contains("."), password.count >= 8 else { throw PlayerError.message("Enter your name, a valid email, and a password with at least 8 characters.") }
        var salt = Data(count: 32)
        let status = salt.withUnsafeMutableBytes { SecRandomCopyBytes(kSecRandomDefault, 32, $0.baseAddress!) }
        guard status == errSecSuccess else { throw PlayerError.message("Could not secure your profile.") }
        let value = DeviceProfile(name: name.trimmingCharacters(in: .whitespacesAndNewlines), email: email.lowercased().trimmingCharacters(in: .whitespacesAndNewlines), salt: salt, passwordHash: try passwordKey(password, salt: salt))
        var query = keychainQuery; query[kSecValueData as String] = try JSONEncoder().encode(value); query[kSecAttrAccessible as String] = kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        guard SecItemAdd(query as CFDictionary, nil) == errSecSuccess else { throw PlayerError.message("Could not save your profile securely.") }
        profile = value; unlocked = true; guest = false
    }
    func login(email: String, password: String) throws {
        guard !password.isEmpty, let profile, profile.email == email.lowercased().trimmingCharacters(in: .whitespacesAndNewlines), try passwordKey(password, salt: profile.salt) == profile.passwordHash else { throw PlayerError.message("Email or password doesn’t match this device’s profile.") }
        unlocked = true; guest = false
    }
    func importVideo(_ source: URL, title: String, type: String, focus: String) async throws -> UUID {
        let asset = AVURLAsset(url: source)
        let duration = try await asset.load(.duration).seconds
        let tracks = try await asset.loadTracks(withMediaType: .video)
        guard duration.isFinite, duration >= 1, duration <= 21600, !tracks.isEmpty else { throw PlayerError.message("Choose a playable video between 1 second and 6 hours.") }
        let filename = UUID().uuidString + "." + (source.pathExtension.isEmpty ? "mov" : source.pathExtension)
        let destination = directory.appendingPathComponent(filename)
        try FileManager.default.copyItem(at: source, to: destination)
        do { try FileManager.default.setAttributes([.protectionKey: FileProtectionType.complete], ofItemAtPath: destination.path) }
        catch { try? FileManager.default.removeItem(at: destination); throw error }
        let session = LocalSession(title: title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? "\(type) session" : title, type: type, focus: focus, filename: filename, duration: duration)
        sessions.insert(session, at: 0)
        do { try save() } catch { sessions.removeAll { $0.id == session.id }; try? FileManager.default.removeItem(at: destination); throw error }
        return session.id
    }
    func analyze(_ id: UUID) async throws {
        guard let session = sessions.first(where: { $0.id == id }), let url = URL(string: endpoint), url.path == "/api/insights" else { throw PlayerError.message("Set a valid insights API URL in Profile.") }
        #if !DEBUG
        guard url.scheme == "https" else { throw PlayerError.message("The insights service requires HTTPS.") }
        #endif
        var request = URLRequest(url: url); request.httpMethod = "POST"; request.timeoutInterval = 30
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: ["durationSeconds": session.duration, "sessionType": session.type, "focus": session.focus])
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let response = response as? HTTPURLResponse, response.statusCode == 200 else { throw PlayerError.message("The insights service is unavailable. Your video is safe on this device. Try again.") }
        let report = try JSONDecoder().decode(CoachingReport.self, from: data)
        guard report.simulated, report.schemaVersion == 1, report.insights.count == 3, Set(report.insights.map(\.key)).count == 3,
              report.insights.allSatisfy({ (0...100).contains($0.value) && $0.moments.allSatisfy { $0.seconds.isFinite && $0.seconds >= 0 && $0.seconds < session.duration } }) else { throw PlayerError.message("The service returned an invalid report. Try again.") }
        try Task.checkCancellation()
        if let index = sessions.firstIndex(where: { $0.id == id }) { sessions[index].report = report; try save() }
    }
    func remove(_ id: UUID) throws {
        guard let session = sessions.first(where: { $0.id == id }) else { return }
        let previous = sessions; sessions.removeAll { $0.id == id }
        do { try save() } catch { sessions = previous; throw error }
        do { if FileManager.default.fileExists(atPath: url(for: session).path) { try FileManager.default.removeItem(at: url(for: session)) } }
        catch { sessions = previous; try? save(); throw error }
        let remainingKeys = Set(sessions.flatMap { $0.report?.insights.map(\.key) ?? [] })
        savedDrills.formIntersection(remainingKeys)
        UserDefaults.standard.set(Array(savedDrills), forKey: "savedDrills")
    }
    func deleteAll() throws {
        for session in sessions { try remove(session.id) }
        // Also clean up any orphan copy left by an interrupted import.
        for file in try FileManager.default.contentsOfDirectory(at: directory, includingPropertiesForKeys: nil) { try FileManager.default.removeItem(at: file) }
        let status = SecItemDelete(keychainQuery as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else { throw PlayerError.message("Could not delete your device profile. Please retry.") }
        profile = nil; unlocked = false; guest = false; savedDrills = []; UserDefaults.standard.removeObject(forKey: "savedDrills")
    }
    func toggleDrill(_ key: String) { if savedDrills.contains(key) { savedDrills.remove(key) } else { savedDrills.insert(key) }; UserDefaults.standard.set(Array(savedDrills), forKey: "savedDrills") }
    func note(_ text: String, sessionID: UUID, key: String) {
        guard let index = sessions.firstIndex(where: { $0.id == sessionID }) else { return }
        sessions[index].notes[key] = text
        do { try save() } catch { self.error = error.localizedDescription }
    }
}
func videoTime(_ seconds: Double) -> String {
    let value = Int(max(0, seconds)); return value >= 3600 ? String(format: "%d:%02d:%02d", value / 3600, value / 60 % 60, value % 60) : String(format: "%d:%02d", value / 60, value % 60)
}
