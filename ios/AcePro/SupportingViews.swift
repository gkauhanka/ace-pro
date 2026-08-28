import SwiftUI

struct TeamView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                Card {
                    VStack(alignment: .leading, spacing: 12) {
                        Label("THIS WEEK", systemImage: "person.3.fill").font(.caption.weight(.black)).tracking(1).foregroundStyle(AceTheme.green)
                        Text("Return depth is the team’s clearest shared pattern.").font(.title3.weight(.bold))
                        Text("4 of 6 players lost more points after short returns. There are 23 supporting clips ready for coach review.").font(.subheadline).foregroundStyle(AceTheme.muted)
                        Button("Review team evidence") { }.font(.subheadline.weight(.bold)).foregroundStyle(AceTheme.forest)
                    }
                }
                Text("Players").font(.title3.weight(.bold))
                ForEach(["Alex Morgan", "Sam Rivera", "Taylor Kim", "Jamie Park"], id: \.self) { player in
                    Card { HStack { Circle().fill(AceTheme.sand).frame(width: 42, height: 42).overlay(Text(player.prefix(1)).font(.headline)); Text(player).font(.headline); Spacer(); Image(systemName: "chevron.right").foregroundStyle(AceTheme.muted) } }
                }
            }.padding(20)
        }
        .background(AceTheme.cream.ignoresSafeArea()).navigationTitle("Team")
    }
}

struct ProfileView: View {
    var body: some View {
        List {
            Section {
                HStack(spacing: 14) { Circle().fill(AceTheme.forest).frame(width: 58, height: 58).overlay(Text("AM").font(.headline).foregroundStyle(AceTheme.lime)); VStack(alignment: .leading) { Text("Alex Morgan").font(.headline); Text("Right-handed • 4.5").foregroundStyle(.secondary) } }
            }
            Section("Preferences") {
                Label("Notifications", systemImage: "bell")
                Label("Video quality", systemImage: "video")
                Label("Analysis settings", systemImage: "slider.horizontal.3")
            }
            Section("Support") {
                Label("Recording guide", systemImage: "camera.viewfinder")
                Label("Privacy & data", systemImage: "lock.shield")
            }
        }
        .scrollContentBackground(.hidden).background(AceTheme.cream).navigationTitle("You")
    }
}
