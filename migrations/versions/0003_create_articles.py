"""create articles table

Revision ID: 0003_create_articles
Revises: 0002_add_user_theme
Create Date: 2026-08-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_create_articles"
down_revision: Union[str, None] = "0002_add_user_theme"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "articles",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=200), server_default="", nullable=False),
        sa.Column("subtitle", sa.String(length=200), server_default="", nullable=False),
        sa.Column("summary", sa.String(length=500), server_default="", nullable=False),
        sa.Column("content_md", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "tags",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=32), server_default="后端", nullable=False),
        sa.Column("column_name", sa.String(length=120), server_default="", nullable=False),
        sa.Column("cover_url", sa.String(length=512), server_default="", nullable=False),
        sa.Column("status", sa.String(length=16), server_default="draft", nullable=False),
        sa.Column("review_status", sa.String(length=16), server_default="none", nullable=False),
        sa.Column("allow_comment", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="ck_articles_status",
        ),
        sa.CheckConstraint(
            "review_status IN ('none', 'pending', 'approved', 'rejected')",
            name="ck_articles_review",
        ),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_articles_author_status",
        "articles",
        ["author_id", "status", "updated_at"],
        unique=False,
    )
    op.create_index(
        "idx_articles_status_published",
        "articles",
        ["status", "published_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_articles_status_published", table_name="articles")
    op.drop_index("idx_articles_author_status", table_name="articles")
    op.drop_table("articles")
