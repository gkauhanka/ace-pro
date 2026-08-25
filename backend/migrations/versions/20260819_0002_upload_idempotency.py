"""Add upload creation idempotency key.

Revision ID: 20260819_0002
Revises: 20260819_0001
Create Date: 2026-08-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260819_0002"
down_revision: str | None = "20260819_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "upload_sessions",
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
    )
    op.create_unique_constraint(
        "uq_upload_sessions_idempotency_key",
        "upload_sessions",
        ["idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_upload_sessions_idempotency_key",
        "upload_sessions",
        type_="unique",
    )
    op.drop_column("upload_sessions", "idempotency_key")

