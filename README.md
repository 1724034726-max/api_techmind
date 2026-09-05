# TechMind API

FastAPI + PostgreSQL 后端，与 `techmind-web` 同级。

## 环境要求

- Python 3.10+
- PostgreSQL

## 配置

1. 复制环境变量文件：

```powershell
cd D:\MYPRO\techmind-api
Copy-Item .env.example .env
```

2. 编辑 `.env`，至少填好：

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/techmind
CORS_ORIGINS=http://localhost:3000
SECRET_KEY=change-me-to-a-long-random-string
```

其余项可保持默认（JWT 过期、雪花 worker 等）。

## 启动

```powershell
cd D:\MYPRO\techmind-api

# 创建并激活虚拟环境（首次）
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 安装依赖（首次或 requirements 变更后）
pip install -r requirements.txt

# 执行数据库迁移（建表）
alembic upgrade head

# 启动服务
uvicorn app.main:app --reload --port 8000
```

启动成功后：

| 地址 | 说明 |
|------|------|
| http://127.0.0.1:8000/docs | Swagger 文档（可直接试接口） |
| http://127.0.0.1:8000/redoc | ReDoc 文档 |

## 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/auth/register` | 注册（成功即登录） |
| `POST` | `/api/auth/login` | 登录 |
| `POST` | `/api/auth/logout` | 登出（清 Cookie） |
| `GET` | `/api/auth/me` | 当前用户（Cookie `tm_access_token`） |

## 常用命令

```powershell
# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 启动（已装依赖、已迁移过）
uvicorn app.main:app --reload --port 8000

# 重新跑迁移
alembic upgrade head
```
