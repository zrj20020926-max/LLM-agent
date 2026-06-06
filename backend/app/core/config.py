from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


# 统一管理后端运行配置。
# 字段不设置默认值，表示这些配置必须来自 backend/.env 或系统环境变量。
class Settings(BaseSettings):
    # 应用名称，会显示在 FastAPI 文档等位置。
    APP_NAME: str

    # 当前运行环境，例如 development、test、production。
    APP_ENV: str

    # 允许访问后端的前端地址；多个地址用英文逗号分隔。
    CORS_ORIGINS: str

    # 让 pydantic-settings 自动读取 backend/.env。
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins(self) -> list[str]:
        # FastAPI 的 CORS 配置需要 list[str]，这里把逗号分隔的字符串转成列表。
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


# 缓存配置对象，避免每次导入 settings 时都重复读取 .env。
@lru_cache
def get_settings() -> Settings:
    return Settings()


# 项目其他模块直接导入 settings 使用统一配置。
settings = get_settings()
