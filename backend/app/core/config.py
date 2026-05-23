from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_WORKSPACE_ROOT = Path(__file__).resolve().parents[1] / "workspace"


class Settings(BaseSettings):
    """Application settings loaded from environment variables when present."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    APP_NAME: str = "Minimal Cloud CAE Demo Backend"
    API_PREFIX: str = "/api"
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    CCX_EXECUTABLE: str = r"E:\CalculiX-2.23.0-win-x64\bin\ccx.exe"
    WORKSPACE_ROOT: Path = DEFAULT_WORKSPACE_ROOT


@lru_cache
def get_settings() -> Settings:
    return Settings()
