"""Receipt OCR: Gemini vision when a key is present; labeled demo mode otherwise.

OCR results are always a *prefill suggestion* — the API never writes an
expense row directly; the user confirms in the UI.
"""
import json
import logging
import re
from datetime import date
from urllib import request as urlrequest

from app.core.config import get_settings
from app.schemas.schemas import CATEGORIES

log = logging.getLogger(__name__)
settings = get_settings()

PROMPT = (
    "You read Indian farm purchase receipts. Extract JSON only, no markdown: "
    '{"amount": number|null, "category": one of ' + json.dumps(CATEGORIES) + ', '
    '"vendor": string|null, "date": "YYYY-MM-DD"|null, "raw_text": string}. '
    "Use null for anything not clearly printed. category must be the closest match "
    "from the list, or null."
)


def ocr_available() -> bool:
    if settings.OCR_ENABLED == "off":
        return False
    return bool(settings.GEMINI_API_KEY)


def extract_receipt_fields(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """Returns OCRResult-shaped dict; demo mode returns empty fields, honestly labeled."""
    if not ocr_available():
        return {
            "amount": None, "category": None, "vendor": None, "date": None,
            "raw_text": "",
            "demo": True,
        }

    model = "gemini-1.5-flash"
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={settings.GEMINI_API_KEY}")
    body = json.dumps({
        "contents": [{
            "parts": [
                {"text": PROMPT},
                {"inline_data": {"mime_type": mime_type, "data": __import__("base64").b64encode(image_bytes).decode()}},
            ]
        }],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 400},
    }).encode()
    req = urlrequest.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urlrequest.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        text = re.sub(r"^```(json)?|```$", "", text, flags=re.M).strip()
        parsed = json.loads(text)
        parsed["demo"] = False
        if parsed.get("date"):
            try:
                parsed["date"] = date.fromisoformat(str(parsed["date"])[:10]).isoformat()
            except ValueError:
                parsed["date"] = None
        if parsed.get("category") not in CATEGORIES:
            parsed["category"] = None
        return parsed
    except Exception as exc:  # noqa: BLE001 - OCR must fail soft
        log.warning("OCR failed (%s); returning demo result", exc)
        return {
            "amount": None, "category": None, "vendor": None, "date": None,
            "raw_text": "", "demo": True,
        }
