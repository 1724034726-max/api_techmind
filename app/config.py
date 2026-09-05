# 应用配置（环境变量 / .env）
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    cors_origins: str = "http://localhost:3000"

    # JWT
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    # 跨站 Cookie 需 Secure；本地 http://localhost 亦可用 True（Chromium）
    cookie_secure: bool = True

    # 雪花
    snowflake_worker_id: int = 1
    snowflake_datacenter_id: int = 1

    # 火山方舟
    ark_api_key: str = Field(default="", alias="ARK_API_KEY")
    ark_base_url: str = Field(
        default="https://ark.cn-beijing.volces.com",
        alias="ARK_BASE_URL",
    )
    ark_chat_model: str = Field(
        default="doubao-seed-2-0-code-preview-260215",
        alias="ARK_CHAT_MODEL",
    )
    ark_chat_completions_url: str = Field(default="", alias="ARK_CHAT_COMPLETIONS_URL")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def ark_chat_completions_endpoint(self) -> str:
        if self.ark_chat_completions_url:
            return self.ark_chat_completions_url
        return f"{self.ark_base_url.rstrip('/')}/api/v3/chat/completions"


@lru_cache
def get_settings() -> Settings:
    return Settings()
