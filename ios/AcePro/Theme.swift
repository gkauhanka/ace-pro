import SwiftUI

enum AceTheme {
    static let ink = Color(red: 0.08, green: 0.13, blue: 0.12)
    static let forest = Color(red: 0.04, green: 0.29, blue: 0.22)
    static let green = Color(red: 0.11, green: 0.47, blue: 0.33)
    static let lime = Color(red: 0.78, green: 0.93, blue: 0.34)
    static let cream = Color(red: 0.96, green: 0.96, blue: 0.92)
    static let sand = Color(red: 0.91, green: 0.90, blue: 0.84)
    static let muted = Color(red: 0.39, green: 0.43, blue: 0.40)
}

struct Card<Content: View>: View {
    let content: Content

    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }

    var body: some View {
        content
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(18)
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 22, style: .continuous)
                    .stroke(AceTheme.ink.opacity(0.07), lineWidth: 1)
            }
    }
}

struct PriorityBadge: View {
    let priority: Int

    var body: some View {
        Text("PRIORITY \(priority)")
            .font(.caption2.weight(.black))
            .tracking(1.1)
            .foregroundStyle(priority == 1 ? AceTheme.forest : AceTheme.muted)
            .padding(.horizontal, 10)
            .padding(.vertical, 7)
            .background(priority == 1 ? AceTheme.lime.opacity(0.75) : AceTheme.sand.opacity(0.65))
            .clipShape(Capsule())
    }
}

extension Date {
    var matchDate: String {
        formatted(.dateTime.month(.abbreviated).day())
    }
}
