from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


# Settings 是整个后端的配置类。
# 它会优先读取 .env 文件或系统环境变量；如果没有配置，就使用这里写的默认值。
class Settings(BaseSettings):
    # 应用名称，会显示在 FastAPI docs 页面里。
    APP_NAME: str = "AgentDesk"

    # 当前运行环境，后续可以用 development / production 区分本地和线上配置。
    APP_ENV: str = "development"

    # 允许访问后端的前端地址。
    # 多个地址可以用英文逗号分隔，例如：
    # http://localhost:5173,http://localhost:3000
    CORS_ORIGINS: str = "http://localhost:5173"

    # 告诉 pydantic-settings：可以从 .env 文件读取配置，文件编码是 UTF-8，覆盖前面的默认配置
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins(self) -> list[str]:
        # FastAPI 的 CORS 配置需要 list[str]，
        # 这里把 .env 里用逗号分隔的字符串转换成列表。
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


# 缓存配置对象，避免每次使用 settings 时都重新读取 .env。
@lru_cache
def get_settings() -> Settings:
    return Settings()


# 项目里其他文件直接导入 settings，就可以读取统一配置。
settings = get_settings()
