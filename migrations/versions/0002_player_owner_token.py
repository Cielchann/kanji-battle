"""add player owner token

Revision ID: 0002_player_owner_token
Revises: 0001_initial
Create Date: 2026-07-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_player_owner_token"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "player_profiles",
        sa.Column("owner_token", sa.String(length=128), nullable=True),
    )
    op.create_index(
        "ix_player_profiles_owner_token",
        "player_profiles",
        ["owner_token"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_player_profiles_owner_token", table_name="player_profiles")
    op.drop_column("player_profiles", "owner_token")
