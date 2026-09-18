"""Location: OpenStreetMap Nominatim geocoding with an offline fallback list."""
import json
from urllib import request as urlrequest
from urllib.parse import quote

from app.core.config import get_settings

settings = get_settings()

# Small offline fallback so "Find on map" never dead-ends without internet.
FALLBACK_PLACES = [
    {"display_name": "Akola, Maharashtra, India", "latitude": 20.7002, "longitude": 77.0082},
    {"display_name": "Nagpur, Maharashtra, India", "latitude": 21.1458, "longitude": 79.0882},
    {"display_name": "Pune, Maharashtra, India", "latitude": 18.5204, "longitude": 73.8567},
    {"display_name": "Mumbai, Maharashtra, India", "latitude": 19.0760, "longitude": 72.8777},
    {"display_name": "Indore, Madhya Pradesh, India", "latitude": 22.7196, "longitude": 75.8577},
    {"display_name": "Bhopal, Madhya Pradesh, India", "latitude": 23.2599, "longitude": 77.4126},
    {"display_name": "Hyderabad, Telangana, India", "latitude": 17.3850, "longitude": 78.4867},
    {"display_name": "Delhi, India", "latitude": 28.6139, "longitude": 77.2090},
]


def geocode(query: str) -> list[dict]:
    email = settings.NOMINATIM_EMAIL
    url = ("https://nominatim.openstreetmap.org/search"
           f"?q={quote(query)}&format=json&limit=5"
           + (f"&email={quote(email)}" if email else ""))
    req = urlrequest.Request(url, headers={
        "User-Agent": "KisanProfit/1.0 (farm expense tracker)",
        "Accept": "application/json",
    })
    try:
        with urlrequest.urlopen(req, timeout=8) as r:
            results = json.loads(r.read())
        return [
            {"display_name": x["display_name"], "latitude": float(x["lat"]), "longitude": float(x["lon"])}
            for x in results
        ]
    except Exception:  # noqa: BLE001 - offline fallback
        q = query.lower()
        matches = [p for p in FALLBACK_PLACES if any(w in p["display_name"].lower() for w in q.split())]
        return matches[:5]
