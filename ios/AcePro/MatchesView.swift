import SwiftUI

struct MatchesView: View {
    @State private var query = ""
    @State private var filter = "All"

    private var filtered: [TennisMatch] {
        MockData.matches.filter { match in
            (query.isEmpty || match.opponent.localizedCaseInsensitiveContains(query)) &&
            (filter == "All" || (filter == "Ready" ? match.status == .ready : match.status == .processing))
        }
    }

    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 14) {
                Picker("Filter", selection: $filter) {
                    Text("All").tag("All")
                    Text("Ready").tag("Ready")
                    Text("Processing").tag("Processing")
                }
                .pickerStyle(.segmented)
                .padding(.bottom, 6)

                ForEach(filtered) { match in
                    NavigationLink { MatchDetailView(match: match) } label: { MatchRow(match: match) }
                        .buttonStyle(.plain)
                }
            }
            .padding(20)
        }
        .background(AceTheme.cream.ignoresSafeArea())
        .navigationTitle("Matches")
        .searchable(text: $query, prompt: "Opponent or venue")
    }
}

struct MatchDetailView: View {
    let match: TennisMatch

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                matchHeader
                if match.status == .processing { processingCard } else { insights }
            }
            .padding(20)
        }
        .background(AceTheme.cream.ignoresSafeArea())
        .navigationTitle("Match report")
        .navigationBarTitleDisplayMode(.inline)
    }

    private var matchHeader: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(alignment: .firstTextBaseline) {
                Text("vs. \(match.opponent)").font(.title2.weight(.bold))
                Spacer()
                Text(match.result).font(.title.weight(.black)).foregroundStyle(AceTheme.green)
            }
            Text(match.score).font(.title3.weight(.semibold))
            HStack {
                Label(match.date.matchDate, systemImage: "calendar")
                Spacer()
                Label(match.duration, systemImage: "clock")
            }
            .font(.subheadline)
            .foregroundStyle(AceTheme.muted)
            Text(match.venue).font(.subheadline).foregroundStyle(AceTheme.muted)
        }
        .padding(22)
        .foregroundStyle(AceTheme.ink)
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
    }

    private var processingCard: some View {
        Card {
            VStack(alignment: .leading, spacing: 14) {
                Label("Finding patterns", systemImage: "waveform.path.ecg")
                    .font(.headline)
                ProgressView(value: match.progress).tint(AceTheme.green)
                Text("We’ve analyzed 68% of the match. You can leave the app—we’ll notify you when your report is ready.")
                    .font(.subheadline).foregroundStyle(AceTheme.muted)
            }
        }
    }

    private var insights: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("What shaped the match").font(.title3.weight(.bold))
            Text("Ranked by estimated impact, with every finding linked to video evidence.")
                .font(.subheadline).foregroundStyle(AceTheme.muted)
            ForEach(match.insights) { insight in
                NavigationLink { InsightDetailView(insight: insight) } label: { InsightCard(insight: insight) }
                    .buttonStyle(.plain)
            }
        }
    }
}

struct InsightCard: View {
    let insight: MatchInsight

    var body: some View {
        Card {
            VStack(alignment: .leading, spacing: 14) {
                HStack { PriorityBadge(priority: insight.priority); Spacer(); Image(systemName: insight.kind.icon).foregroundStyle(AceTheme.green) }
                Text(insight.title).font(.headline).foregroundStyle(AceTheme.ink)
                Text(insight.summary).font(.subheadline).foregroundStyle(AceTheme.muted).lineLimit(3)
                HStack {
                    Label("\(insight.clips.count) clips", systemImage: "play.square.stack")
                    Spacer()
                    Image(systemName: "arrow.right")
                }
                .font(.caption.weight(.bold)).foregroundStyle(AceTheme.green)
            }
        }
    }
}
