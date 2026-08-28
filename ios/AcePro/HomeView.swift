import SwiftUI

struct HomeView: View {
    @Binding var showingUpload: Bool
    private let featured = MockData.matches[0]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                header
                focusCard
                recentSection
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 32)
        }
        .background(AceTheme.cream.ignoresSafeArea())
        .toolbar(.hidden, for: .navigationBar)
    }

    private var header: some View {
        HStack(alignment: .center) {
            VStack(alignment: .leading, spacing: 3) {
                Text("ACE PRO")
                    .font(.caption.weight(.black))
                    .tracking(2.1)
                    .foregroundStyle(AceTheme.green)
                Text("Good morning, Alex")
                    .font(.title2.weight(.bold))
                    .foregroundStyle(AceTheme.ink)
            }
            Spacer()
            Button { showingUpload = true } label: {
                Image(systemName: "plus")
                    .font(.headline.weight(.bold))
                    .foregroundStyle(.white)
                    .frame(width: 44, height: 44)
                    .background(AceTheme.forest)
                    .clipShape(Circle())
            }
            .accessibilityLabel("Add match")
        }
        .padding(.top, 16)
    }

    private var focusCard: some View {
        NavigationLink(value: featured.insights[0]) {
            VStack(alignment: .leading, spacing: 20) {
                HStack {
                    Label("YOUR NEXT FOCUS", systemImage: "scope")
                        .font(.caption.weight(.black))
                        .tracking(1.2)
                    Spacer()
                    Text("FROM MAYA MATCH")
                        .font(.caption2.weight(.bold))
                        .foregroundStyle(.white.opacity(0.6))
                }
                HStack(alignment: .bottom, spacing: 18) {
                    VStack(alignment: .leading, spacing: 9) {
                        Text("Build depth on your backhand return")
                            .font(.title2.weight(.bold))
                            .fixedSize(horizontal: false, vertical: true)
                        Text("7 clips show the same pattern across both sets.")
                            .font(.subheadline)
                            .foregroundStyle(.white.opacity(0.72))
                    }
                    Spacer(minLength: 0)
                    Image(systemName: "arrow.up.right")
                        .font(.headline.weight(.bold))
                        .frame(width: 44, height: 44)
                        .background(AceTheme.lime)
                        .foregroundStyle(AceTheme.forest)
                        .clipShape(Circle())
                }
            }
            .padding(22)
            .foregroundStyle(.white)
            .background(AceTheme.forest)
            .clipShape(RoundedRectangle(cornerRadius: 28, style: .continuous))
        }
        .buttonStyle(.plain)
        .navigationDestination(for: MatchInsight.self) { InsightDetailView(insight: $0) }
    }

    private var recentSection: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Text("Recent matches")
                    .font(.title3.weight(.bold))
                Spacer()
                NavigationLink("See all") { MatchesView() }
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(AceTheme.green)
            }
            ForEach(MockData.matches.prefix(3)) { match in
                NavigationLink { MatchDetailView(match: match) } label: {
                    MatchRow(match: match)
                }
                .buttonStyle(.plain)
            }
        }
    }
}

struct MatchRow: View {
    let match: TennisMatch

    var body: some View {
        Card {
            HStack(spacing: 14) {
                ZStack {
                    RoundedRectangle(cornerRadius: 14, style: .continuous)
                        .fill(match.status == .processing ? AceTheme.sand : AceTheme.lime.opacity(0.55))
                    if match.status == .processing {
                        ProgressView(value: match.progress)
                            .progressViewStyle(.circular)
                            .tint(AceTheme.green)
                    } else {
                        Text(match.result)
                            .font(.title3.weight(.black))
                            .foregroundStyle(AceTheme.forest)
                    }
                }
                .frame(width: 50, height: 50)

                VStack(alignment: .leading, spacing: 4) {
                    Text("vs. \(match.opponent)")
                        .font(.headline)
                        .foregroundStyle(AceTheme.ink)
                    Text("\(match.date.matchDate)  •  \(match.score)")
                        .font(.subheadline)
                        .foregroundStyle(AceTheme.muted)
                }
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.caption.weight(.bold))
                    .foregroundStyle(AceTheme.muted.opacity(0.7))
            }
        }
    }
}
