import SwiftUI

struct UploadFlowView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var step = 0
    @State private var opponent = ""
    @State private var venue = ""
    @State private var isUploading = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                HStack(spacing: 8) {
                    ForEach(0..<3) { index in
                        Capsule().fill(index <= step ? AceTheme.green : AceTheme.sand).frame(height: 5)
                    }
                }
                .padding(.top, 8)

                Group {
                    if step == 0 { source }
                    else if step == 1 { details }
                    else { upload }
                }
                Spacer()
            }
            .padding(20)
            .background(AceTheme.cream.ignoresSafeArea())
            .navigationTitle("Add a match")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .topBarLeading) { Button("Cancel") { dismiss() } } }
        }
    }

    private var source: some View {
        VStack(alignment: .leading, spacing: 18) {
            Text("Choose your match video").font(.title2.weight(.bold))
            Text("A full match from behind the baseline works best. You can close the app while it uploads.").foregroundStyle(AceTheme.muted)
            Button { step = 1 } label: {
                uploadChoice(icon: "photo.on.rectangle", title: "Photo library", subtitle: "Choose a video already on this iPhone")
            }.buttonStyle(.plain)
            Button { step = 1 } label: {
                uploadChoice(icon: "folder", title: "Browse files", subtitle: "iCloud Drive, GoPro, or another source")
            }.buttonStyle(.plain)
            Card {
                Label("Best results: fixed camera, full court visible, 1080p or higher.", systemImage: "lightbulb.fill")
                    .font(.subheadline).foregroundStyle(AceTheme.muted)
            }
        }
    }

    private func uploadChoice(icon: String, title: String, subtitle: String) -> some View {
        Card {
            HStack(spacing: 16) {
                Image(systemName: icon).font(.title2).foregroundStyle(AceTheme.green).frame(width: 42, height: 42).background(AceTheme.lime.opacity(0.5)).clipShape(Circle())
                VStack(alignment: .leading, spacing: 4) { Text(title).font(.headline); Text(subtitle).font(.caption).foregroundStyle(AceTheme.muted) }
                Spacer(); Image(systemName: "chevron.right").foregroundStyle(AceTheme.muted)
            }
        }
    }

    private var details: some View {
        VStack(alignment: .leading, spacing: 18) {
            Text("Match details").font(.title2.weight(.bold))
            Text("This helps organize your reports. You can edit it later.").foregroundStyle(AceTheme.muted)
            VStack(spacing: 14) {
                TextField("Opponent name", text: $opponent)
                Divider()
                TextField("Venue (optional)", text: $venue)
            }
            .padding(18).background(Color.white).clipShape(RoundedRectangle(cornerRadius: 20))
            Button { step = 2; isUploading = true } label: { primaryButton("Continue") }.disabled(opponent.isEmpty)
        }
    }

    private var upload: some View {
        VStack(spacing: 22) {
            Spacer().frame(height: 20)
            ZStack {
                Circle().fill(AceTheme.lime.opacity(0.45)).frame(width: 112, height: 112)
                Image(systemName: "arrow.up.circle.fill").font(.system(size: 58)).foregroundStyle(AceTheme.forest)
            }
            Text("Your match is uploading").font(.title2.weight(.bold))
            Text("We’ll start analysis automatically and notify you when your report is ready.").multilineTextAlignment(.center).foregroundStyle(AceTheme.muted)
            ProgressView(value: 0.42).tint(AceTheme.green)
            HStack { Text("42%").font(.subheadline.weight(.bold)); Spacer(); Text("About 8 min left").font(.subheadline).foregroundStyle(AceTheme.muted) }
            Button { dismiss() } label: { primaryButton("Done") }
        }
    }

    private func primaryButton(_ title: String) -> some View {
        Text(title).font(.headline).frame(maxWidth: .infinity).padding(16).background(AceTheme.forest).foregroundStyle(.white).clipShape(RoundedRectangle(cornerRadius: 17))
    }
}
