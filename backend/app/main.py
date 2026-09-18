"""KisanProfit backend entrypoint.

Lifespan creates tables and (optionally) seeds the demo farmer; all routers
mount under /api; /health serves container health checks.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.seed import seed_at_startup

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_at_startup()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENV != "production" else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.ENV != "production" else None,
)

# CORS allow-list from env
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.routers import (ai, analytics, auth, crops, expenses, farms,  # noqa: E402
                             integrations, location, market, notifications,
                             ocr, production, reports, sales, weather)

API_PREFIX = "/api"
for r in (auth, farms, crops, expenses, production, sales, analytics, ai,
          weather, market, reports, notifications, location, ocr, integrations):
    app.include_router(r.router, prefix=API_PREFIX)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}
