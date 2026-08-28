import Foundation

enum MockData {
    static let returnClips = [
        EvidenceClip(point: 8, timestamp: "12:42", score: "1–2, 30–40", label: "Short backhand return", confidence: 0.96, isVerified: true),
        EvidenceClip(point: 14, timestamp: "21:08", score: "2–3, 15–30", label: "Short backhand return", confidence: 0.91),
        EvidenceClip(point: 19, timestamp: "29:17", score: "3–4, deuce", label: "Short backhand return", confidence: 0.88),
        EvidenceClip(point: 31, timestamp: "45:52", score: "5–5, 0–15", label: "Short backhand return", confidence: 0.77),
        EvidenceClip(point: 38, timestamp: "56:31", score: "1–2, 15–30", label: "Short backhand return", confidence: 0.94),
        EvidenceClip(point: 43, timestamp: "1:04:22", score: "2–3, 30–40", label: "Short backhand return", confidence: 0.83),
        EvidenceClip(point: 51, timestamp: "1:17:09", score: "4–5, 15–30", label: "Short backhand return", confidence: 0.89)
    ]

    static let insights = [
        MatchInsight(
            priority: 1,
            kind: .returnDepth,
            title: "Short backhand returns were costly",
            summary: "You lost 64% of points when your backhand return landed inside the service box. This pattern appeared in both sets.",
            metric: "64%",
            metricLabel: "points lost",
            action: "Review return position with your coach, then practice deep cross-court returns under second-serve pressure.",
            clips: returnClips
        ),
        MatchInsight(
            priority: 2,
            kind: .secondServe,
            title: "Second serve held up under pressure",
            summary: "Your second-serve win rate rose to 58% on break points, driven by serves to the opponent’s backhand.",
            metric: "58%",
            metricLabel: "points won",
            action: "Keep the backhand body serve as a pressure pattern and test it earlier in return games.",
            clips: Array(returnClips.prefix(4))
        ),
        MatchInsight(
            priority: 3,
            kind: .netPlay,
            title: "Selective net approaches worked",
            summary: "You won 8 of 11 points at net, mostly after a deep forehand. Three rushed approaches produced errors.",
            metric: "8/11",
            metricLabel: "net points won",
            action: "Approach behind depth, not pace. Review the three early approaches before your next session.",
            clips: Array(returnClips.suffix(3))
        )
    ]

    static let matches = [
        TennisMatch(opponent: "Maya Chen", daysAgo: 1, venue: "Riverside Tennis Club", score: "4–6, 6–3, 4–6", result: "L", duration: "1h 42m", status: .ready, insights: insights),
        TennisMatch(opponent: "Sofia Reyes", daysAgo: 5, venue: "Westwood Courts", score: "6–3, 6–4", result: "W", duration: "1h 18m", status: .ready, insights: Array(insights.dropLast())),
        TennisMatch(opponent: "Nina Patel", daysAgo: 11, venue: "Home courts", score: "6–7, 2–1", result: "", duration: "54m", status: .processing, progress: 0.68),
        TennisMatch(opponent: "Jordan Lee", daysAgo: 18, venue: "Summit Racquet Club", score: "6–2, 6–2", result: "W", duration: "1h 06m", status: .ready, insights: [insights[1]])
    ]
}
