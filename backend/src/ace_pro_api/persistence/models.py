from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from ace_pro_api.domain.enums import AnalysisStatus, ClipStatus, UploadStatus, VideoStatus


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(255), index=True)
    original_filename: Mapped[str] = mapped_column(String(1024))
    content_type: Mapped[str] = mapped_column(String(255))
    container: Mapped[str] = mapped_column(String(16))
    codec: Mapped[str] = mapped_column(String(32))
    declared_size_bytes: Mapped[int] = mapped_column(BigInteger)
    declared_duration_seconds: Mapped[int] = mapped_column(Integer)
    final_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    bucket: Mapped[str] = mapped_column(String(255))
    object_key: Mapped[str] = mapped_column(String(1024), unique=True)
    status: Mapped[str] = mapped_column(String(32), default=VideoStatus.PENDING.value)
    storage_path: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    playback_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    upload: Mapped[Optional["UploadSession"]] = relationship(
        back_populates="video", cascade="all, delete-orphan", uselist=False
    )
    analyses: Mapped[list["AnalysisJob"]] = relationship(
        back_populates="video", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_videos_owner_status", "owner_id", "status"),)


class UploadSession(Base):
    __tablename__ = "upload_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    video_id: Mapped[str] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"), unique=True, index=True
    )
    multipart_upload_id: Mapped[str] = mapped_column(String(1024), unique=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    source_fingerprint: Mapped[str] = mapped_column(String(512))
    part_size_bytes: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(32), default=UploadStatus.PENDING.value)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    video: Mapped[Video] = relationship(back_populates="upload")
    parts: Mapped[list["UploadPart"]] = relationship(
        back_populates="upload", cascade="all, delete-orphan"
    )


class UploadPart(Base):
    __tablename__ = "upload_parts"

    upload_id: Mapped[str] = mapped_column(
        ForeignKey("upload_sessions.id", ondelete="CASCADE"), primary_key=True
    )
    part_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    etag: Mapped[str] = mapped_column(String(255))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    checksum: Mapped[str | None] = mapped_column(String(255), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    upload: Mapped[UploadSession] = relationship(back_populates="parts")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    pipeline_version: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(
        String(32), default=AnalysisStatus.INSPECTING.value, index=True
    )
    stage: Mapped[str] = mapped_column(String(64), default="media_inspection")
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    media_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    snapshot_version: Mapped[int] = mapped_column(Integer, default=0)
    failure_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    video: Mapped[Video] = relationship(back_populates="analyses")
    points: Mapped[list["AnalyzedPoint"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    insights: Mapped[list["Insight"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    clips: Mapped[list["EvidenceClip"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("video_id", "pipeline_version", name="uq_analysis_video_pipeline"),
    )


class AnalyzedPoint(Base):
    __tablename__ = "analysis_points"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        ForeignKey("analysis_jobs.id", ondelete="CASCADE"), index=True
    )
    sequence_number: Mapped[int] = mapped_column(Integer)
    start_ms: Mapped[int] = mapped_column(BigInteger)
    end_ms: Mapped[int] = mapped_column(BigInteger)
    winner_role: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    job: Mapped[AnalysisJob] = relationship(back_populates="points")
    events: Mapped[list["AnalysisEvent"]] = relationship(
        back_populates="point", cascade="all, delete-orphan"
    )
    clip: Mapped[Optional["EvidenceClip"]] = relationship(
        back_populates="point", cascade="all, delete-orphan", uselist=False
    )

    __table_args__ = (
        UniqueConstraint("job_id", "sequence_number", name="uq_analysis_point_sequence"),
    )


class AnalysisEvent(Base):
    __tablename__ = "analysis_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    point_id: Mapped[str] = mapped_column(
        ForeignKey("analysis_points.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(64))
    timestamp_ms: Mapped[int] = mapped_column(BigInteger)
    player_role: Mapped[str] = mapped_column(String(32))
    predicted_attributes: Mapped[dict] = mapped_column(JSON)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    model_version: Mapped[str] = mapped_column(String(64), default="manual-1")
    revision: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    point: Mapped[AnalyzedPoint] = relationship(back_populates="events")
    corrections: Mapped[list["EventCorrection"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class EventCorrection(Base):
    __tablename__ = "event_corrections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_id: Mapped[str] = mapped_column(
        ForeignKey("analysis_events.id", ondelete="CASCADE"), index=True
    )
    base_revision: Mapped[int] = mapped_column(Integer)
    corrected_fields: Mapped[dict] = mapped_column(JSON)
    actor_id: Mapped[str] = mapped_column(String(255))
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    event: Mapped[AnalysisEvent] = relationship(back_populates="corrections")


class EvidenceClip(Base):
    __tablename__ = "evidence_clips"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        ForeignKey("analysis_jobs.id", ondelete="CASCADE"), index=True
    )
    point_id: Mapped[str] = mapped_column(
        ForeignKey("analysis_points.id", ondelete="CASCADE"), unique=True, index=True
    )
    start_ms: Mapped[int] = mapped_column(BigInteger)
    end_ms: Mapped[int] = mapped_column(BigInteger)
    object_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    playback_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=ClipStatus.PENDING.value)
    failure_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    job: Mapped[AnalysisJob] = relationship(back_populates="clips")
    point: Mapped[AnalyzedPoint] = relationship(back_populates="clip")


class Insight(Base):
    __tablename__ = "analysis_insights"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        ForeignKey("analysis_jobs.id", ondelete="CASCADE"), index=True
    )
    insight_type: Mapped[str] = mapped_column(String(64))
    rule_version: Mapped[str] = mapped_column(String(64))
    snapshot_version: Mapped[int] = mapped_column(Integer)
    rank: Mapped[int] = mapped_column(Integer, default=1)
    metrics: Mapped[dict] = mapped_column(JSON)
    confidence: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(String(2048))
    evidence_event_ids: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    job: Mapped[AnalysisJob] = relationship(back_populates="insights")
