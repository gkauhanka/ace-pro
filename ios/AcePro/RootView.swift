import SwiftUI

struct RootView: View {
    @State private var selection = 0
    @State private var showingUpload = false

    var body: some View {
        TabView(selection: $selection) {
            NavigationStack { HomeView(showingUpload: $showingUpload) }
                .tabItem { Label("Today", systemImage: "sparkles") }
                .tag(0)

            NavigationStack { MatchesView() }
                .tabItem { Label("Matches", systemImage: "play.rectangle.on.rectangle") }
                .tag(1)

            NavigationStack { TeamView() }
                .tabItem { Label("Team", systemImage: "person.2") }
                .tag(2)

            NavigationStack { ProfileView() }
                .tabItem { Label("You", systemImage: "person.crop.circle") }
                .tag(3)
        }
        .tint(AceTheme.forest)
        .sheet(isPresented: $showingUpload) { UploadFlowView() }
    }
}
