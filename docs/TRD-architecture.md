# TRD：TechMind API 整体架构与全局约定

| 项 | 内容 |
|----|------|
| 文档类型 | Technical Requirements Document |
| 范围 | `techmind-api` 工程架构、分层、全局基建与跨模块约定 |
| 关联文档 | [TRD-auth-login-register.md](./TRD-auth-login-register.md)（认证）、[TRD-articles-editor.md](./TRD-articles-editor.md)（文章与写作） |
| 版本 | v1.3 |
| 日期 | 2026-08-14 |
| 状态 | Draft |

---

## 1. 目标

本文描述 **整个后端项目** 的骨架与全局能力，作为后续各业务 TRD / 实现的公共前提。

包含：

- 技术选型与目录结构
- 分层与调用链
- 统一响应、错误码、异常处理
- 配置、CORS、数据库会话与事务
- 主键（雪花）、鉴权基建、迁移
- 命名与工程约定

不包含：具体业务接口细节（由各专题 TRD 展开，如认证、文章与写作）。

---

## 2. 系统定位

TechMind API 是「AI 驱动的技术内容社区」后端，对接 `techmind-web`（及后续客户端）。

当前已落地：**认证（注册 / 登录 / me）**、用户主题偏好、**文章草稿 CRUD**、**写作助手 AI（方舟 + SSE）**。  
详设见：[TRD-auth-login-register.md](./TRD-auth-login-register.md)、[TRD-articles-editor.md](./TRD-articles-editor.md)。  
骨架已按业务域预留：搜索、收藏、专栏、专题、图谱、流水线、运营台等（多数为空文件占位）。

---

## 3. 技术选型

| 类别 | 选型 |
|------|------|
| 语言 / 运行时 | Python 3.10+ |
| Web 框架 | FastAPI |
| ORM | SQLAlchemy 2.x |
| 数据库 | PostgreSQL（`psycopg`） |
| 迁移 | Alembic |
| 配置 | pydantic-settings（`.env`） |
| 密码 | bcrypt |
| 令牌 | JWT（PyJWT，HS256） |
| 主键 | 雪花 ID（应用层生成，`BIGINT`） |
| 进程 | uvicorn |

FastAPI **不提供**事务与业务错误体系；二者分别由 SQLAlchemy Session 与项目自研 `ErrorCode` / `AppException` 承担。

---

## 4. 目录结构

```
techmind-api/
├── app/
│   ├── main.py                 # 入口：中间件、异常处理器、路由挂载
│   ├── config.py               # 环境配置
│   ├── deps.py                 # FastAPI 依赖（db、当前用户）
│   ├── core/                   # 跨模块核心能力
│   │   ├── constants.py        # 枚举常量
│   │   ├── error_codes.py      # 业务错误码
│   │   ├── exceptions.py       # AppException / exception()
│   │   ├── exception_handlers.py
│   │   ├── security.py         # 密码哈希、JWT
│   │   ├── sensitive.py        # 敏感词检测
│   │   └── snowflake.py        # 雪花 ID
│   ├── db/
│   │   └── session.py          # engine、SessionLocal、get_db
│   ├── models/                 # ORM（表结构）
│   ├── schemas/                # DTO / VO（入参出参）
│   ├── repositories/           # 数据访问
│   ├── services/               # 业务逻辑
│   └── controllers/            # HTTP 路由
├── data/
│   └── sensitive_words.txt     # 敏感词词库
├── migrations/                 # Alembic 版本脚本
├── docs/                       # TRD 等文档
├── tests/
├── .cursor/rules/              # 工程约定（注释、事务等）
├── alembic.ini
├── requirements.txt
├── .env.example
└── README.md
```

---

## 5. 分层架构

### 5.1 调用链

```
HTTP Request
    │
    ▼
Controller（路由、入参 Schema、包装 ApiResponse）
    │
    ▼
Service（业务规则、事务边界、ErrorCode）
    │
    ├──► Repository（SQL / ORM 读写，不 commit）
    │         │
    │         ▼
    │      PostgreSQL
    │
    └──► core（security / snowflake / constants …）
```

### 5.2 各层职责

| 层 | 职责 | 禁止 |
|----|------|------|
| **Controller** | 定义路由；接收 DTO；调 Service；返回 `ApiResponse` | 写业务规则、直接操作 Session 事务 |
| **Service** | 业务编排；`begin`/`commit`；抛 `exception(ErrorCode)` | 拼 HTTP 细节、散落中文错误文案 |
| **Repository** | 查询 / `add` / `flush` | `commit` / `begin` / 业务判断 |
| **Model** | 表映射 | 暴露给前端 |
| **Schema** | 入参校验与出参形状 | 代替 Model 落库 |

### 5.3 Schema 命名（DTO / VO）

| 后缀 | 含义 | 示例 |
|------|------|------|
| `*DTO` | 请求入参 | `RegisterDTO`、`LoginDTO` |
| `*VO` | 响应出参 | `UserVO`、`TokenVO` |
| `ApiResponse[T]` | 全局响应信封 | `ApiResponse[TokenVO]` |

ORM 实体（如 `User`）不得直接作为 API 响应模型。

---

## 6. 全局响应

所有业务接口统一：

```json
{
  "code": "0",
  "message": "ok",
  "data": {}
}
```

| 字段 | 成功 | 失败 |
|------|------|------|
| `code` | `"0"` | `err…`（见 ErrorCode） |
| `message` | `"ok"` 或提示文案 | 错误码对应中文 |
| `data` | 业务数据 / `null` | 可选附加信息（如校验细节） |

构造方式：

- 成功：`return ApiResponse.ok(data)`
- 失败：业务层 `raise exception(ErrorCode.XXX)`，由全局异常过滤器转成 `ApiResponse.fail(...)`

实现位置：`app/schemas/common.py`。

---

## 7. 全局错误与异常

### 7.1 错误码枚举

位置：`app/core/error_codes.py`。

约定：

- 每个错误一条枚举：`ERR_XXX = ("err……", "中文文案")`
- 业务禁止手写散落的错误字符串；统一 `raise exception(ErrorCode.XXX)`
- 新业务在枚举中增量添加，保持 code 稳定、可给前端映射

当前分类示例：

| 类别 | 示例 |
|------|------|
| 通用 | `ERR_UNKNOWN`、`ERR_VALIDATION`、`ERR_UNAUTHORIZED` … |
| 认证 | `ERR_ACCOUNT_NOT_FOUND`、`ERR_PASSWORD_WRONG`、`ERR_ACCOUNT_EXISTS`、`ERR_SENSITIVE_WORD` … |

### 7.2 业务异常

```python
raise exception(ErrorCode.ERR_PASSWORD_WRONG, http_status=400)
# 或
raise AppException(ErrorCode.ERR_PASSWORD_WRONG, http_status=400)
```

`exception` 为 `AppException` 短别名（`app/core/exceptions.py`）。

### 7.3 全局异常过滤器

位置：`app/core/exception_handlers.py`，在 `main.py` 启动时注册。

| 异常类型 | 处理 |
|----------|------|
| `AppException` | → 对应 `ErrorCode` + HTTP 状态 |
| `RequestValidationError` | → `ERR_VALIDATION`（422） |
| `HTTPException` | → 映射未登录 / 无权限 / 不存在等 |
| 其他未捕获 `Exception` | → `ERR_UNKNOWN`（500），不对外暴露堆栈 |

---

## 8. 配置与 CORS

### 8.1 配置

位置：`app/config.py`，环境变量 / `.env`。

| 变量 | 用途 |
|------|------|
| `DATABASE_URL` | PostgreSQL 连接 |
| `CORS_ORIGINS` | 允许的前端源（逗号分隔） |
| `SECRET_KEY` | JWT 签名 |
| `JWT_ALGORITHM` | 默认 `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token 过期（分钟） |
| `SNOWFLAKE_WORKER_ID` | 雪花机器号 |
| `SNOWFLAKE_DATACENTER_ID` | 雪花数据中心号 |
| `ARK_API_KEY` | 火山方舟密钥（写作 AI）；空则 AI 不可用 |
| `ARK_BASE_URL` | 方舟 API 根；默认北京区 |
| `ARK_CHAT_MODEL` | Chat 模型 id |
| `ARK_CHAT_COMPLETIONS_URL` | 可选；覆盖 completions 完整 URL |

通过 `get_settings()`（`lru_cache`）读取。写作 AI 细节见 [TRD-articles-editor.md](./TRD-articles-editor.md) §5.7。

### 8.2 CORS

在 `main.py` 使用 `CORSMiddleware`：

- `allow_origins` ← `settings.cors_origin_list`
- `allow_credentials=True`
- methods / headers：`*`

「记住我」等浏览器行为 **不属于** 后端配置范畴。

---

## 9. 数据库会话与事务

### 9.1 Session

- `app/db/session.py`：`engine`、`SessionLocal`、`get_db`
- 每个请求一个 Session；异常时 `rollback`，结束时 `close`
- FastAPI 依赖：`DbSession = Annotated[Session, Depends(get_db)]`

### 9.2 事务约定（全局）

| 场景 | 做法 |
|------|------|
| 纯写入（本请求尚未 SELECT） | `with db.begin(): ...`（成功 commit，异常自动 rollback） |
| 先读后写 | 不可再 `begin()`；改完后 `db.commit()`；失败由 `get_db` 兜底 rollback |
| 唯一约束冲突 | 捕 `IntegrityError` → 对应 `ErrorCode`，禁止漏成 500 |
| Repository | 不 `commit` / 不 `begin` |

细节与认证场景示例见认证 TRD §4.5；工程规则见 `.cursor/rules/db-transactions.mdc`。

### 9.3 迁移

- 工具：Alembic（`alembic.ini` + `migrations/`）
- `env.py` 注入 `DATABASE_URL` 与 `Base.metadata`
- 表结构变更必须走迁移脚本，不以运行时 `create_all` 作为正式方案

---

## 10. 全局基础设施

### 10.1 雪花 ID

- 位置：`app/core/snowflake.py`
- 主键类型：`BIGINT`，应用层 `next_id()` 生成
- API 对外：`id` **序列化为字符串**，避免 JS 精度问题

### 10.2 安全

- 位置：`app/core/security.py`
- 密码：bcrypt 哈希存储，禁止明文落库或回传
- JWT：`Authorization: Bearer <token>`；claims 含 `sub`（用户 id 字符串）等
- 当前用户：`deps.get_current_user` / `CurrentUser`

### 10.3 常量

- 位置：`app/core/constants.py`
- 跨模块枚举（如 `UserRole`、`UserStatus`）集中定义，避免魔法字符串散落

### 10.4 敏感词检测

- 位置：`app/core/sensitive.py`
- 依赖：`pyahocorasick`（AC 自动机）
- 词库：`data/sensitive_words.txt`（一行一词；`#` 注释；改后需重启）
- 策略：**检测命中即业务失败**（`ERR_SENSITIVE_WORD`），不静默过滤、不打码替换
- 当前接入：注册自定义 `tags`；后续 `bio`、文章、评论可复用同一模块
- 细节见认证 TRD §4.1.1

---

## 11. 路由与模块地图

### 11.1 挂载约定

- 业务路由按域拆分 Controller，在 `main.py` `include_router`
- URL 前缀建议：`/api/<domain>`（例：`/api/auth`）

### 11.2 域划分（骨架）

| 域 | Controller | 状态（写作时） |
|----|------------|----------------|
| 认证 | `auth` | 已实现 |
| 用户 | `users` | 主题等已实现；其余可扩展 |
| 首页 Feed | `feed` | 占位 |
| 搜索 | `search` | 占位 |
| 文章 | `articles` | 草稿 CRUD 已实现；发布待做，见 [TRD-articles-editor.md](./TRD-articles-editor.md) |
| 写作助手 | `editor` | AI SSE 四接口已实现，见同一 TRD |
| 发布流水线 | `pipeline` | 占位 |
| 收藏 | `favorites` | 占位 |
| 专栏 | `columns` | 占位 |
| 专题 | `topics` | 占位 |
| 知识图谱 | `graph` | 占位 |
| 运营台 | `admin` | 占位 |

每域新增能力时：补 Model（如需）→ Schema → Repo → Service → Controller → 迁移 → 挂载；并宜有对应专题 TRD。

---

## 12. 工程约定

### 12.1 注释

- 文件头一行中文职责说明
- 关键业务步骤可加一行中文注释；正常表达，不写说教式「事务原理」注释（约定放 rule / TRD）
- 详见 `.cursor/rules/chinese-comments.mdc`

### 12.2 文档

| 文档 | 内容 |
|------|------|
| 本文 | 全局架构与约定 |
| `TRD-auth-login-register.md` | 认证表结构、接口、事务在认证中的落地 |
| `TRD-articles-editor.md` | 文章 / 草稿 / 发布 / 写作 AI |
| 后续 `TRD-*.md` | 按业务域增量 |

### 12.3 启动

见根目录 `README.md`（`.env` → 依赖 → `alembic upgrade head` → `uvicorn`）。

---

## 13. 非功能原则（摘要）

| 项 | 约定 |
|----|------|
| 安全 | 密码哈希；JWT；响应无密钥字段 |
| 一致性 | 统一 `ApiResponse` + `ErrorCode` |
| 数据演进 | Alembic；UNIQUE / CHECK 落在库层 |
| 并发写 | 靠 DB 约束 + `IntegrityError` 映射，不靠应用锁做注册类防重 |
| 可观测 | 本阶段不强制；后续可加请求日志 / 追踪 ID |

---

## 14. 开放决策（全局默认）

| 项 | 默认 |
|----|------|
| 分层 | Controller → Service → Repository → Model |
| 入参 / 出参 | DTO / VO |
| 响应信封 | `ApiResponse` |
| 错误 | `ErrorCode` + `exception()` + 全局过滤器 |
| 主键 | 雪花 `BIGINT`，API 出字符串 |
| 事务 | Session；纯写 `begin`，先读后写 `commit` |
| 敏感词 | `pyahocorasick` + `data/sensitive_words.txt`；命中即 `ErrorCode` |
| 配置 | `.env` + pydantic-settings |

业务特例以各专题 TRD 为准；与本文冲突时，**专题 TRD 覆盖该域细节，本文约束全局形态**。
