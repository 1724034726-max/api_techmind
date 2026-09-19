# 专题
from sqlalchemy.orm import Session

from app.core.constants import ArticleStatus
from app.core.error_codes import ErrorCode
from app.core.exceptions import exception
from app.core.sensitive import find_sensitive
from app.core.snowflake import next_id
from app.models.topic import Topic
from app.models.user import User
from app.repositories import article_repo, topic_repo
from app.schemas.article import ArticleListItemVO
from app.schemas.topic import TopicDetailVO, TopicListVO, TopicVO


def _check_text(title: str, summary: str) -> None:
    # 标题与简介敏感词
    for text in (title, summary):
        hit = find_sensitive(text or "")
        if hit is not None:
            raise exception(ErrorCode.ERR_SENSITIVE_WORD, http_status=400, detail={"word": hit})


def _owned(db: Session, user: User, topic_id: int) -> Topic:
    # 仅创建者可改
    topic = topic_repo.get(db, topic_id)
    if not topic or topic.owner_id != user.id:
        raise exception(ErrorCode.ERR_TOPIC_NOT_FOUND, http_status=404)
    return topic


def _detail(db: Session, topic: Topic) -> TopicDetailVO:
    rows = topic_repo.list_articles(db, topic.id)
    articles = [
        ArticleListItemVO.model_validate(article).model_copy(update={"author_name": name})
        for article, name in rows
    ]
    return TopicDetailVO.model_validate(topic).model_copy(update={"articles": articles})


def list_topics(db: Session, limit: int, offset: int) -> TopicListVO:
    # 专题列表
    items, total = topic_repo.list_topics(db, limit, offset)
    return TopicListVO(items=[TopicVO.model_validate(item) for item in items], total=total)


def get_topic(db: Session, topic_id: int) -> TopicDetailVO:
    # 专题详情
    topic = topic_repo.get(db, topic_id)
    if not topic:
        raise exception(ErrorCode.ERR_TOPIC_NOT_FOUND, http_status=404)
    return _detail(db, topic)


def create_topic(db: Session, user: User, title: str, summary: str) -> TopicDetailVO:
    # 创建专题
    _check_text(title, summary)
    topic = topic_repo.create(
        db, Topic(id=next_id(), owner_id=user.id, title=title, summary=summary)
    )
    db.commit()
    db.refresh(topic)
    return _detail(db, topic)


def update_topic(db: Session, user: User, topic_id: int, data: dict) -> TopicDetailVO:
    # 更新标题或简介
    topic = _owned(db, user, topic_id)
    if "title" in data and data["title"] is not None:
        topic.title = data["title"]
    if "summary" in data and data["summary"] is not None:
        topic.summary = data["summary"]
    _check_text(topic.title, topic.summary)
    topic_repo.touch(db, topic)
    db.commit()
    db.refresh(topic)
    return _detail(db, topic)


def delete_topic(db: Session, user: User, topic_id: int) -> None:
    # 删除专题
    topic = _owned(db, user, topic_id)
    topic_repo.delete(db, topic)
    db.commit()


def set_articles(db: Session, user: User, topic_id: int, article_ids: list[str]) -> TopicDetailVO:
    # 替换挂载的已发布文章
    topic = _owned(db, user, topic_id)
    ids: list[int] = []
    for raw in article_ids:
        article_id = int(raw)
        article = article_repo.get_by_id(db, article_id)
        if not article or article.status != ArticleStatus.PUBLISHED.value:
            raise exception(ErrorCode.ERR_ARTICLE_NOT_FOUND, http_status=404)
        if article_id not in ids:
            ids.append(article_id)
    topic_repo.replace_articles(db, topic.id, ids)
    topic_repo.touch(db, topic)
    db.commit()
    db.refresh(topic)
    return _detail(db, topic)
