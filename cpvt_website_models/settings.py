from functools import lru_cache

from pydantic import (
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PostgreSQL
    driver: str = "postgresql+psycopg_async"
    postgresql_host: str = "localhost"
    postgresql_username: str = "postgres"
    postgresql_password: str = "postgres"
    postgresql_database: str = "postgres"
    postgresql_schema: str = "public"
    postgresql_port: int = 5432

    @computed_field
    @property
    def postgresql_dsn(self) -> str:
        return f"{self.driver}://{self.postgresql_username}:{self.postgresql_password}@{self.postgresql_host}:{self.postgresql_port}/{self.postgresql_database}"

    model_config = SettingsConfigDict(env_file='.env',
                                      env_file_encoding='utf-8',
                                      extra='ignore'
                                      )


@lru_cache()
def get_settings() -> Settings:
    print("Loading settings...")
    settings = Settings()
    return settings


__all__ = [
    "Settings",
    "get_settings",
]
