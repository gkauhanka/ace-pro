import SwiftUI
import AVFoundation
import Vision
import ImageIO
#if canImport(FoundationModels)
import FoundationModels
#endif

struct VisionDebugPoint: Hashable, Sendable {
    let x: Double
    let y: Double
}

struct VisionDebugPoint3D: Hashable, Sendable {
    let x: Double
    let y: Double
    let z: Double
}

struct VisionTrajectoryDebugSample: Identifiable, Sendable {
    let id: UUID
    let startTimestampSeconds: Double
    let endTimestampSeconds: Double
    let confidence: Double
    let radius: Double
    let detectedPoints: [VisionDebugPoint]
    let projectedPoints: [VisionDebugPoint]
}

struct VisionPoseDebugSample: Identifiable, Sendable {
    let id = UUID()
    let timestampSeconds: Double
    let confidence: Double
    let joints: [String: VisionDebugPoint]
}

struct VisionHandPoseDebugSample: Identifiable, Sendable {
    let id = UUID()
    let timestampSeconds: Double
    let confidence: Double
    let chirality: String
    let joints: [String: VisionDebugPoint]
}

struct VisionPose3DDebugSample: Identifiable, Sendable {
    let id = UUID()
    let timestampSeconds: Double
    let confidence: Double
    let bodyHeightMeters: Double
    let heightWasMeasured: Bool
    let joints: [String: VisionDebugPoint3D]
}

struct VisionOpticalFlowDebugSample: Identifiable, Sendable {
    let id = UUID()
    let timestampSeconds: Double
    let averageMagnitude: Double
    let peakMagnitude: Double
}

struct OnDeviceVideoAnalysisResult: Sendable {
    let analyzedDurationSeconds: Double
    let sourceWidth: Int
    let sourceHeight: Int
    let nominalFrameRate: Double
    let decodedFrameCount: Int
    let trajectoryFrameCount: Int
    let skippedTrajectoryFrameCount: Int
    let poseFrameCount: Int
    let opticalFlowFrameCount: Int
    let trajectories: [VisionTrajectoryDebugSample]
    let poses: [VisionPoseDebugSample]
    let handPoses: [VisionHandPoseDebugSample]
    let poses3D: [VisionPose3DDebugSample]
    let opticalFlow: [VisionOpticalFlowDebugSample]
    let elapsedSeconds: Double

    var averagePoseConfidence: Double {
        guard !poses.isEmpty else { return 0 }
        return poses.reduce(0) { $0 + $1.confidence } / Double(poses.count)
    }

    var trajectoryWarning: String? {
        guard skippedTrajectoryFrameCount > 0 else { return nil }
        if trajectoryFrameCount == 0 {
            return "Trajectory tracking could not lock onto this clip because the camera or background was moving heavily. Pose analysis still completed. For ball trajectories, use a stationary camera with the full court in view."
        }
        return "Apple Vision skipped \(skippedTrajectoryFrameCount) noisy frames and recovered automatically. The results below use the stable parts of the clip."
    }

    var averageOpticalFlowMagnitude: Double {
        guard !opticalFlow.isEmpty else { return 0 }
        return opticalFlow.reduce(0) { $0 + $1.averageMagnitude } / Double(opticalFlow.count)
    }
}

enum OnDeviceVideoAnalysisError: LocalizedError {
    case missingVideoTrack
    case cannotReadVideo(String)
    case noFrames

    var errorDescription: String? {
        switch self {
        case .missingVideoTrack:
            "The saved session does not contain a readable video track."
        case .cannotReadVideo(let reason):
            "The video could not be analyzed: \(reason)"
        case .noFrames:
            "No video frames were available for analysis."
        }
    }
}

struct OnDeviceVideoAnalyzer: Sendable {
    typealias ProgressHandler = @Sendable (_ progress: Double, _ stage: String) -> Void

    func analyze(
        url: URL,
        maximumDurationSeconds: Double,
        progress: @escaping ProgressHandler
    ) async throws -> OnDeviceVideoAnalysisResult {
        let asset = AVURLAsset(url: url)
        let tracks = try await asset.loadTracks(withMediaType: .video)
        guard let track = tracks.first else { throw OnDeviceVideoAnalysisError.missingVideoTrack }

        let assetDuration = try await asset.load(.duration).seconds
        let naturalSize = try await track.load(.naturalSize)
        let preferredTransform = try await track.load(.preferredTransform)
        let nominalFrameRate = Double(try await track.load(.nominalFrameRate))
        let transformedSize = naturalSize.applying(preferredTransform)
        let width = Int(abs(transformedSize.width).rounded())
        let height = Int(abs(transformedSize.height).rounded())
        let limit = max(1, min(maximumDurationSeconds, assetDuration.isFinite ? assetDuration : maximumDurationSeconds))
        let orientation = Self.orientation(for: preferredTransform)

        let worker = Task.detached(priority: .userInitiated) {
            try Self.process(
                asset: asset,
                track: track,
                durationSeconds: limit,
                width: width,
                height: height,
                nominalFrameRate: nominalFrameRate,
                orientation: orientation,
                progress: progress
            )
        }
        return try await withTaskCancellationHandler {
            try await worker.value
        } onCancel: {
            worker.cancel()
        }
    }

    private static func process(
        asset: AVAsset,
        track: AVAssetTrack,
        durationSeconds: Double,
        width: Int,
        height: Int,
        nominalFrameRate: Double,
        orientation: CGImagePropertyOrientation,
        progress: ProgressHandler
    ) throws -> OnDeviceVideoAnalysisResult {
        let started = CFAbsoluteTimeGetCurrent()
        let reader = try AVAssetReader(asset: asset)
        reader.timeRange = CMTimeRange(
            start: .zero,
            duration: CMTime(seconds: durationSeconds, preferredTimescale: 600)
        )
        let output = AVAssetReaderTrackOutput(
            track: track,
            outputSettings: [
                kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA
            ]
        )
        output.alwaysCopiesSampleData = false
        guard reader.canAdd(output) else {
            throw OnDeviceVideoAnalysisError.cannotReadVideo("AVFoundation rejected the decoded-frame output.")
        }
        reader.add(output)
        guard reader.startReading() else {
            throw OnDeviceVideoAnalysisError.cannotReadVideo(reader.error?.localizedDescription ?? "The reader did not start.")
        }

        var trajectoryRequest = makeTrajectoryRequest()
        var trajectoryHandler = VNSequenceRequestHandler()
        let poseRequest = VNDetectHumanBodyPoseRequest()
        let handPoseRequest = VNDetectHumanHandPoseRequest()
        handPoseRequest.maximumHandCount = 2
        let pose3DRequest = VNDetectHumanBodyPose3DRequest()
        var trajectoryByID: [UUID: VisionTrajectoryDebugSample] = [:]
        var poses: [VisionPoseDebugSample] = []
        var handPoses: [VisionHandPoseDebugSample] = []
        var poses3D: [VisionPose3DDebugSample] = []
        var opticalFlow: [VisionOpticalFlowDebugSample] = []
        var decodedFrames = 0
        var trajectoryFrames = 0
        var skippedTrajectoryFrames = 0
        var poseFrames = 0
        var opticalFlowFrames = 0
        var lastPoseTime = -Double.infinity
        var lastHandPoseTime = -Double.infinity
        var lastPose3DTime = -Double.infinity
        var lastOpticalFlowTime = -Double.infinity
        var previousFlowBuffer: CVPixelBuffer?
        var lastProgressBucket = -1
        var analyzedDuration = 0.0

        progress(0, "Preparing Apple Vision…")

        while let sampleBuffer = output.copyNextSampleBuffer() {
            do { try Task.checkCancellation() }
            catch { reader.cancelReading(); throw error }

            let timestamp = CMSampleBufferGetPresentationTimeStamp(sampleBuffer).seconds
            guard timestamp.isFinite else { continue }
            analyzedDuration = min(durationSeconds, max(analyzedDuration, timestamp))
            decodedFrames += 1

            do {
                try trajectoryHandler.perform([trajectoryRequest], on: sampleBuffer, orientation: orientation)
                trajectoryFrames += 1
                for observation in trajectoryRequest.results ?? [] {
                    let interval = trajectoryInterval(
                        observation: observation,
                        currentTimestamp: timestamp,
                        nominalFrameRate: nominalFrameRate
                    )
                    trajectoryByID[observation.uuid] = VisionTrajectoryDebugSample(
                        id: observation.uuid,
                        startTimestampSeconds: interval.start,
                        endTimestampSeconds: interval.end,
                        confidence: Double(observation.confidence),
                        radius: Double(observation.movingAverageRadius),
                        detectedPoints: observation.detectedPoints.map { VisionDebugPoint(x: $0.x, y: $0.y) },
                        projectedPoints: observation.projectedPoints.map { VisionDebugPoint(x: $0.x, y: $0.y) }
                    )
                }
            } catch {
                // VNDetectTrajectoriesRequest can reject a frame when global camera
                // motion creates too many candidates. That should not discard pose
                // results or prevent the tracker from trying a later, stable section.
                skippedTrajectoryFrames += 1
                trajectoryHandler = VNSequenceRequestHandler()
                trajectoryRequest = makeTrajectoryRequest()
            }

            if timestamp - lastPoseTime >= 0.2 {
                let poseHandler = VNImageRequestHandler(
                    cmSampleBuffer: sampleBuffer,
                    orientation: orientation,
                    options: [:]
                )
                do {
                    try poseHandler.perform([poseRequest])
                    poseFrames += 1
                    if let bestPose = try bestPose(from: poseRequest.results ?? [], timestamp: timestamp) {
                        poses.append(bestPose)
                    }
                } catch {
                    // A missed or undersized player should not terminate analysis.
                }
                lastPoseTime = timestamp
            }

            if timestamp - lastHandPoseTime >= 0.5 {
                let handHandler = VNImageRequestHandler(
                    cmSampleBuffer: sampleBuffer,
                    orientation: orientation,
                    options: [:]
                )
                do {
                    try handHandler.perform([handPoseRequest])
                    handPoses.append(contentsOf: try handPoseSamples(
                        from: handPoseRequest.results ?? [],
                        timestamp: timestamp
                    ))
                } catch {
                    // Hand detection commonly returns nothing in wide court video.
                }
                lastHandPoseTime = timestamp
            }

            if timestamp - lastPose3DTime >= 1.0 {
                let pose3DHandler = VNImageRequestHandler(
                    cmSampleBuffer: sampleBuffer,
                    orientation: orientation,
                    options: [:]
                )
                do {
                    try pose3DHandler.perform([pose3DRequest])
                    if let pose3D = try pose3DSample(
                        from: pose3DRequest.results ?? [],
                        timestamp: timestamp
                    ) {
                        poses3D.append(pose3D)
                    }
                } catch {
                    // Keep 2D pose and hand results when 3D pose is unavailable.
                }
                lastPose3DTime = timestamp
            }

            if timestamp - lastOpticalFlowTime >= 1.0,
               let currentBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) {
                if let previousFlowBuffer,
                   let flowSample = opticalFlowSample(
                       from: previousFlowBuffer,
                       to: currentBuffer,
                       timestamp: timestamp,
                       orientation: orientation
                   ) {
                    opticalFlow.append(flowSample)
                    opticalFlowFrames += 1
                }
                previousFlowBuffer = currentBuffer
                lastOpticalFlowTime = timestamp
            }

            let progressValue = min(1, timestamp / durationSeconds)
            let bucket = Int(progressValue * 100) / 2
            if bucket != lastProgressBucket {
                lastProgressBucket = bucket
                progress(progressValue, "Tracking motion and player poses…")
            }
        }

        if reader.status == .failed {
            throw OnDeviceVideoAnalysisError.cannotReadVideo(reader.error?.localizedDescription ?? "Frame decoding failed.")
        }
        guard decodedFrames > 0 else { throw OnDeviceVideoAnalysisError.noFrames }

        let trajectories = trajectoryByID.values.sorted {
            if $0.confidence == $1.confidence { return $0.startTimestampSeconds < $1.startTimestampSeconds }
            return $0.confidence > $1.confidence
        }
        let result = OnDeviceVideoAnalysisResult(
            analyzedDurationSeconds: analyzedDuration,
            sourceWidth: width,
            sourceHeight: height,
            nominalFrameRate: nominalFrameRate,
            decodedFrameCount: decodedFrames,
            trajectoryFrameCount: trajectoryFrames,
            skippedTrajectoryFrameCount: skippedTrajectoryFrames,
            poseFrameCount: poseFrames,
            opticalFlowFrameCount: opticalFlowFrames,
            trajectories: trajectories,
            poses: poses,
            handPoses: handPoses,
            poses3D: poses3D,
            opticalFlow: opticalFlow,
            elapsedSeconds: CFAbsoluteTimeGetCurrent() - started
        )
        progress(1, "Analysis complete")
        return result
    }

    private static func trajectoryInterval(
        observation: VNTrajectoryObservation,
        currentTimestamp: Double,
        nominalFrameRate: Double
    ) -> (start: Double, end: Double) {
        let rangeStart = observation.timeRange.start.seconds
        let rangeEnd = CMTimeRangeGetEnd(observation.timeRange).seconds
        if rangeStart.isFinite, rangeEnd.isFinite, rangeEnd > rangeStart {
            return (max(0, rangeStart), max(rangeStart, rangeEnd))
        }

        // Older or unusual assets can report a zero Vision time range. Use
        // the measured point count as a precise frame-based fallback.
        let frameRate = nominalFrameRate > 0 ? nominalFrameRate : 30
        let pointSpan = Double(max(0, observation.detectedPoints.count - 1)) / frameRate
        return (max(0, currentTimestamp - pointSpan), currentTimestamp)
    }

    private static func makeTrajectoryRequest() -> VNDetectTrajectoriesRequest {
        let request = VNDetectTrajectoriesRequest(
            frameAnalysisSpacing: CMTime(value: 1, timescale: 30),
            trajectoryLength: 5
        )
        request.objectMinimumNormalizedRadius = 0.0005
        request.objectMaximumNormalizedRadius = 0.04
        request.targetFrameTime = CMTime(value: 1, timescale: 30)
        // Ignore thin edge regions where handheld movement and compression
        // artifacts commonly generate large numbers of false candidates.
        request.regionOfInterest = CGRect(x: 0.04, y: 0.06, width: 0.92, height: 0.88)
        return request
    }

    private static func bestPose(
        from observations: [VNHumanBodyPoseObservation],
        timestamp: Double
    ) throws -> VisionPoseDebugSample? {
        var candidates: [(points: [VNHumanBodyPoseObservation.JointName: VNRecognizedPoint], score: Double)] = []
        for observation in observations {
            let points = try observation.recognizedPoints(.all)
            let confident = points.values.filter { $0.confidence >= 0.25 }
            guard !confident.isEmpty else { continue }
            let score = confident.reduce(0.0) { $0 + Double($1.confidence) } / Double(confident.count)
            candidates.append((points, score))
        }
        guard let selected = candidates.max(by: { $0.score < $1.score }) else { return nil }
        let joints = selected.points.reduce(into: [String: VisionDebugPoint]()) { result, entry in
            guard entry.value.confidence >= 0.25 else { return }
            result[String(describing: entry.key)] = VisionDebugPoint(
                x: entry.value.location.x,
                y: entry.value.location.y
            )
        }
        return VisionPoseDebugSample(
            timestampSeconds: timestamp,
            confidence: selected.score,
            joints: joints
        )
    }

    private static func handPoseSamples(
        from observations: [VNHumanHandPoseObservation],
        timestamp: Double
    ) throws -> [VisionHandPoseDebugSample] {
        try observations.compactMap { observation in
            let points = try observation.recognizedPoints(.all)
            let confident = points.filter { $0.value.confidence >= 0.25 }
            guard !confident.isEmpty else { return nil }
            let score = confident.values.reduce(0.0) { $0 + Double($1.confidence) } / Double(confident.count)
            let joints = confident.reduce(into: [String: VisionDebugPoint]()) { result, entry in
                result[String(describing: entry.key)] = VisionDebugPoint(
                    x: entry.value.location.x,
                    y: entry.value.location.y
                )
            }
            return VisionHandPoseDebugSample(
                timestampSeconds: timestamp,
                confidence: score,
                chirality: String(describing: observation.chirality),
                joints: joints
            )
        }
    }

    private static func pose3DSample(
        from observations: [VNHumanBodyPose3DObservation],
        timestamp: Double
    ) throws -> VisionPose3DDebugSample? {
        guard let observation = observations.max(by: { $0.confidence < $1.confidence }) else { return nil }
        let points = try observation.recognizedPoints(.all)
        let joints = points.reduce(into: [String: VisionDebugPoint3D]()) { result, entry in
            let translation = entry.value.position.columns.3
            result[String(describing: entry.key)] = VisionDebugPoint3D(
                x: Double(translation.x),
                y: Double(translation.y),
                z: Double(translation.z)
            )
        }
        guard !joints.isEmpty else { return nil }
        return VisionPose3DDebugSample(
            timestampSeconds: timestamp,
            confidence: Double(observation.confidence),
            bodyHeightMeters: Double(observation.bodyHeight),
            heightWasMeasured: observation.heightEstimation == .measured,
            joints: joints
        )
    }

    private static func opticalFlowSample(
        from previousBuffer: CVPixelBuffer,
        to currentBuffer: CVPixelBuffer,
        timestamp: Double,
        orientation: CGImagePropertyOrientation
    ) -> VisionOpticalFlowDebugSample? {
        let request = VNGenerateOpticalFlowRequest(
            targetedCVPixelBuffer: currentBuffer,
            options: [:]
        )
        request.computationAccuracy = .low
        request.outputPixelFormat = kCVPixelFormatType_TwoComponent32Float
        request.regionOfInterest = CGRect(x: 0.08, y: 0.10, width: 0.84, height: 0.80)
        let handler = VNImageRequestHandler(
            cvPixelBuffer: previousBuffer,
            orientation: orientation,
            options: [:]
        )
        do {
            try handler.perform([request])
            guard let buffer = request.results?.first?.pixelBuffer else { return nil }
            CVPixelBufferLockBaseAddress(buffer, .readOnly)
            defer { CVPixelBufferUnlockBaseAddress(buffer, .readOnly) }
            guard CVPixelBufferGetPixelFormatType(buffer) == kCVPixelFormatType_TwoComponent32Float,
                  let baseAddress = CVPixelBufferGetBaseAddress(buffer) else { return nil }

            let width = CVPixelBufferGetWidth(buffer)
            let height = CVPixelBufferGetHeight(buffer)
            let rowBytes = CVPixelBufferGetBytesPerRow(buffer)
            let step = max(1, min(width, height) / 32)
            var total = 0.0
            var peak = 0.0
            var count = 0
            for y in stride(from: 0, to: height, by: step) {
                let row = baseAddress.advanced(by: y * rowBytes).assumingMemoryBound(to: Float.self)
                for x in stride(from: 0, to: width, by: step) {
                    let dx = Double(row[x * 2])
                    let dy = Double(row[x * 2 + 1])
                    guard dx.isFinite, dy.isFinite else { continue }
                    let magnitude = hypot(dx, dy)
                    total += magnitude
                    peak = max(peak, magnitude)
                    count += 1
                }
            }
            guard count > 0 else { return nil }
            return VisionOpticalFlowDebugSample(
                timestampSeconds: timestamp,
                averageMagnitude: total / Double(count),
                peakMagnitude: peak
            )
        } catch {
            return nil
        }
    }

    private static func orientation(for transform: CGAffineTransform) -> CGImagePropertyOrientation {
        let a = Int(transform.a.rounded())
        let b = Int(transform.b.rounded())
        let c = Int(transform.c.rounded())
        let d = Int(transform.d.rounded())
        switch (a, b, c, d) {
        case (0, 1, -1, 0): return .right
        case (0, -1, 1, 0): return .left
        case (-1, 0, 0, -1): return .down
        default: return .up
        }
    }
}

enum AppleOnDeviceDescriptionError: LocalizedError {
    case requiresNewerOS
    case unavailable(String)

    var errorDescription: String? {
        switch self {
        case .requiresNewerOS:
            "On-device descriptions require iOS 26 or later."
        case .unavailable(let reason):
            "Apple Intelligence is not available: \(reason)."
        }
    }
}

struct AppleOnDeviceDescriptionGenerator {
    static func generate(from result: OnDeviceVideoAnalysisResult) async throws -> String {
#if canImport(FoundationModels)
        if #available(iOS 26.0, *) {
            let model = SystemLanguageModel.default
            guard case .available = model.availability else {
                throw AppleOnDeviceDescriptionError.unavailable(String(describing: model.availability))
            }
            let session = LanguageModelSession(
                model: model,
                instructions: """
                You summarize measured Apple Vision debug results from tennis video. Be concise and factual. Never identify a motion candidate as a tennis ball, never name a stroke, and never diagnose technique unless the input explicitly contains a trained classifier result. Clearly distinguish detections from interpretations.
                """
            )
            let strongestTrajectory = result.trajectories.first
            let prompt = """
                Write a short plain-language description of these on-device measurements:
                analyzed duration: \(result.analyzedDurationSeconds) seconds
                decoded frames: \(result.decodedFrameCount)
                generic parabolic motion candidates: \(result.trajectories.count)
                strongest motion confidence: \(strongestTrajectory?.confidence ?? 0)
                2D body pose samples: \(result.poses.count)
                3D body pose samples: \(result.poses3D.count)
                hand pose samples: \(result.handPoses.count)
                optical-flow samples: \(result.opticalFlow.count)
                average optical-flow magnitude: \(result.averageOpticalFlowMagnitude)
                noisy trajectory frames skipped: \(result.skippedTrajectoryFrameCount)
                Include one recording-quality recommendation only when supported by these measurements.
                """
            let response = try await session.respond(to: prompt)
            return response.content
        }
#endif
        throw AppleOnDeviceDescriptionError.requiresNewerOS
    }
}

struct VideoAnalysisDebugView: View {
    @EnvironmentObject private var store: PlayerStore
    let session: LocalSession

    @State private var limitSeconds = 30
    @State private var running = false
    @State private var progress = 0.0
    @State private var stage = "Ready"
    @State private var result: OnDeviceVideoAnalysisResult?
    @State private var message = ""
    @State private var generatedDescription = ""
    @State private var generatingDescription = false
    @State private var analysisTask: Task<Void, Never>?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                Text("Apple Vision debug").font(.largeTitle.bold())
                Text("Runs trajectory, optical-flow, 2D/3D body-pose, and hand-pose analysis directly on this device. No video frames leave the phone.")
                    .foregroundStyle(AceTheme.muted)

                Card {
                    VStack(alignment: .leading, spacing: 14) {
                        Picker("Clip length", selection: $limitSeconds) {
                            Text("15 sec").tag(15)
                            Text("30 sec").tag(30)
                            Text("60 sec").tag(60)
                        }
                        .pickerStyle(.segmented)
                        .disabled(running)

                        if running {
                            ProgressView(value: progress).tint(AceTheme.forest)
                            Text(stage).font(.subheadline.weight(.semibold))
                            Button("Cancel analysis", role: .cancel) { analysisTask?.cancel() }
                        } else {
                            Button { runAnalysis() } label: {
                                Label(result == nil ? "Run on-device analysis" : "Run again", systemImage: "waveform.path.ecg.rectangle")
                            }
                            .modifier(PrimaryAction())
                        }
                    }
                }

                if !message.isEmpty {
                    Text(message).foregroundStyle(.red).font(.subheadline)
                }

                if let result {
                    resultSummary(result)
                    descriptionCard(result)
                    if let warning = result.trajectoryWarning {
                        Label(warning, systemImage: "exclamationmark.triangle.fill")
                            .font(.subheadline)
                            .foregroundStyle(.orange)
                    }
                    VisionDebugPlot(result: result)

                    Text("Motion candidates").font(.title2.bold())
                    Text("Vision detects parabolic motion, not object identity. These tracks are debugging candidates and are not yet verified tennis-ball observations.")
                        .font(.caption).foregroundStyle(AceTheme.muted)
                    if result.trajectories.isEmpty {
                        ContentUnavailableView("No trajectories found", systemImage: "scope", description: Text("Try a stable 1080p clip where the ball is visible for several consecutive frames."))
                    } else {
                        ForEach(result.trajectories.prefix(20)) { trajectory in
                            NavigationLink {
                                LocalPlayback(
                                    session: session,
                                    startSeconds: trajectory.startTimestampSeconds,
                                    endSeconds: trajectory.endTimestampSeconds
                                )
                            } label: {
                                Card {
                                    HStack {
                                        VStack(alignment: .leading, spacing: 5) {
                                            Text("\(videoTime(trajectory.startTimestampSeconds)) – \(videoTime(trajectory.endTimestampSeconds))")
                                                .font(.headline).monospacedDigit()
                                            Text("\(trajectory.detectedPoints.count) measured points · \((trajectory.endTimestampSeconds - trajectory.startTimestampSeconds).formatted(.number.precision(.fractionLength(2)))) sec · radius \(trajectory.radius.formatted(.number.precision(.fractionLength(4))))")
                                                .font(.caption).foregroundStyle(AceTheme.muted)
                                        }
                                        Spacer()
                                        Text(trajectory.confidence, format: .percent.precision(.fractionLength(0)))
                                            .font(.subheadline.bold()).foregroundStyle(AceTheme.forest)
                                        Image(systemName: "chevron.right").font(.caption)
                                    }
                                }
                            }
                            .buttonStyle(.plain)
                        }
                    }

                    Text("Pose samples").font(.title2.bold())
                    if result.poses.isEmpty {
                        ContentUnavailableView("No player poses found", systemImage: "figure.stand", description: Text("Players may be too small, obscured, or outside the analyzed segment."))
                    } else {
                        ForEach(result.poses.suffix(20)) { pose in
                            NavigationLink {
                                LocalPlayback(
                                    session: session,
                                    startSeconds: pose.timestampSeconds,
                                    endSeconds: nil,
                                    autoplay: false
                                )
                            } label: {
                                Card {
                                    HStack {
                                        VStack(alignment: .leading, spacing: 5) {
                                            Text("Pose at \(videoTime(pose.timestampSeconds))").font(.headline)
                                            Text("\(pose.joints.count) confident joints").font(.caption).foregroundStyle(AceTheme.muted)
                                        }
                                        Spacer()
                                        Text(pose.confidence, format: .percent.precision(.fractionLength(0)))
                                            .font(.subheadline.bold()).foregroundStyle(AceTheme.forest)
                                        Image(systemName: "chevron.right").font(.caption)
                                    }
                                }
                            }
                            .buttonStyle(.plain)
                        }
                    }

                    Text("3D pose samples").font(.title2.bold())
                    if result.poses3D.isEmpty {
                        Text("No 3D body pose was detected. The player may be too small or obscured.")
                            .font(.caption).foregroundStyle(AceTheme.muted)
                    } else {
                        ForEach(result.poses3D.suffix(10)) { pose in
                            exactFrameLink(
                                timestamp: pose.timestampSeconds,
                                title: "3D pose at \(videoTime(pose.timestampSeconds))",
                                detail: "\(pose.joints.count) joints · \(pose.heightWasMeasured ? "measured" : "reference") height \(pose.bodyHeightMeters.formatted(.number.precision(.fractionLength(2)))) m",
                                confidence: pose.confidence
                            )
                        }
                    }

                    Text("Hand pose samples").font(.title2.bold())
                    if result.handPoses.isEmpty {
                        Text("No hands were large and clear enough for Apple Vision.")
                            .font(.caption).foregroundStyle(AceTheme.muted)
                    } else {
                        ForEach(result.handPoses.suffix(10)) { hand in
                            exactFrameLink(
                                timestamp: hand.timestampSeconds,
                                title: "Hand at \(videoTime(hand.timestampSeconds))",
                                detail: "\(hand.chirality) · \(hand.joints.count) joints",
                                confidence: hand.confidence
                            )
                        }
                    }

                    Text("Camera and scene motion").font(.title2.bold())
                    Text("Optical flow measures overall pixel motion. Large values can indicate camera movement as well as player or background movement.")
                        .font(.caption).foregroundStyle(AceTheme.muted)
                    ForEach(result.opticalFlow.sorted(by: { $0.averageMagnitude > $1.averageMagnitude }).prefix(10)) { flow in
                        exactFrameLink(
                            timestamp: flow.timestampSeconds,
                            title: "Flow at \(videoTime(flow.timestampSeconds))",
                            detail: "average \(flow.averageMagnitude.formatted(.number.precision(.fractionLength(2)))) · peak \(flow.peakMagnitude.formatted(.number.precision(.fractionLength(2))))",
                            confidence: nil
                        )
                    }
                }
            }
            .padding(22)
        }
        .background(AceTheme.cream)
        .navigationTitle("Vision debug")
        .navigationBarTitleDisplayMode(.inline)
        .onDisappear { analysisTask?.cancel() }
    }

    @ViewBuilder private func resultSummary(_ result: OnDeviceVideoAnalysisResult) -> some View {
        Text("Run summary").font(.title2.bold())
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
            debugMetric("\(result.trajectories.count)", "Motion tracks", "scope")
            debugMetric("\(result.poses.count)", "2D poses", "figure.stand")
            debugMetric("\(result.poses3D.count)", "3D poses", "rotate.3d")
            debugMetric("\(result.handPoses.count)", "Hand poses", "hand.raised")
            debugMetric("\(result.opticalFlow.count)", "Flow samples", "wind")
            debugMetric("\(result.decodedFrameCount)", "Decoded frames", "film.stack")
            debugMetric(result.elapsedSeconds.formatted(.number.precision(.fractionLength(1))) + "s", "Processing time", "timer")
        }
        Text("Analyzed \(videoTime(result.analyzedDurationSeconds)) · \(result.sourceWidth)×\(result.sourceHeight) · \(result.nominalFrameRate.formatted(.number.precision(.fractionLength(1)))) fps source · pose sampled on \(result.poseFrameCount) frames")
            .font(.caption).foregroundStyle(AceTheme.muted)
        if result.skippedTrajectoryFrameCount > 0 {
            Text("Trajectory tracker processed \(result.trajectoryFrameCount) frames and skipped \(result.skippedTrajectoryFrameCount) noisy frames.")
                .font(.caption).foregroundStyle(AceTheme.muted)
        }
    }

    @ViewBuilder private func descriptionCard(_ result: OnDeviceVideoAnalysisResult) -> some View {
        Card {
            VStack(alignment: .leading, spacing: 10) {
                Label("On-device description", systemImage: "apple.intelligence")
                    .font(.headline)
                if generatedDescription.isEmpty {
                    Text("Apple Intelligence can summarize the measured results. It does not inspect the raw video or invent tennis labels.")
                        .font(.caption).foregroundStyle(AceTheme.muted)
                } else {
                    Text(generatedDescription).font(.subheadline)
                }
                Button {
                    generateDescription(for: result)
                } label: {
                    if generatingDescription {
                        HStack { ProgressView(); Text("Generating on device…") }
                    } else {
                        Label(generatedDescription.isEmpty ? "Generate description" : "Generate again", systemImage: "sparkles")
                    }
                }
                .disabled(generatingDescription)
            }
        }
    }

    private func exactFrameLink(
        timestamp: Double,
        title: String,
        detail: String,
        confidence: Double?
    ) -> some View {
        NavigationLink {
            LocalPlayback(
                session: session,
                startSeconds: timestamp,
                endSeconds: nil,
                autoplay: false
            )
        } label: {
            Card {
                HStack {
                    VStack(alignment: .leading, spacing: 5) {
                        Text(title).font(.headline).monospacedDigit()
                        Text(detail).font(.caption).foregroundStyle(AceTheme.muted)
                    }
                    Spacer()
                    if let confidence {
                        Text(confidence, format: .percent.precision(.fractionLength(0)))
                            .font(.subheadline.bold()).foregroundStyle(AceTheme.forest)
                    }
                    Image(systemName: "chevron.right").font(.caption)
                }
            }
        }
        .buttonStyle(.plain)
    }

    private func debugMetric(_ value: String, _ label: String, _ icon: String) -> some View {
        Card {
            VStack(alignment: .leading, spacing: 7) {
                Image(systemName: icon).foregroundStyle(AceTheme.forest)
                Text(value).font(.title2.bold())
                Text(label).font(.caption).foregroundStyle(AceTheme.muted)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func runAnalysis() {
        analysisTask?.cancel()
        running = true
        progress = 0
        stage = "Preparing video…"
        message = ""
        generatedDescription = ""
        result = nil
        let url = store.url(for: session)
        let limit = Double(limitSeconds)
        analysisTask = Task {
            do {
                let output = try await OnDeviceVideoAnalyzer().analyze(
                    url: url,
                    maximumDurationSeconds: limit
                ) { value, newStage in
                    Task { @MainActor in
                        progress = value
                        stage = newStage
                    }
                }
                try Task.checkCancellation()
                result = output
                stage = "Analysis complete"
                progress = 1
            } catch is CancellationError {
                stage = "Cancelled"
            } catch {
                message = error.localizedDescription
                stage = "Analysis failed"
            }
            running = false
        }
    }

    private func generateDescription(for result: OnDeviceVideoAnalysisResult) {
        generatingDescription = true
        message = ""
        Task {
            do {
                generatedDescription = try await AppleOnDeviceDescriptionGenerator.generate(from: result)
            } catch {
                message = error.localizedDescription
            }
            generatingDescription = false
        }
    }
}

private struct VisionDebugPlot: View {
    let result: OnDeviceVideoAnalysisResult

    var body: some View {
        Card {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Text("Normalized detections").font(.headline)
                    Spacer()
                    Label("motion", systemImage: "circle.fill").foregroundStyle(.yellow)
                    Label("pose", systemImage: "circle.fill").foregroundStyle(AceTheme.lime)
                }
                .font(.caption)

                ZStack {
                    CourtArtwork()
                    Canvas { context, size in
                        if let trajectory = result.trajectories.first {
                            var path = Path()
                            for (index, point) in trajectory.detectedPoints.enumerated() {
                                let canvasPoint = CGPoint(x: point.x * size.width, y: (1 - point.y) * size.height)
                                if index == 0 { path.move(to: canvasPoint) } else { path.addLine(to: canvasPoint) }
                                context.fill(Path(ellipseIn: CGRect(x: canvasPoint.x - 3, y: canvasPoint.y - 3, width: 6, height: 6)), with: .color(.yellow))
                            }
                            context.stroke(path, with: .color(.yellow), lineWidth: 2)
                        }
                        if let pose = result.poses.last {
                            for point in pose.joints.values {
                                let canvasPoint = CGPoint(x: point.x * size.width, y: (1 - point.y) * size.height)
                                context.fill(Path(ellipseIn: CGRect(x: canvasPoint.x - 3, y: canvasPoint.y - 3, width: 6, height: 6)), with: .color(AceTheme.lime))
                            }
                        }
                    }
                }
                .frame(height: 260)
                .clipShape(RoundedRectangle(cornerRadius: 18))
                Text("Shows the highest-confidence motion track and the most recent detected pose in Vision-normalized image coordinates.")
                    .font(.caption).foregroundStyle(AceTheme.muted)
            }
        }
    }
}
