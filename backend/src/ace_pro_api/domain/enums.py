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
