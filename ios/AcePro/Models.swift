import Foundation

enum InsightKind: String, CaseIterable, Identifiable {
    case returnDepth = "Return depth"
    case secondServe = "Second serve"
    case netPlay = "Net play"

    var id: String { rawValue }
    var icon: String {
        switch self {
        case .returnDepth: "arrow.down.right.circle.fill"
        case .secondServe: "target"
        case .netPlay: "figure.tennis"
        }
    }
}

struct EvidenceClip: Identifiable, Hashable {
    let id: UUID
    let point: Int
    let timestamp: String
    let score: String
    let label: String
    let confidence: Double
    var isVerified: Bool

    init(point: Int, timestamp: String, score: String, label: String, confidence: Double, isVerified: Bool = false) {
        id = UUID()
        self.point = point
        self.timestamp = timestamp
        self.score = score
        self.label = label
        self.confidence = confidence
        self.isVerified = isVerified
    }
}

struct MatchInsight: Identifiable, Hashable {
    let id: UUID
    let priority: Int
    let kind: InsightKind
    let title: String
    let summary: String
    let metric: String
    let metricLabel: String
    let action: String
    let clips: [EvidenceClip]

    init(priority: Int, kind: InsightKind, title: String, summary: String, metric: String, metricLabel: String, action: String, clips: [EvidenceClip]) {
        id = UUID()
        self.priority = priority
        self.kind = kind
        self.title = title
        self.summary = summary
        self.metric = metric
        self.metricLabel = metricLabel
        self.action = action
        self.clips = clips
    }
}

enum MatchStatus: String {
    case ready = "Analysis ready"
    case processing = "Analyzing"
    case uploaded = "Uploaded"
}

struct TennisMatch: Identifiable, Hashable {
    let id: UUID
    let opponent: String
    let date: Date
    let venue: String
    let score: String
    let result: String
    let duration: String
    let status: MatchStatus
    let progress: Double
    let insights: [MatchInsight]

    init(opponent: String, daysAgo: Int, venue: String, score: String, result: String, duration: String, status: MatchStatus, progress: Double = 1, insights: [MatchInsight] = []) {
        id = UUID()
        self.opponent = opponent
        date = Calendar.current.date(byAdding: .day, value: -daysAgo, to: .now) ?? .now
        self.venue = venue
        self.score = score
        self.result = result
        self.duration = duration
        self.status = status
        self.progress = progress
        self.insights = insights
    }
}
