"""likes favorites comments topics

Revision ID: 0004_community
Revises: 0003_create_articles
Create Date: 2026-09-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_community"
down_revision: Union[str, None] = "0003_create_articles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "article_likes",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("article_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"]),
        sa.PrimaryKeyConstraint("user_id", "article_id"),
    )
    op.create_index("idx_article_likes_article", "article_likes", ["article_id"])
    op.create_table(
        "favorites",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("article_id", sa.BigInteger(), nullable=False),
        sa.Column("folder", sa.String(length=32), server_default="默认", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"]),
        sa.PrimaryKeyConstraint("user_id", "article_id"),
    )
    op.create_index("idx_favorites_user_folder", "favorites", ["user_id", "folder"])
    op.create_table(
        "comments",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("article_id", sa.BigInteger(), nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.Column("content", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"]),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_comments_article_created", "comments", ["article_id", "created_at"])
    op.create_table(
        "topics",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=80), nullable=False),
        sa.Column("summary", sa.String(length=300), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "topic_articles",
        sa.Column("topic_id", sa.BigInteger(), nullable=False),
        sa.Column("article_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"]),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"]),
        sa.PrimaryKeyConstraint("topic_id", "article_id"),
    )


def downgrade() -> None:
    op.drop_table("topic_articles")
    op.drop_table("topics")
    op.drop_index("idx_comments_article_created", table_name="comments")
    op.drop_table("comments")
    op.drop_index("idx_favorites_user_folder", table_name="favorites")
    op.drop_table("favorites")
    op.drop_index("idx_article_likes_article", table_name="article_likes")
    op.drop_table("article_likes")
