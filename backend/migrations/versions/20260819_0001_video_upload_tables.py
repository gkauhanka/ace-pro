"""Create video upload tables.

Revision ID: 20260819_0001
Revises:
Create Date: 2026-08-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260819_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "videos",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=1024), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("container", sa.String(length=16), nullable=False),
        sa.Column("codec", sa.String(length=32), nullable=False),
        sa.Column("declared_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("declared_duration_seconds", sa.Integer(), nullable=False),
        sa.Column("final_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("bucket", sa.String(length=255), nullable=False),
        sa.Column("object_key", sa.String(length=1024), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("storage_path", sa.String(length=2048), nullable=True),
        sa.Column("playback_url", sa.String(length=2048), nullable=True),
        sa.Column("failure_code", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("object_key"),
    )
    op.create_index("ix_videos_owner_id", "videos", ["owner_id"])
    op.create_index("ix_videos_owner_status", "videos", ["owner_id", "status"])
    op.create_table(
        "upload_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("video_id", sa.String(length=36), nullable=False),
        sa.Column("multipart_upload_id", sa.String(length=1024), nullable=False),
        sa.Column("source_fingerprint", sa.String(length=512), nullable=False),
        sa.Column("part_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("multipart_upload_id"),
        sa.UniqueConstraint("video_id"),
    )
    op.create_index("ix_upload_sessions_expires_at", "upload_sessions", ["expires_at"])
    op.create_index("ix_upload_sessions_video_id", "upload_sessions", ["video_id"])
    op.create_table(
        "upload_parts",
        sa.Column("upload_id", sa.String(length=36), nullable=False),
        sa.Column("part_number", sa.Integer(), nullable=False),
        sa.Column("etag", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("checksum", sa.String(length=255), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["upload_id"], ["upload_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("upload_id", "part_number"),
    )


def downgrade() -> None:
    op.drop_table("upload_parts")
    op.drop_index("ix_upload_sessions_video_id", table_name="upload_sessions")
    op.drop_index("ix_upload_sessions_expires_at", table_name="upload_sessions")
    op.drop_table("upload_sessions")
    op.drop_index("ix_videos_owner_status", table_name="videos")
    op.drop_index("ix_videos_owner_id", table_name="videos")
    op.drop_table("videos")
