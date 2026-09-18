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

    # --- demo account ---
    # Public by design (the README documents the login) and read-only, so it is
    # safe to publish. These live here rather than in code so an operator can
    # rotate the demo password from the dashboard and have the reset pick it up.
    DEMO_MOBILE: str = "9999999999"
    DEMO_PASSWORD: str = "demo1234"
    DEMO_NAME: str = "Demo Farmer"
    # One-tap public entry to the demo farm (POST /api/auth/demo-login), which
    # lets the frontend stop embedding credentials. Set false to require real
    # accounts — the demo link then 404s.
    DEMO_LOGIN_ENABLED: str = "true"

    # --- rate limiting (per instance, in-process) ---
    # Blunts password guessing, scripted sign-ups and AI-quota burn on a public
    # free-tier origin. Tuned generously: a whole venue can share one NAT IP.
    RATE_LIMIT_ENABLED: str = "true"
    RATE_LIMIT_WINDOW_SECONDS: int = 300
    RATE_LIMIT_LOGIN: int = 20          # per IP
    RATE_LIMIT_REGISTER: int = 10       # per IP
    RATE_LIMIT_DEMO_LOGIN: int = 60     # per IP — one-tap button, shared NAT
    RATE_LIMIT_CHAT_PER_USER: int = 30  # per account (guards the LLM quota)
    RATE_LIMIT_CHAT_PER_IP: int = 60    # per IP
    # Behind a platform proxy the client IP arrives in X-Forwarded-For. Turn
    # this off if the app is ever exposed without one, or the header becomes
    # client-controlled and the limits can be bypassed.
    TRUST_PROXY_HEADERS: str = "true"

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
