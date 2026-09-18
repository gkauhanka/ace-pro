from enum import StrEnum


class VideoStatus(StrEnum):
    PENDING = "pending"
    UPLOADING = "uploading"
    PAUSED = "paused"
    COMPLETING = "completing"
    READY = "ready"
    EXPIRED = "expired"
    ABORTED = "aborted"
    FAILED = "failed"
    DELETING = "deleting"
    DELETED = "deleted"


class UploadStatus(StrEnum):
    PENDING = "pending"
    UPLOADING = "uploading"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    EXPIRED = "expired"
    ABORTED = "aborted"
    FAILED = "failed"


class AnalysisStatus(StrEnum):
    INSPECTING = "inspecting"
    AWAITING_ANNOTATIONS = "awaiting_annotations"
    GENERATING_CLIPS = "generating_clips"
    READY = "ready"
    FAILED = "failed"


class ClipStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"
