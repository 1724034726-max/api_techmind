# TRD：认证模块（登录 / 注册）— 纯后端

| 项 | 内容 |
|----|------|
| 文档类型 | Technical Requirements Document |
| 范围 | `techmind-api` 用户与认证子系统 |
| 关联文档 | [TRD-architecture.md](./TRD-architecture.md)（整体架构与全局约定） |
| 版本 | v0.4 |
| 日期 | 2026-08-12 |
| 状态 | Draft |

---

## 1. 目标与边界

### 1.1 目标

交付可独立联调的认证能力：

1. 用户注册（落库 + 密码哈希）
2. 用户登录（校验 + 签发访问令牌）
3. 基于 Bearer Token 的当前用户解析（`/me`）
4. 与现有基建对齐：统一响应 `ApiResponse`、错误码 `ErrorCode`、全局异常过滤器

### 1.2 非目标

- 任何前端改造、联调排期、页面交互
- 邮箱验证 / 手机验证码 / 忘记密码
- OAuth / 第三方登录
- Refresh Token 轮换与服务端 Token 黑名单
- RBAC 细粒度权限、运营台角色体系
- 关注数真实维护、用户资料编辑接口（可后续扩展）

### 1.3 技术前提

| 项 | 选型 |
|----|------|
| 框架 | FastAPI |
| ORM | SQLAlchemy 2.x |
| DB | PostgreSQL（`DATABASE_URL`） |
| 密码 | bcrypt（或等价库）哈希存储 |
| 会话 | JWT（HS256），无状态 |
| 分层 | Controller → Service → Repository → Model |

---

## 2. 总体架构

```
Client
  │  POST /api/auth/register | login
  │  GET  /api/auth/me   (Authorization: Bearer)
  ▼
Controller (auth)
  │  参数校验 / 调 Service / 包装 ApiResponse
  ▼
Service (auth_service)
  │  业务规则 / 调 Repo / 调 security
  ▼
Repository (user_repo) ──► PostgreSQL (users 等表)
Security (hash / jwt)
Deps (get_db / get_current_user)
Exception → ErrorCode → ApiResponse
```

---

## 3. 数据库设计

### 3.1 设计原则

- 认证核心只落 **用户主表**；标签不单独建关系表（本阶段用 JSONB，降低复杂度）。
- 密码 **只存哈希**，列名 `password_hash`，禁止明文。
- 主键使用 **雪花 ID（Snowflake）**，64 位整型；应用层生成，避免自增暴露规模、利于分布式。
- 时间统一 `timestamptz`；API 序列化对外可用 ISO8601 或毫秒时间戳（实现时在 Schema 层统一，**库内用 timestamptz**）。
- 逻辑删除本阶段不做；注销/禁用用 `status` 预留。

### 3.2 ER 概览（本迭代）

```
┌──────────────────────────────────────────────────────────────┐
│                         users                                │
├──────────────────┬───────────────┬───────────────────────────┤
│ 列               │ 类型          │ 说明                      │
├──────────────────┼───────────────┼───────────────────────────┤
│ PK  id           │ BIGINT        │ 主键（雪花 ID）           │
│ UK  username     │ VARCHAR(32)   │ 用户名（唯一）            │
│ UK  email        │ VARCHAR(255)  │ 邮箱（唯一，入库小写）    │
│     password_hash│ VARCHAR(255)  │ 密码哈希（禁止明文）      │
│     role         │ VARCHAR(16)   │ 身份：读者/作者/两者      │
│     tags         │ JSONB         │ 兴趣标签列表              │
│     bio          │ VARCHAR(160)  │ 个人简介                  │
│     followers_count │ INT        │ 粉丝数（冗余计数）        │
│     following_count │ INT        │ 关注数（冗余计数）        │
│     status       │ VARCHAR(16)   │ 账号状态：正常/禁用       │
│     last_login_at│ TIMESTAMPTZ   │ 最近成功登录时间          │
│     created_at   │ TIMESTAMPTZ   │ 创建时间                  │
│     updated_at   │ TIMESTAMPTZ   │ 最近更新时间              │
└──────────────────┴───────────────┴───────────────────────────┘
```

本迭代 **不建**：

- `sessions` / `refresh_tokens`（JWT 无状态）
- `user_tags` 关联表（`tags` JSONB 足够）
- `roles` / `permissions` 表（`role` 枚举字段足够）

后续若要审计登录、强制下线，可增补 `user_login_logs` 或 `token_blacklist`，不在本 TRD 范围。

### 3.3 表：`users`

**表名**：`users`  
**说明**：平台账号主表，认证与基础资料合一。

| 列名 | 类型 | 空 | 默认 | 约束 / 说明 |
|------|------|----|------|-------------|
| `id` | `BIGINT` | NO | 应用层雪花算法生成 | 主键；非 DB 自增 |
| `username` | `VARCHAR(32)` | NO | — | 唯一；业务长度建议 2–16，列宽预留至 32 |
| `email` | `VARCHAR(255)` | NO | — | 唯一；入库统一小写 |
| `password_hash` | `VARCHAR(255)` | NO | — | bcrypt 哈希 |
| `role` | `VARCHAR(16)` | NO | `'reader'` | 见枚举：`reader` / `author` / `both` |
| `tags` | `JSONB` | NO | `'[]'` | 兴趣标签字符串数组，如 `["Java","Redis"]` |
| `bio` | `VARCHAR(160)` | NO | `''` | 简介；空串允许，业务层可填默认文案 |
| `followers_count` | `INT` | NO | `0` | 粉丝数冗余计数，本阶段只初始化 |
| `following_count` | `INT` | NO | `0` | 关注数冗余计数，本阶段只初始化 |
| `status` | `VARCHAR(16)` | NO | `'active'` | `active` / `disabled`；禁用账号禁止登录 |
| `last_login_at` | `TIMESTAMPTZ` | YES | `NULL` | 最近成功登录时间 |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | 创建时间 |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | 更新时间（应用层或触发器维护） |

**索引**

| 名称 | 类型 | 列 | 说明 |
|------|------|-----|------|
| `pk_users` | PRIMARY KEY | `id` | |
| `uk_users_username` | UNIQUE | `username` | |
| `uk_users_email` | UNIQUE | `email` | |
| `idx_users_status` | BTREE | `status` | 可选，便于运维筛选 |

**检查约束（建议）**

```sql
CONSTRAINT ck_users_role CHECK (role IN ('reader', 'author', 'both'))
CONSTRAINT ck_users_status CHECK (status IN ('active', 'disabled'))
```

**DDL 草案**

```sql
CREATE TABLE users (
    id               BIGINT PRIMARY KEY,
    username         VARCHAR(32)  NOT NULL,
    email            VARCHAR(255) NOT NULL,
    password_hash    VARCHAR(255) NOT NULL,
    role             VARCHAR(16)  NOT NULL DEFAULT 'reader',
    tags             JSONB        NOT NULL DEFAULT '[]'::jsonb,
    bio              VARCHAR(160) NOT NULL DEFAULT '',
    followers_count  INT          NOT NULL DEFAULT 0,
    following_count  INT          NOT NULL DEFAULT 0,
    status           VARCHAR(16)  NOT NULL DEFAULT 'active',
    last_login_at    TIMESTAMPTZ  NULL,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT uk_users_username UNIQUE (username),
    CONSTRAINT uk_users_email UNIQUE (email),
    CONSTRAINT ck_users_role CHECK (role IN ('reader', 'author', 'both')),
    CONSTRAINT ck_users_status CHECK (status IN ('active', 'disabled'))
);

CREATE INDEX idx_users_status ON users (status);
```

> **雪花 ID**：由应用层（如 `app/core/snowflake.py`）在插入前生成并写入 `id`，数据库不使用 `SERIAL`/`IDENTITY`。对外 JSON 建议序列化为 **字符串**，避免 JavaScript 大整数精度丢失。

### 3.4 枚举定义（应用层常量）

与表字段对应，落在 `app/core/constants.py`：

| 常量 | 取值 |
|------|------|
| `UserRole` | `reader`, `author`, `both` |
| `UserStatus` | `active`, `disabled` |

### 3.5 建表策略

| 方案 | 说明 | 建议 |
|------|------|------|
| A. Alembic | `migrations/` 正式版本管理 | **推荐作为正式方案** |
| B. `Base.metadata.create_all` | 仅本地快速拉起 | 可作开发过渡，不替代迁移 |

本 TRD 要求最终以 **Alembic 迁移脚本** 创建 `users` 表为准。

---

## 4. 领域规则

### 4.1 注册

1. 校验入参（长度、邮箱格式、密码 ≥ 8、`role` 枚举、`tags` 至少 1 个）。
2. `email` 规范化为小写后写入；**不做先查再插**，唯一性交给表上 `username` / `email` UNIQUE。
3. 清洗 `tags`（trim、去空串）；对每个标签做**敏感词检测**，命中 → `ERR_SENSITIVE_WORD`（HTTP 400），**不落库**。
4. 对明文密码做哈希，写入 `password_hash`。
5. `bio` 为空时写入默认文案：`这位用户还没有填写简介`。（本阶段 bio 可不做敏感词；后续可复用同一检测模块）
6. `status=active`，计数为 0；主键由雪花算法生成。
7. 落库成功后签发 JWT，返回 token + 用户公开信息（**注册即登录**）。
8. 插入撞唯一约束 → 捕获 `IntegrityError` → `ErrorCode.ERR_ACCOUNT_EXISTS`（HTTP 409）。

### 4.1.1 注册标签敏感词

前端支持自定义标签，后端必须二次校验，不能只信前端。

| 项 | 约定 |
|----|------|
| 算法 | AC 自动机（依赖 `pyahocorasick`） |
| 实现 | `app/core/sensitive.py` |
| 词库 | `data/sensitive_words.txt`（一行一词；`#` 行为注释） |
| 覆盖类别 | 辱骂、歧视、政治敏感、色情、赌博/毒品、暴恐等（词库可运营维护） |
| 策略 | **检测即拒绝**（不打码、不静默丢弃标签） |
| 缓存 | 自动机进程内缓存；**改词库后需重启服务** |
| 调用点 | `auth_service.register`，落库前 |

失败响应示例：

```json
{
  "code": "err21234339",
  "message": "标签包含敏感词，请修改后重试",
  "data": { "word": "赌博" }
}
```

`data.word` 为命中词，便于联调；前端可只展示 `message`。

### 4.2 登录

1. `account` trim 后按 **username 精确匹配或 email 小写匹配** 查用户。
2. 不存在 → `ERR_ACCOUNT_NOT_FOUND`。
3. `status != active` → `ERR_ACCOUNT_DISABLED`。
4. 验密失败 → `ERR_PASSWORD_WRONG`。
5. 成功：更新 `last_login_at`、`updated_at`；按统一过期时间签发 JWT。

### 4.3 Token

**Claims（建议）**

| claim | 含义 |
|-------|------|
| `sub` | `user.id`（雪花 ID，建议 JWT 内用字符串） |
| `username` | 冗余便于日志（可选） |
| `role` | 可选 |
| `iat` / `exp` | 标准时间戳 |

**Header**：`Authorization: Bearer <access_token>`

**过期时间**

| 配置项 | 建议默认 | 说明 |
|--------|----------|------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440`（1 天） | 全站统一；「记住我」由前端/浏览器自行处理，后端不接收、不区分 |

> 「记住我」属于前端与浏览器（如 localStorage / sessionStorage 选型）职责，**不进入登录请求体，不影响 JWT 过期策略**。

### 4.4 当前用户

1. 解析 Bearer；缺失/非法 → `ERR_UNAUTHORIZED` 或 `ERR_TOKEN_INVALID`。
2. 过期 → `ERR_TOKEN_EXPIRED`。
3. 按 `sub` 查库；用户不存在或已禁用 → `ERR_UNAUTHORIZED` / `ERR_FORBIDDEN`。
4. 返回公开用户 VO（`UserVO`）。

### 4.5 事务与并发

FastAPI **不提供**事务；事务由 SQLAlchemy `Session` 管理。`get_db` 按请求创建 Session，异常退出时 `rollback`，结束时 `close`。

#### 分层职责

| 层 | 职责 |
|----|------|
| Repository | `add` / `flush` / 查询；**不** `commit` / `begin` |
| Service | 事务边界与业务异常映射 |
| Controller | 不碰事务 |

#### 写库两种模式

**1. 纯写入（本请求尚未查库）— 注册**

使用 `with db.begin():`：块成功自动 `commit`，块内异常自动 `rollback` 后再抛出。

```python
try:
    with db.begin():
        user_repo.create(db, user)
except IntegrityError as exc:
    raise exception(ErrorCode.ERR_ACCOUNT_EXISTS, http_status=409) from exc
```

**2. 先读后写（前面已 SELECT）— 登录更新 `last_login_at`**

Session 事务已因查询开启，**不可再** `db.begin()`。改字段后显式 `db.commit()`；若 `commit` 失败，由 `get_db` 兜底 `rollback`。

```python
user_repo.update_login_time(db, user)
db.commit()
db.refresh(user)
```

#### 唯一约束与并发

- 防重复账号依赖 PostgreSQL UNIQUE（索引项冲突），不依赖应用层锁，也不依赖先查再插。
- 并发双请求同注册：至多一条成功，另一条 `IntegrityError` → `ERR_ACCOUNT_EXISTS`。
- 禁止将未处理的 `IntegrityError` 漏成 500。

#### 幂等性说明（注册）

| 能力 | 是否具备 |
|------|----------|
| 同一 username/email 不会插入两行 | 是（UNIQUE） |
| 重复提交稳定返回同一次成功结果（同 token） | **否**（本阶段不做） |
| 客户端超时重试：若首次已成功 | 重试得到 `ERR_ACCOUNT_EXISTS`，需前端按「已注册」处理或改走登录 |

本阶段接受「冲突即业务错误」；若后续要强幂等，再引入幂等键 / request_id 或「已存在则直接登录」策略（另开需求）。

---

## 5. API 设计

Base：`/api/auth`  
统一响应：

```json
{ "code": "0", "message": "ok", "data": {} }
```

失败时 `code` 为 `err…`，由全局异常过滤器输出。

### 5.1 `POST /api/auth/register`

**Request**

```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "role": "reader",
  "tags": ["Java"],
  "bio": "string"
}
```

| 字段 | 必填 | 校验 |
|------|------|------|
| username | 是 | 2–16 |
| email | 是 | Email |
| password | 是 | ≥ 8 |
| role | 否 | 默认 `reader` |
| tags | 是* | 至少 1 个；支持自定义；后端敏感词检测，命中失败 |
| bio | 否 | ≤ 80 或 ≤ 160（与列宽一致，建议请求 ≤ 80） |

**Response 201** `data`：

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "1234567890123456789",
    "username": "...",
    "email": "...",
    "role": "reader",
    "tags": [],
    "bio": "...",
    "followers": 0,
    "following": 0,
    "status": "active",
    "created_at": "2026-08-12T08:00:00Z",
    "updated_at": "2026-08-12T08:00:00Z"
  }
}
```

> 对外 DTO 可用 `followers` / `following` 映射库字段 `followers_count` / `following_count`。  
> **禁止**返回 `password` / `password_hash`。

### 5.2 `POST /api/auth/login`

**Request**

```json
{
  "account": "string",
  "password": "string"
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `account` | 是 | 用户名或邮箱 |
| `password` | 是 | 明文密码，仅传输不落库 |

**Response 200**：与注册成功 `data` 结构相同。

### 5.3 `GET /api/auth/me`

Header：`Authorization: Bearer <token>`  
**Response 200**：`data` 为 `user` 对象（无 token 字段）。

### 5.4 错误码（复用 / 建议增补）

| ErrorCode | code | 场景 |
|-----------|------|------|
| `ERR_VALIDATION` | `err10000002` | 入参校验失败 |
| `ERR_UNAUTHORIZED` | `err10000003` | 未带 token / 无法识别身份 |
| `ERR_FORBIDDEN` | `err10000004` | 账号禁用等 |
| `ERR_ACCOUNT_NOT_FOUND` | `err21234333` | 登录账号不存在 |
| `ERR_PASSWORD_WRONG` | `err21234334` | 密码错误 |
| `ERR_ACCOUNT_EXISTS` | `err21234335` | 注册冲突 |
| `ERR_TOKEN_INVALID` | `err21234336` | token 非法 |
| `ERR_TOKEN_EXPIRED` | `err21234337` | token 过期 |
| `ERR_ACCOUNT_DISABLED` | `err21234338` | 账号已禁用 |
| `ERR_SENSITIVE_WORD` | `err21234339` | 标签含敏感词 |

业务层统一：`raise exception(ErrorCode.XXX)`。

---

## 6. 模块落地清单

| 层级 | 文件 | 内容 |
|------|------|------|
| 常量 | `app/core/constants.py` | `UserRole` / `UserStatus` |
| 安全 | `app/core/security.py` | hash / verify / create_token / decode_token |
| 敏感词 | `app/core/sensitive.py` | AC 自动机检测；`first_sensitive_in_tags` |
| 词库 | `data/sensitive_words.txt` | 敏感词列表（运营可维护） |
| 雪花 | `app/core/snowflake.py` | 雪花 ID 生成器（worker/datacenter 可配置） |
| 配置 | `app/config.py` | `SECRET_KEY`、JWT 过期时间、算法、雪花 worker 配置 |
| Model | `app/models/base.py`、`user.py` | Declarative Base + User（`id: BigInteger`） |
| Schema | `app/schemas/auth.py`、`user.py` | Register/Login 入参、Token+User 出参（`id` 输出为 string） |
| Repo | `app/repositories/user_repo.py` | get_by_id / get_by_username / get_by_email / create / update_login |
| Service | `app/services/auth_service.py` | register（含敏感词）/ login / 组装 token 响应 |
| Deps | `app/deps.py` | `get_db`、`get_current_user` |
| Controller | `app/controllers/auth.py` | 路由定义 |
| 入口 | `app/main.py` | `include_router(auth_router, prefix="/api/auth")` |
| 迁移 | `migrations/` | 创建 `users` 表 |

---

## 7. 配置项

| 环境变量 | 必填 | 说明 |
|----------|------|------|
| `DATABASE_URL` | 是 | 已有 |
| `CORS_ORIGINS` | 否 | 已有 |
| `SECRET_KEY` | 是 | JWT 签名 |
| `JWT_ALGORITHM` | 否 | 默认 `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 否 | 默认 `1440`（统一过期；与「记住我」无关） |
| `SNOWFLAKE_WORKER_ID` | 否 | 默认 `1`（0–31） |
| `SNOWFLAKE_DATACENTER_ID` | 否 | 默认 `1`（0–31） |

---

## 8. 依赖增量

- 密码哈希：`bcrypt`
- JWT：`PyJWT`
- 迁移：`alembic`
- 敏感词：`pyahocorasick`

---

## 9. 验收标准（后端）

1. 迁移可重复执行，`users` 表结构与第 3.3 节一致（含唯一约束与 check）。
2. 注册成功写入哈希而非明文；重复 username/email 返回 `err21234335`。
3. 登录支持 username 或 email；错误码区分不存在 / 密码错误。
4. JWT 可被 `/me` 解析；过期与非法 token 返回对应错误码。
5. 所有接口响应为 `{code,message,data}`；业务错误只通过 `ErrorCode`。
6. 响应体永不包含 `password` / `password_hash`。
7. JWT 过期时间符合 `ACCESS_TOKEN_EXPIRE_MINUTES` 单一配置。
8. 注册撞唯一约束返回 `err21234335`，不出现未处理的 500。
9. 注册使用 `db.begin()`；登录更新登录时间使用先读后写 + `commit`。
10. 注册 tags 命中敏感词返回 `err21234339`，且用户未入库；正常标签（如 `Java`）可注册成功。

---

## 10. 实现顺序

1. 配置 + `constants` + `security` + `snowflake`
2. `User` Model（`BIGINT` PK）+ Alembic 迁移
3. `user_repo` + schemas（`id` 序列化为 string）
4. `sensitive` + 词库 + `auth_service`（含标签敏感词）+ `deps`
5. `auth` controller 挂载 + 自测（Swagger / curl）

---

## 11. 开放决策（已给默认）

| 项 | 默认 |
|----|------|
| 主键 | 雪花 ID（`BIGINT`，应用层生成；API 输出字符串） |
| 标签存储 | `JSONB` 数组，本阶段不拆表 |
| Token | 仅 Access JWT，无 refresh 表 |
| 时间对外格式 | ISO8601（Schema 层）；库内 `timestamptz` |
| 禁用账号错误码 | `ERR_ACCOUNT_DISABLED`（`err21234338`） |
| 注册查重 | 不先查；UNIQUE + `IntegrityError` 映射 |
| 注册幂等 | 仅防重复行；不做「重试同成功响应」 |
| 自定义标签 | 允许；后端敏感词检测，命中拒绝 |
| 敏感词策略 | AC + 本地词库；检测即报错，不打码 |
| bio 敏感词 | 本阶段不做，后续复用 `sensitive` 模块 |
| Demo 数据 | 本 TRD 不要求 seed |
