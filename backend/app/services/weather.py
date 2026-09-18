"""Weather: keyless Open-Meteo forecast with a DB-backed TTL cache."""
import json
from datetime import date, datetime, timedelta, timezone
from urllib import request as urlrequest
from urllib.error import URLError

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.models import WeatherCache

settings = get_settings()

WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Drizzle",
    55: "Dense drizzle", 61: "Light rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Freezing rain", 67: "Freezing rain", 71: "Light snow", 73: "Snow",
    75: "Heavy snow", 80: "Rain showers", 81: "Moderate showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with hail",
}


def _fetch_open_meteo(lat: float, lon: float) -> dict:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
        "precipitation_probability_max,weather_code"
        "&timezone=auto&forecast_days=7"
    )
    req = urlrequest.Request(url, headers={"User-Agent": "KisanProfit/1.0"})
    with urlrequest.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def _advisories(days: list[dict]) -> list[str]:
    tips: list[str] = []
    week_rain = sum(d["precipitation_mm"] for d in days)
    today = days[0] if days else None
    if today and today["precipitation_mm"] >= 10:
        tips.append("Heavy rain expected today — consider postponing spraying or fertilizer application.")
    elif today and today["precipitation_mm"] >= 2.5:
        tips.append("Rain likely today — good day for field prep; avoid pesticide spraying.")
    if week_rain < 5:
        tips.append("Dry week ahead — plan irrigation; young plants need consistent moisture.")
    if week_rain >= 50:
        tips.append("Very wet week — watch for waterlogging and fungal disease; clear field drainage.")
    max_temp = max((d["temp_max_c"] for d in days), default=0)
    if max_temp >= 38:
        tips.append("Heatwave conditions this week — irrigate early morning and watch for heat stress.")
    if not tips:
        tips.append("Stable conditions expected — a good window for regular field work.")
    return tips


def get_forecast(db: Session, lat: float, lon: float) -> dict:
    """7-day forecast with cache; degraded-but-honest when offline."""
    now = datetime.now(timezone.utc)
    ttl = timedelta(minutes=settings.WEATHER_CACHE_TTL_MINUTES)

    cached = (
        db.query(WeatherCache)
        .filter(WeatherCache.latitude == lat, WeatherCache.longitude == lon,
                WeatherCache.fetched_at > now - ttl)
        .first()
    )
    if cached:
        return {**json.loads(cached.payload), "cached": True}

    try:
        raw = _fetch_open_meteo(lat, lon)
        dates = raw["daily"]["time"]
        days = [
            {
                "date": date.fromisoformat(d).isoformat(),
                "temp_min_c": raw["daily"]["temperature_2m_min"][i],
                "temp_max_c": raw["daily"]["temperature_2m_max"][i],
                "precipitation_mm": raw["daily"]["precipitation_sum"][i] or 0.0,
                "precipitation_probability_percent": raw["daily"]["precipitation_probability_max"][i] or 0,
                "weather_code": raw["daily"]["weather_code"][i],
            }
            for i, d in enumerate(dates)
        ]
        payload = {
            "latitude": lat, "longitude": lon, "days": days,
            "advisory": _advisories(days), "cached": False,
        }
        db.add(WeatherCache(latitude=lat, longitude=lon, payload=json.dumps(payload), fetched_at=now))
        db.commit()
        return payload
    except (URLError, OSError, KeyError, ValueError):
        # Offline: serve stale cache if any, else an honest empty forecast.
        stale = (
            db.query(WeatherCache)
            .filter(WeatherCache.latitude == lat, WeatherCache.longitude == lon)
            .order_by(WeatherCache.fetched_at.desc())
            .first()
        )
        if stale:
            return {**json.loads(stale.payload), "cached": True}
        return {
            "latitude": lat, "longitude": lon, "days": [],
            "advisory": ["Weather service unreachable — showing no forecast rather than guessing."],
            "cached": False,
        }
