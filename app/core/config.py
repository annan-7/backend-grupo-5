"""Configuración de la aplicación (12-factor: variables de entorno / .env)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # PostgreSQL con driver async por defecto. En tests se sobreescribe con
    # DATABASE_URL=sqlite+aiosqlite:///... (ver tests/conftest.py).
    database_url: str = "postgresql+asyncpg://coworking:coworking@localhost:5432/coworking"
    echo_sql: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
