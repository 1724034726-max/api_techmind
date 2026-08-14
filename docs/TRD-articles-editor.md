# TRD：文章与写作（草稿 / 发布 / 编辑器 AI）— 纯后端

| 项 | 内容 |
|----|------|
| 文档类型 | Technical Requirements Document |
| 范围 | `techmind-api` 文章主数据、作者草稿 CRUD、发布、写作助手 AI（火山方舟：选题/扩写 SSE；润色 JSON） |
| 关联文档 | [TRD-architecture.md](./TRD-architecture.md)；前端 [techmind-web/docs/TRD-frontend-editor.md](../../techmind-web/docs/TRD-frontend-editor.md) |
| 版本 | v0.3 |
| 日期 | 2026-08-14 |
| 状态 | Draft（草稿 CRUD + 写作 AI 双模式已落地；发布未做） |

> 全局响应信封、`ErrorCode`、JWT、雪花 ID、分层约定见架构 TRD。  
> 本文与前端编辑器 TRD 对齐：**正文唯一源格式为 Markdown（`content_md`）**；不存 HTML 为主源。

---

## 1. 目标与边界

### 1.1 目标

1. 作者可创建 / 更新 / 列表 / 删除**自己的草稿**。
2. 作者可**发布**文章：元数据（专栏、分类、标签、封面、导读）+ Markdown 正文；导读为空时**服务端自动生成**。
3. 读者可按 id 拉取**已发布**文章详情（供详情页渲染 MD）。
4. 提供写作助手接口（选题分析 / 扩写 / 导读 / 开头）：**火山方舟 Chat**；选题/扩写为 **SSE**（`delta` → `done` / `error`），导读/开头为 **一次性 JSON**（`ApiResponse`）。
5. 敏感词检测复用 `app/core/sensitive.py`（标题、标签、导读、正文可配置接入）。

### 1.2 非目标（本迭代）

- **发布**（`POST .../publish`）、定时发布、审核流水线
- 向量 Embedding / 语义检索
- 版本历史表、协作编辑、富文本 / MDX
- 专栏 / 分类独立 CRUD 完整化
- 图片上传 OSS

> 当前已实现：**草稿**创建 / 更新 / 我的列表 / 详情 / 删除；**写作 AI** 选题/扩写 SSE + 润色 JSON。

### 1.3 技术前提

与架构 TRD 一致：FastAPI + SQLAlchemy 2 + PostgreSQL + Alembic + JWT Bearer + 雪花 ID。  
LLM：火山方舟 OpenAI 兼容 `chat/completions`（`app/integrations/ark`）。

---

## 2. 总体架构

```
Client (techmind-web /editor)
  │  CRUD /api/articles/*
  │  POST /api/articles/{id}/publish
  │  POST /api/editor/ai/*
  ▼
Controller (articles / editor)
  ▼
Service (article_service / editor_ai_service)
  │  业务规则、空摘要自动生成、敏感词、权限
  ▼
Repository (article_repo) ──► PostgreSQL (articles)
```

| 域 | Controller 前缀 | 说明 |
|----|-----------------|------|
| 文章 | `/api/articles` | 草稿与已发布 CRUD / 发布 / 公开详情 |
| 写作 AI | `/api/editor` | 助手能力，无强制落库 |

---

## 3. 数据库设计

### 3.1 原则

- **一篇文章一行**：草稿与已发布共用 `articles`，用 `status` 区分（避免双写、便于「新开一篇 / 切草稿」迁到服务端）。
- 正文只存 **`content_md`（TEXT）**；不存渲染 HTML。
- 标签用 **JSONB 字符串数组**（与 `users.tags` 一致）。
- 主键雪花 `BIGINT`；对外 JSON **string**。
- `author_id` → `users.id`；作者只能改自己的非公开草稿（已发布后的编辑策略见 §3.5）。

### 3.2 ER 概览

```
users 1 ─── * articles
```

本迭代 **不建**：`article_versions`、`article_tags` 关联表、`publish_jobs`（流水线可后续表）。

### 3.3 表：`articles`

| 列名 | 类型 | 空 | 默认 | 说明 |
|------|------|----|------|------|
| `id` | `BIGINT` | NO | 雪花 | PK |
| `author_id` | `BIGINT` | NO | — | FK → `users.id` |
| `title` | `VARCHAR(200)` | NO | `''` | 标题；草稿允许空，**发布时必填** |
| `subtitle` | `VARCHAR(200)` | NO | `''` | 副标题 |
| `summary` | `VARCHAR(500)` | NO | `''` | 导读摘要；发布时空则服务端生成 |
| `content_md` | `TEXT` | NO | `''` | Markdown 正文 |
| `tags` | `JSONB` | NO | `'[]'` | 标签数组 |
| `category` | `VARCHAR(32)` | NO | `'后端'` | 分类：后端/前端/AI/云原生 等 |
| `column_name` | `VARCHAR(120)` | NO | `''` | 专栏名（过渡；有 columns 表后改 FK） |
| `cover_url` | `VARCHAR(512)` | NO | `''` | 封面 URL |
| `status` | `VARCHAR(16)` | NO | `'draft'` | 见枚举 |
| `review_status` | `VARCHAR(16)` | NO | `'none'` | `none` / `pending` / `approved` / `rejected` |
| `allow_comment` | `BOOLEAN` | NO | `true` | |
| `published_at` | `TIMESTAMPTZ` | YES | `NULL` | 首次发布时间 |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |

**索引**

| 名称 | 类型 | 列 |
|------|------|-----|
| `pk_articles` | PK | `id` |
| `idx_articles_author_status` | BTREE | `(author_id, status, updated_at DESC)` |
| `idx_articles_status_published` | BTREE | `(status, published_at DESC)` | 列表已发布 |

**检查约束**

```sql
CONSTRAINT ck_articles_status CHECK (status IN ('draft', 'published', 'archived'))
CONSTRAINT ck_articles_review CHECK (review_status IN ('none', 'pending', 'approved', 'rejected'))
```

**DDL 草案**

```sql
CREATE TABLE articles (
    id              BIGINT PRIMARY KEY,
    author_id       BIGINT NOT NULL REFERENCES users(id),
    title           VARCHAR(200)  NOT NULL DEFAULT '',
    subtitle        VARCHAR(200)  NOT NULL DEFAULT '',
    summary         VARCHAR(500)  NOT NULL DEFAULT '',
    content_md      TEXT          NOT NULL DEFAULT '',
    tags            JSONB         NOT NULL DEFAULT '[]'::jsonb,
    category        VARCHAR(32)   NOT NULL DEFAULT '后端',
    column_name     VARCHAR(120)  NOT NULL DEFAULT '',
    cover_url       VARCHAR(512)  NOT NULL DEFAULT '',
    status          VARCHAR(16)   NOT NULL DEFAULT 'draft',
    review_status   VARCHAR(16)   NOT NULL DEFAULT 'none',
    allow_comment   BOOLEAN       NOT NULL DEFAULT TRUE,
    published_at    TIMESTAMPTZ   NULL,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT now(),
    CONSTRAINT ck_articles_status CHECK (status IN ('draft', 'published', 'archived')),
    CONSTRAINT ck_articles_review CHECK (review_status IN ('none', 'pending', 'approved', 'rejected'))
);

CREATE INDEX idx_articles_author_status ON articles (author_id, status, updated_at DESC);
CREATE INDEX idx_articles_status_published ON articles (status, published_at DESC);
```

### 3.4 枚举（`app/core/constants.py`）

```python
class ArticleStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class ReviewStatus(str, Enum):
    NONE = "none"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
```

### 3.5 状态流转（本迭代）

```
创建 → draft
draft → publish → published + review_status=pending（或直接 approved，产品二选一，默认 pending）
published → archived（作者下架，可选）
```

- 已发布文章本迭代允许作者 **再编辑并保存**（仍为 `published`，更新 `updated_at`）；若需「编辑后重新审核」另增规则。
- 删除：草稿可硬删；已发布建议 `archived`（或硬删，实现时统一一种并写清）。

---

## 4. 业务规则

### 4.1 权限

| 操作 | 规则 |
|------|------|
| 创建草稿 / 更新草稿 / 发布 / 删草稿 | 需登录；`role` 为 `author` 或 `both`（`reader` → `ERR_FORBIDDEN`） |
| 读自己的草稿列表 / 详情 | 仅 `author_id == current_user.id` |
| 读已发布详情 | 登录与否均可（或仅登录，与产品一致；**默认公开读**） |

### 4.2 发布校验

| 字段 | 规则 |
|------|------|
| `title` | trim 后非空，长度 1–200 |
| `content_md` | 建议非空（可配置最低字数，首版 ≥ 1） |
| `summary` | 可空；**空则服务端生成**（见 §4.3） |
| `tags` | 0–8 个；单项长度限制与注册标签对齐时可复用常量；过敏感词失败 |
| `category` | 枚举白名单 |

### 4.3 导读自动生成

与前端约定一致：

1. 作者可在编辑期手写 / AI 生成 `summary`。
2. `POST .../publish`（或等价）时若 `summary` 空白：服务端根据 `title` + `content_md` 截断/模板生成一条（首版规则化即可，后续可换 LLM）。
3. 生成结果写回 `articles.summary` 再置为已发布。

### 4.4 敏感词

- 发布与更新：至少检测 `title`、`tags`、`summary`；`content_md` 建议同样检测（长文可异步，首版同步命中即失败）。
- 错误码复用 `ERR_SENSITIVE_WORD`（文案可泛化为「内容包含敏感词」）。

### 4.5 Markdown

- 服务端**不负责** MD→HTML；只存原文。
- 可选：字数统计（去空白）作冗余字段，本迭代可不落库，由前端计。

---

## 5. API 设计

统一：`ApiResponse[T]`；需登录接口带 `Authorization: Bearer`。  
id 一律 **string**。

### 5.1 `POST /api/articles`

创建草稿。

**Request**

```json
{
  "title": "",
  "subtitle": "",
  "summary": "",
  "content_md": "",
  "tags": [],
  "category": "后端",
  "column_name": "",
  "cover_url": ""
}
```

字段均可选；缺省按表默认。  
**Response 201**：`ArticleVO`（含 `status: "draft"`）。

### 5.2 `PATCH /api/articles/{id}`

更新草稿或已发布文（仅作者）。  
Body 同创建（全量或部分：建议 **PATCH 可选字段**）。  
**Response 200**：`ArticleVO`。

### 5.3 `GET /api/articles/mine`

当前用户文章列表。

**Query**

| 参数 | 说明 |
|------|------|
| `status` | 可选：`draft` / `published` / `archived` / 不传=全部 |
| `limit` | 默认 20，最大 50 |
| `cursor` | 可选，后续游标；首版可用 `offset` |

**Response 200**：`{ "items": ArticleVO[], "total": number }`（或纯 list，实现时与项目列表风格统一）。

### 5.4 `GET /api/articles/{id}`

- 若 `published`：公开返回。
- 若 `draft` / `archived`：仅作者；否则 `ERR_NOT_FOUND` 或 `ERR_FORBIDDEN`（建议对非作者统一 **NOT_FOUND**，防枚举）。

### 5.5 `POST /api/articles/{id}/publish`

将草稿（或已有文）发布。

**Request**（可与 PATCH 合并元数据，或空 body 表示用当前存盘内容）

```json
{
  "title": "...",
  "subtitle": "...",
  "summary": "",
  "content_md": "...",
  "tags": ["Redis"],
  "category": "后端",
  "column_name": "Spring 源码深度解析",
  "cover_url": "",
  "allow_comment": true
}
```

若带 body：先按 PATCH 合并再发布。  
**处理**：校验 → 敏感词 → 空摘要生成 → `status=published`，`published_at=now()`（若首次），`review_status=pending`。  
**Response 200**：`ArticleVO`。

### 5.6 `DELETE /api/articles/{id}`

- `draft`：硬删。  
- `published`：本迭代改为 `archived`（推荐）或拒绝删除。

### 5.7 写作 AI（`/api/editor`，双模式）

均需登录；**不强制**改文章，由前端决定是否写入编辑器。

| 任务 | 传输 | 说明 |
|------|------|------|
| `topic-analyze` / `expand` | SSE | `delta` 流式 MD + `done` 结构化 VO |
| `summary` / `opening` | JSON | 标准 `ApiResponse`，无 `delta` |

#### SSE（选题 / 扩写）

| 项 | 约定 |
|----|------|
| 协议 | `POST` + `Content-Type: application/json` 请求体；响应 `Content-Type: text/event-stream` |
| 鉴权 | Bearer；鉴权失败时仍可能返回**普通 JSON 信封**（非 SSE），由前端按 `apiFetch` 规则处理 |
| 上游 | 火山方舟 `chat/completions`，`stream: true`；客户端 `app/integrations/ark` |
| 未配置 | 流内 `event: error`，`code=err41200001`（`ERR_AI_NOT_CONFIGURED`）；或启动前校验失败同码 |
| 缓冲 | 响应头建议：`Cache-Control: no-cache`、`Connection: keep-alive`、`X-Accel-Buffering: no` |

| event | data（JSON） | 说明 |
|-------|--------------|------|
| `delta` | `{ "text": "<Markdown 增量>" }` | 模型 token / 片段，可多次 |
| `done` | 对应任务的 VO（见下） | 服务端按约定 MD 结构解析后返回 |
| `error` | `{ "code": "err…", "message": "…" }` | 上游失败 / 解析失败等 |

帧格式：`event: …\ndata: …\n\n`（`app/core/sse.py`）。

#### JSON（导读 / 开头）

| 项 | 约定 |
|----|------|
| 协议 | `POST` + JSON 请求体；响应 `ApiResponse[VO]` |
| 上游 | 方舟非流式 `chat`（或流式聚合后一次返回） |
| 失败 | 全局 JSON 异常 / 业务错误码（同其它 REST） |

#### `POST /api/editor/ai/topic-analyze`

请求：

```json
{ "keyword": "JVM" }
```

流式：`delta` 为模型原始输出增量。  
`done.data`：

```json
{
  "insight": "近 30 天…",
  "angles": [
    {
      "angle": "对比选型",
      "title": "ZGC vs G1：生产环境怎么选",
      "hint": "竞争中等…",
      "outline_md": "## 背景\n\n..."
    }
  ]
}
```

#### `POST /api/editor/ai/expand`

请求：

```json
{ "content_md": "...", "title": "..." }
```

流式：`delta` 为模型输出的 Markdown 增量。  
`done.data`：`{ "appendix_md": "..." }`。若模型仍返回 JSON，返回 `ERR_AI_BAD_RESPONSE`。

#### `POST /api/editor/ai/summary`

请求：

```json
{ "title": "...", "content_md": "..." }
```

响应：`ApiResponse`，`data`：`{ "candidates": [ { "label": "问题导向", "text": "..." } ] }`。

#### `POST /api/editor/ai/opening`

请求：

```json
{ "title": "...", "content_md": "..." }
```

响应：`ApiResponse`，`data`：`{ "candidates": [ { "label": "场景切入", "text": "..." } ] }`。

#### 相关配置

| 变量 | 说明 |
|------|------|
| `ARK_API_KEY` | 方舟密钥；空则 AI 不可用 |
| `ARK_BASE_URL` | 默认 `https://ark.cn-beijing.volces.com` |
| `ARK_CHAT_MODEL` | Chat 模型 id |
| `ARK_CHAT_COMPLETIONS_URL` | 可选；覆盖默认 completions 路径 |

限流：每用户约 **8 次 / 60s**（进程内内存计数，`ERR_AI_RATE_LIMITED`）；客户端断开 SSE 时会 `cancel` 停止方舟拉取。

实现：`editor_ai_service` 固定 system prompt + MD 结构解析；选题/扩写走 SSE；导读/开头同步聚合后解析。

### 5.8 `ArticleVO`（对外）

```json
{
  "id": "1234567890123456789",
  "author_id": "…",
  "author_name": "demo",
  "title": "...",
  "subtitle": "...",
  "summary": "...",
  "content_md": "...",
  "tags": ["Redis"],
  "category": "后端",
  "column_name": "",
  "cover_url": "",
  "status": "draft",
  "review_status": "none",
  "allow_comment": true,
  "published_at": null,
  "created_at": "...",
  "updated_at": "..."
}
```

列表接口可省略 `content_md`（用 `ArticleListItemVO`），详情再带全文。

### 5.9 错误码（建议增补）

| 枚举 | code 建议 | 文案 |
|------|-----------|------|
| `ERR_ARTICLE_NOT_FOUND` | `err31200001` | 文章不存在 |
| `ERR_ARTICLE_TITLE_REQUIRED` | `err31200002` | 发布前请填写标题 |
| `ERR_ARTICLE_CONTENT_REQUIRED` | `err31200003` | 发布前请填写正文 |
| `ERR_ARTICLE_NOT_AUTHOR` | `err31200004` | 无权操作该文章 |
| `ERR_ARTICLE_STATUS` | `err31200005` | 当前状态不允许该操作 |
| `ERR_ARTICLE_SAVE_FAILED` | `err31200006` | 文章保存失败，请稍后重试 |
| `ERR_AI_NOT_CONFIGURED` | `err41200001` | 写作助手未配置，请联系管理员 |
| `ERR_AI_UPSTREAM` | `err41200002` | 写作助手暂时不可用，请稍后重试 |
| `ERR_AI_BAD_RESPONSE` | `err41200003` | 写作助手返回格式异常，请重试 |

通用：`ERR_UNAUTHORIZED` / `ERR_FORBIDDEN` / `ERR_SENSITIVE_WORD` / `ERR_VALIDATION`；  
鉴权另见 `ERR_TOKEN_EXPIRED`（`err21234337`）/ `ERR_TOKEN_INVALID`（`err21234336`）。

> 写作 AI 在 **SSE 已开始** 后的业务失败走 `event: error`（HTTP 多为 200 + 流内错误码）；流开始前的鉴权失败仍走全局 JSON 异常过滤器。

---

## 6. 模块落地

| 层 | 路径 |
|----|------|
| Model | `app/models/article.py` |
| Schema | `app/schemas/article.py`、`app/schemas/editor_ai.py` |
| Repo | `app/repositories/article_repo.py` |
| Service | `app/services/article_service.py`、`app/services/editor_ai_service.py` |
| Controller | `app/controllers/articles.py`、`app/controllers/editor.py` |
| 集成 | `app/integrations/ark/chat.py`（同步 + stream） |
| SSE | `app/core/sse.py` |
| 常量 | `ArticleStatus` / `ReviewStatus` → `constants.py` |
| 迁移 | `migrations/versions/0003_add_articles.py`（序号以仓库现状为准） |

`main.py` 挂载：`/api/articles`、`/api/editor`。

事务：写操作在 Service 内 `commit`；与认证模块同一约定。

---

## 7. 与前端协作要点

| 前端（编辑器 TRD） | 后端 |
|--------------------|------|
| 服务端草稿 | `GET/POST/PATCH/DELETE /api/articles`，`status=draft` |
| 导读空则发布时生成 | **服务端必须再兜底一遍**（防绕过；发布未做） |
| 正文 MD | `content_md` |
| AI | 选题/扩写 SSE → `apiSseFetch`；润色 JSON → `apiFetch` |
| 发布经 Sheet | `POST /api/articles/{id}/publish`（未做） |
| 详情渲染 MD | `GET /api/articles/{id}` → 前端 `react-markdown` |

---

## 8. 验收

| # | 项 |
|---|-----|
| 1 | 迁移后 `articles` 表存在，CHECK / 索引齐全 |
| 2 | 作者可建草稿、更新、列表、删除；读者角色创建失败 |
| 3 | 非作者不可读他人草稿（表现为不存在或无权限） |
| 4 | 发布：无标题失败；无摘要自动生成并落库；`status=published`（待做） |
| 5 | 已发布详情返回 `content_md`；id 为字符串（待发布后） |
| 6 | AI：选题/扩写 SSE；导读/开头一次性 JSON；配置 Key 后可联调方舟 |
| 7 | 敏感词命中返回既有/扩展错误码 |
| 8 | 非流式接口响应均为 `ApiResponse`；SSE 业务失败在流内 `error` |

---

## 9. 实施顺序建议

1. Model + 迁移 + constants / error codes  
2. Repo + Service：草稿 CRUD  
3. `publish` + 空摘要生成 + 敏感词  
4. 公开详情 + mine 列表  
5. `editor` AI：Ark + 选题/扩写 SSE + 润色 JSON  
6. 与 `techmind-web` 联调（草稿已切 API；AI 双模式）  

---

## 10. 开放决策

| 项 | 默认 |
|----|------|
| 发布后 `review_status` | `pending`（Feed 可先只展示 `approved`，或本阶段 `published` 即可见） |
| 已发布是否允许改正文 | 允许（简单）；若要审核回流再改 |
| 专栏 | 先 `column_name` 字符串 |
| 列表是否返回全文 | 否，仅详情 |
| AI 传输模式 | 选题/扩写 SSE；导读/开头一次性 JSON |

修订时同步前端编辑器 TRD。
