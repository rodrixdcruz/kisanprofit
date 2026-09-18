"""Market prices: data.gov.in (Agmarknet) when keyed, labeled reference prices otherwise."""
import json
import logging
from datetime import date, datetime, timezone
from urllib import request as urlrequest
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.models import MarketPrice

log = logging.getLogger(__name__)
settings = get_settings()

# Resource ID for the Agmarknet daily mandi price dataset on data.gov.in
AGMARKNET_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"

# Reference prices (₹/quintal, indicative mandi levels) used when no API key.
REFERENCE = [
    {"commodity": "Cotton", "market": "", "min_price": 6500, "max_price": 8200, "modal_price": 7500},
    {"commodity": "Soybean", "market": "", "min_price": 4200, "max_price": 5000, "modal_price": 4700},
    {"commodity": "Wheat", "market": "", "min_price": 2200, "max_price": 2600, "modal_price": 2400},
    {"commodity": "Rice", "market": "", "min_price": 1900, "max_price": 2400, "modal_price": 2200},
    {"commodity": "Maize", "market": "", "min_price": 1900, "max_price": 2300, "modal_price": 2100},
    {"commodity": "Gram (Chana)", "market": "", "min_price": 5000, "max_price": 5900, "modal_price": 5500},
    {"commodity": "Tur (Arhar)", "market": "", "min_price": 7000, "max_price": 8100, "modal_price": 7550},
    {"commodity": "Groundnut", "market": "", "min_price": 5800, "max_price": 6800, "modal_price": 6300},
    {"commodity": "Sugarcane", "market": "", "min_price": 2900, "max_price": 3400, "modal_price": 3100},
    {"commodity": "Onion", "market": "", "min_price": 1200, "max_price": 2800, "modal_price": 2000},
    {"commodity": "Tomato", "market": "", "min_price": 800, "max_price": 2500, "modal_price": 1600},
    {"commodity": "Potato", "market": "", "min_price": 900, "max_price": 1800, "modal_price": 1400},
    {"commodity": "Chilli (Dry)", "market": "", "min_price": 12000, "max_price": 18000, "modal_price": 15000},
    {"commodity": "Turmeric", "market": "", "min_price": 11000, "max_price": 16000, "modal_price": 13500},
]


def _fetch_agmarknet(api_key: str, commodity: str | None) -> list[dict]:
    params = {
        "api-key": api_key,
        "format": "json",
        "limit": 500,
        "filters[commodity]": commodity or "",
    }
    url = f"https://api.data.gov.in/resource/{AGMARKNET_RESOURCE_ID}?{urlencode({k: v for k, v in params.items() if v})}"
    req = urlrequest.Request(url, headers={"User-Agent": "KisanProfit/1.0"})
    with urlrequest.urlopen(req, timeout=12) as r:
        data = json.loads(r.read())
    rows = []
    for rec in data.get("records", []):
        try:
            rows.append({
                "commodity": rec.get("commodity", ""),
                "market": rec.get("market", ""),
                "min_price": float(rec["min_price"]) if rec.get("min_price") else None,
                "max_price": float(rec["max_price"]) if rec.get("max_price") else None,
                "modal_price": float(rec["modal_price"]) if rec.get("modal_price") else None,
                "price_date": rec.get("arrival_date") or None,
                "source": "agmarknet",
            })
        except (TypeError, ValueError):
            continue
    return rows


def get_prices(db: Session, commodity: str | None = None) -> dict:
    """Live mandi prices when a key exists; clearly-labeled reference prices otherwise."""
    key = settings.DATA_GOV_IN_API_KEY
    if key:
        try:
            rows = _fetch_agmarknet(key, commodity)
            if rows:
                for row in rows:
                    db.add(MarketPrice(
                        commodity=row["commodity"], market=row["market"],
                        min_price=row["min_price"], max_price=row["max_price"],
                        modal_price=row["modal_price"],
                        price_date=row["price_date"] if row["price_date"] else None,
                        source="agmarknet",
                    ))
                db.commit()
                return {"source": "agmarknet", "live": True, "rows": rows[:100]}
        except Exception as exc:  # noqa: BLE001 - fall back honestly
            log.warning("Agmarknet fetch failed (%s); serving reference prices", exc)

    rows = [r for r in REFERENCE if not commodity or commodity.lower() in r["commodity"].lower()]
    return {
        "source": "reference",
        "live": False,
        "rows": [{**r, "price_date": None} for r in rows],
        "note": ("Indicative reference prices, not live mandi quotes. "
                 "Set DATA_GOV_IN_API_KEY for live Agmarknet prices."),
    }
