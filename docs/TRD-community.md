# TRD：社区读写

版本 0.1 · 2026-09-19

点赞、收藏、评论、专题存 PostgreSQL 表，不使用 Redis。见前端 [PRD](../../techmind-web/docs/PRD-community.md)。

## 表

| 表 | 主键 | 说明 |
|----|------|------|
| `article_likes` | `(user_id, article_id)` | 点赞关系 |
| `favorites` | `(user_id, article_id)` | `folder` 夹名，默认「默认」 |
| `comments` | `id` | `content` 最长 500 |
| `topics` | `id` | `title` / `summary` / `owner_id` |
| `topic_articles` | `(topic_id, article_id)` | 仅允许挂已发布文章 |

迁移：`0004_community`。

## 接口

均需登录 Cookie。雪花 id 在 JSON 里是字符串。

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET /api/articles` | `author_id`、`column_name` 可选 | 已发布筛选 |
| `PUT/DELETE /api/articles/{id}/like` | | 点赞 / 取消，返回 `like_count` `liked` `favorited` `favorite_folder` |
| `PUT/DELETE /api/articles/{id}/favorite` | body `{ folder }` | 收藏或改夹 / 取消 |
| `GET/POST /api/articles/{id}/comments` | | 列表 / 发表 |
| `DELETE /api/articles/{id}/comments/{comment_id}` | | 仅评论作者 |
| `GET /api/favorites` | `folder` 可选 | 收藏及夹名列表 |
| `GET/POST /api/topics` | | 列表 / 创建 |
| `GET/PATCH/DELETE /api/topics/{id}` | | 详情 / 更新 / 删除（仅创建者可改删） |
| `PUT /api/topics/{id}/articles` | `{ article_ids: string[] }` | 替换挂载 |
| `PATCH /api/users/me` | `username` `bio` `role` `tags` | 资料 |
| `POST /api/users/me/password` | `old_password` `new_password` | 改密码 |
| `GET /api/users/{id}` | | 公开资料，不含邮箱 |

文章详情 `ArticleVO` 附带 `like_count`、`liked`、`favorited`、`favorite_folder`。

点赞、收藏、评论只针对 `published`。`allow_comment = false` 时不能新发评论。
