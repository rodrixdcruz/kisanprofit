"""Application settings, loaded from environment variables (.env supported).

Everything has a safe default so the app runs out of the box; secrets must
come from the environment, never from the repo.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- app ---
    APP_NAME: str = "KisanProfit"
    ENV: str = "development"

    # --- security ---
    SECRET_KEY: str = "dev-only-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days, matches README

    # --- database ---
    DATABASE_URL: str = "sqlite:///./kisanprofit.db"

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5500,http://127.0.0.1:5173,http://127.0.0.1:5500"

    # --- AI provider: offline | gemini | openai | auto ---
    AI_PROVIDER: str = "offline"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # --- weather (keyless Open-Meteo) ---
    WEATHER_CACHE_TTL_MINUTES: int = 30

    # --- market prices ---
    DATA_GOV_IN_API_KEY: str = ""

    # --- location ---
    NOMINATIM_EMAIL: str = ""

    # --- demo seeding ---
    SEED_DEMO_DATA: str = "true"
    # Shared secret for POST /api/admin/reseed-demo (used by the nightly
    # workflow). Empty means the route is disabled entirely — there is no
    # built-in default, so an unconfigured deploy cannot be reset by strangers.
    RESEED_TOKEN: str = ""

    # --- optional OCR (gemini vision) ---
    OCR_ENABLED: str = "auto"  # auto: on when GEMINI_API_KEY present

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
