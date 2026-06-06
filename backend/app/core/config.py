from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


# 默认配置，从.env中获取
class Settings(BaseSettings):
    APP_NAME: str
    APP_ENV: str
    CORS_ORIGINS: str
    DATABASE_URL: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
