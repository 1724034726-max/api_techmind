# FastAPI 应用入口：中间件与路由挂载
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.controllers.articles import router as articles_router
from app.controllers.auth import router as auth_router
from app.controllers.editor import router as editor_router
from app.controllers.favorites import router as favorites_router
from app.controllers.topics import router as topics_router
from app.controllers.users import router as users_router
from app.core.exception_handlers import register_exception_handlers

settings = get_settings()

app = FastAPI(title="TechMind API", version="0.1.0")

# 注册全局异常过滤器
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载认证 / 用户 / 文章草稿 / 写作助手
app.include_router(auth_router, prefix="/api/auth")
app.include_router(users_router, prefix="/api/users")
app.include_router(articles_router, prefix="/api/articles")
app.include_router(favorites_router, prefix="/api/favorites")
app.include_router(topics_router, prefix="/api/topics")
app.include_router(editor_router, prefix="/api/editor")
