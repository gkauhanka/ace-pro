import SwiftUI

struct InsightDetailView: View {
    let insight: MatchInsight
    @State private var clips: [EvidenceClip]
    @State private var selectedClip: EvidenceClip?

    init(insight: MatchInsight) {
        self.insight = insight
        _clips = State(initialValue: insight.clips)
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                hero
                actionCard
                evidence
            }
            .padding(20)
        }
        .background(AceTheme.cream.ignoresSafeArea())
        .navigationTitle("Insight")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(item: $selectedClip) { clip in ClipReviewView(clip: clip) }
    }

    private var hero: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack { PriorityBadge(priority: insight.priority); Spacer(); Image(systemName: insight.kind.icon).font(.title2) }
            Text(insight.title).font(.title.weight(.bold))
            Text(insight.summary).font(.body).foregroundStyle(.white.opacity(0.76))
            HStack(alignment: .firstTextBaseline, spacing: 8) {
                Text(insight.metric).font(.system(size: 44, weight: .black, design: .rounded))
                Text(insight.metricLabel).font(.subheadline.weight(.semibold)).foregroundStyle(.white.opacity(0.68))
            }
        }
        .padding(24)
        .foregroundStyle(.white)
        .background(AceTheme.forest)
        .clipShape(RoundedRectangle(cornerRadius: 28, style: .continuous))
    }

    private var actionCard: some View {
        Card {
            VStack(alignment: .leading, spacing: 10) {
                Label("NEXT PRACTICE", systemImage: "checkmark.seal.fill")
                    .font(.caption.weight(.black)).tracking(1.1).foregroundStyle(AceTheme.green)
                Text(insight.action).font(.headline).foregroundStyle(AceTheme.ink)
                Button("Add to practice plan") { }
                    .font(.subheadline.weight(.bold))
                    .foregroundStyle(AceTheme.forest)
                    .padding(.top, 4)
            }
        }
    }

    private var evidence: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Evidence").font(.title3.weight(.bold))
                Spacer()
                Text("\(clips.filter(\.isVerified).count)/\(clips.count) verified")
                    .font(.caption.weight(.semibold)).foregroundStyle(AceTheme.muted)
            }
            Text("Tap a point to review or correct the detection.")
                .font(.subheadline).foregroundStyle(AceTheme.muted)
            ForEach(Array(clips.enumerated()), id: \.element.id) { index, clip in
                Button { selectedClip = clip } label: {
                    HStack(spacing: 14) {
                        ZStack {
                            RoundedRectangle(cornerRadius: 14).fill(AceTheme.forest)
                            Image(systemName: "play.fill").foregroundStyle(AceTheme.lime)
                        }.frame(width: 64, height: 54)
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Point \(clip.point)  •  \(clip.score)").font(.subheadline.weight(.semibold)).foregroundStyle(AceTheme.ink)
                            Text("\(clip.timestamp)  •  \(Int(clip.confidence * 100))% confidence").font(.caption).foregroundStyle(AceTheme.muted)
                        }
                        Spacer()
                        Image(systemName: clip.isVerified ? "checkmark.circle.fill" : "chevron.right")
                            .foregroundStyle(clip.isVerified ? AceTheme.green : AceTheme.muted)
                    }
                    .padding(12).background(Color.white).clipShape(RoundedRectangle(cornerRadius: 18))
                }
                .buttonStyle(.plain)
                .swipeActions {
                    Button("Verify") { clips[index].isVerified = true }.tint(AceTheme.green)
                }
            }
        }
    }
}

struct ClipReviewView: View {
    @Environment(\.dismiss) private var dismiss
    let clip: EvidenceClip
    @State private var label: String

    init(clip: EvidenceClip) {
        self.clip = clip
        _label = State(initialValue: clip.label)
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 22) {
                ZStack {
                    LinearGradient(colors: [AceTheme.forest, AceTheme.ink], startPoint: .top, endPoint: .bottom)
                    VStack(spacing: 18) {
                        Image(systemName: "play.circle.fill").font(.system(size: 62)).foregroundStyle(AceTheme.lime)
                        Text("Mock video  •  \(clip.timestamp)").font(.caption.weight(.semibold)).foregroundStyle(.white.opacity(0.7))
                    }
                }
                .aspectRatio(9/12, contentMode: .fit)
                .clipShape(RoundedRectangle(cornerRadius: 24))

                VStack(alignment: .leading, spacing: 12) {
                    Text("Was this detected correctly?").font(.headline)
                    Picker("Detection", selection: $label) {
                        Text("Short backhand return").tag("Short backhand return")
                        Text("Deep backhand return").tag("Deep backhand return")
                        Text("Not a return").tag("Not a return")
                    }.pickerStyle(.menu).tint(AceTheme.forest)
                    Button { dismiss() } label: {
                        Text("Confirm detection").font(.headline).frame(maxWidth: .infinity).padding(15).background(AceTheme.forest).foregroundStyle(.white).clipShape(RoundedRectangle(cornerRadius: 16))
                    }
                }
                Spacer()
            }
            .padding(20)
            .background(AceTheme.cream.ignoresSafeArea())
            .navigationTitle("Point \(clip.point)")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .topBarTrailing) { Button("Done") { dismiss() } } }
        }
    }
}
