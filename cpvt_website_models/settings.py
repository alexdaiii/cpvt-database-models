from functools import lru_cache

from pydantic import (
    PostgresDsn,
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PostgreSQL
    postgresql_host: str = "localhost"
    postgresql_username: str = "postgres"
    postgresql_password: str = "postgres"
    postgresql_database: str = "postgres"
    postgresql_schema: str = "public"
    postgresql_port: int = 5432

    @computed_field
    @property
    def _postgresql_dsn(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql",
            username=self.postgresql_username,
            password=self.postgresql_password,
            host=self.postgresql_host,
            port=self.postgresql_port,
            path=self.postgresql_database,
        )

    @computed_field
    @property
    def postgresql_dsn(self) -> str:
        return self._postgresql_dsn.__str__()

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
