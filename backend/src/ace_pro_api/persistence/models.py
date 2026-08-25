from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from ace_pro_api.domain.enums import UploadStatus, VideoStatus


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
