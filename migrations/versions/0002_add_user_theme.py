"""add users.theme

Revision ID: 0002_add_user_theme
Revises: 0001_create_users
Create Date: 2026-08-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_add_user_theme"
down_revision: Union[str, None] = "0001_create_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 账号主题偏好：light / dark，默认 light
    op.add_column(
        "users",
        sa.Column("theme", sa.String(length=16), server_default="light", nullable=False),
    )
    op.create_check_constraint(
        "ck_users_theme",
        "users",
        "theme IN ('light', 'dark')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_theme", "users", type_="check")
    op.drop_column("users", "theme")
