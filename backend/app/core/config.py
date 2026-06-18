from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent


@dataclass(frozen=True)
class Settings:
    app_name: str
    environment: str
    database_url: str
    sample_data_dir: Path
    cors_origins: tuple[str, ...]
    system_user_id: str
    system_username: str
    auth_secret: str
    access_token_ttl_seconds: int
    allow_dev_auth_fallback: bool
    market_data_base_url: str
    market_data_fallback_urls: tuple[str, ...]
    market_data_timeout_seconds: float
    openai_api_key: str | None
    openai_model: str
    openai_base_url: str
    openai_timeout_seconds: float
    gemini_api_key: str | None
    gemini_model: str
    gemini_base_url: str
    gemini_timeout_seconds: float

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    database_path = BACKEND_ROOT / "quant_platform.db"
    cors_origins = _split_csv(
        os.getenv("QUANT_PLATFORM_CORS_ORIGINS"),
        ("http://127.0.0.1:5173", "http://localhost:5173"),
    )
    return Settings(
        app_name=os.getenv("QUANT_PLATFORM_APP_NAME", "Quant Platform API"),
        environment=os.getenv("QUANT_PLATFORM_ENV", "development"),
        database_url=os.getenv("QUANT_PLATFORM_DATABASE_URL", f"sqlite:///{database_path}"),
        sample_data_dir=Path(
            os.getenv("QUANT_PLATFORM_SAMPLE_DATA_DIR", PROJECT_ROOT / "data" / "sample")
        ),
        cors_origins=cors_origins,
        system_user_id=os.getenv("QUANT_PLATFORM_SYSTEM_USER_ID", "dev-user"),
        system_username=os.getenv("QUANT_PLATFORM_SYSTEM_USERNAME", "developer"),
        auth_secret=os.getenv("QUANT_PLATFORM_AUTH_SECRET", "dev-only-change-me"),
        access_token_ttl_seconds=int(
            os.getenv("QUANT_PLATFORM_ACCESS_TOKEN_TTL_SECONDS", "86400")
        ),
        allow_dev_auth_fallback=_parse_bool(
            os.getenv("QUANT_PLATFORM_ALLOW_DEV_AUTH_FALLBACK"),
            default=os.getenv("QUANT_PLATFORM_ENV", "development") == "development",
        ),
        market_data_base_url=os.getenv(
            "QUANT_PLATFORM_MARKET_DATA_BASE_URL", "https://api.binance.com"
        ).rstrip("/"),
        market_data_fallback_urls=tuple(
            url.rstrip("/")
            for url in _split_csv(
                os.getenv("QUANT_PLATFORM_MARKET_DATA_FALLBACK_URLS"),
                ("https://data-api.binance.vision",),
            )
        ),
        market_data_timeout_seconds=float(
            os.getenv("QUANT_PLATFORM_MARKET_DATA_TIMEOUT_SECONDS", "20")
        ),
        openai_api_key=os.getenv("QUANT_PLATFORM_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("QUANT_PLATFORM_OPENAI_MODEL", "gpt-5.5"),
        openai_base_url=os.getenv("QUANT_PLATFORM_OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        openai_timeout_seconds=float(os.getenv("QUANT_PLATFORM_OPENAI_TIMEOUT_SECONDS", "30")),
        gemini_api_key=os.getenv("QUANT_PLATFORM_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY"),
        gemini_model=os.getenv("QUANT_PLATFORM_GEMINI_MODEL", "gemini-3.5-flash"),
        gemini_base_url=os.getenv(
            "QUANT_PLATFORM_GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"
        ).rstrip("/"),
        gemini_timeout_seconds=float(os.getenv("QUANT_PLATFORM_GEMINI_TIMEOUT_SECONDS", "30")),
    )


def _split_csv(value: str | None, default: tuple[str, ...]) -> tuple[str, ...]:
    if not value:
        return default
    items = tuple(item.strip() for item in value.split(",") if item.strip())
    return items or default


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
