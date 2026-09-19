# 专题数据访问
from datetime import datetime, timezone

from sqlalchemy import delete as sa_delete, func, select
from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.topic import Topic, TopicArticle
from app.models.user import User


def get(db: Session, topic_id: int) -> Topic | None:
    # 按主键查询
    return db.get(Topic, topic_id)


def create(db: Session, topic: Topic) -> Topic:
    # 插入专题
    db.add(topic)
    db.flush()
    return topic


def touch(db: Session, topic: Topic) -> Topic:
    # 刷新更新时间
    topic.updated_at = datetime.now(timezone.utc)
    db.flush()
    return topic


def delete(db: Session, topic: Topic) -> None:
    # 删除专题及其挂载
    db.execute(sa_delete(TopicArticle).where(TopicArticle.topic_id == topic.id))
    db.delete(topic)
    db.flush()


def list_topics(db: Session, limit: int, offset: int) -> tuple[list[Topic], int]:
    # 专题列表
    total = int(db.scalar(select(func.count()).select_from(Topic)) or 0)
    stmt = select(Topic).order_by(Topic.updated_at.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt).all()), total


def replace_articles(db: Session, topic_id: int, article_ids: list[int]) -> None:
    # 用新列表替换挂载
    db.execute(sa_delete(TopicArticle).where(TopicArticle.topic_id == topic_id))
    for article_id in article_ids:
        db.add(TopicArticle(topic_id=topic_id, article_id=article_id))
    db.flush()


def list_articles(db: Session, topic_id: int) -> list[tuple[Article, str]]:
    # 专题下已发布文章
    stmt = (
        select(Article, User.username)
        .join(TopicArticle, TopicArticle.article_id == Article.id)
        .join(User, User.id == Article.author_id)
        .where(TopicArticle.topic_id == topic_id, Article.status == "published")
        .order_by(Article.published_at.desc().nulls_last())
    )
    rows = list(db.execute(stmt).all())
    return [(row[0], row[1]) for row in rows]
