"""Integration status: what is live vs demo mode right now (Settings page)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.db import get_db
from app.models.models import User
from app.services.ocr import ocr_available

router = APIRouter(prefix="/integrations", tags=["integrations"])

settings = get_settings()


@router.get("")
def status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [
        {"name": "Weather", "live": True, "detail": "Open-Meteo — live, no key needed"},
        {"name": "Map & location", "live": True,
         "detail": "OpenStreetMap / Nominatim — live; offline lookup fallback"},
        {"name": "Mandi prices", "live": bool(settings.DATA_GOV_IN_API_KEY),
         "detail": "data.gov.in Agmarknet" if settings.DATA_GOV_IN_API_KEY
         else "Reference prices (set DATA_GOV_IN_API_KEY for live)"},
        {"name": "Kisan AI", "live": settings.AI_PROVIDER in ("gemini", "openai", "auto")
         and bool(settings.GEMINI_API_KEY or settings.OPENAI_API_KEY),
         "detail": ("LLM rephrasing enabled" if (settings.AI_PROVIDER != "offline")
                    else "Deterministic engine on your own records")},
        {"name": "Receipt OCR", "live": ocr_available(),
         "detail": "Gemini vision" if ocr_available() else "Demo mode — results need your confirmation"},
    ]
