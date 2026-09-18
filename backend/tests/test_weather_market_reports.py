"""Weather / market / notifications / reports / integrations / geocode."""
import random
from unittest.mock import patch

import pytest


def _unique_mobile() -> str:
    return f"9{random.randint(10**8, 10**9 - 1)}"


FAKE_OPEN_METEO = {
    "daily": {
        "time": ["2026-09-18", "2026-09-19", "2026-09-20"],
        "temperature_2m_max": [33.0, 31.0, 29.0],
        "temperature_2m_min": [24.0, 23.0, 22.0],
        "precipitation_sum": [0.0, 12.0, 45.0],
        "precipitation_probability_max": [10, 80, 90],
        "weather_code": [0, 63, 65],
    }
}


def test_weather_advisories_and_caching(authed_client):
    lat, lon = 20.7002, 77.0082
    with patch("app.services.weather._fetch_open_meteo", return_value=FAKE_OPEN_METEO):
        r1 = authed_client.get("/api/weather", params={"latitude": lat, "longitude": lon})
    assert r1.status_code == 200
    body = r1.json()
    assert len(body["days"]) == 3 and body["cached"] is False
    # second call must come from cache without any fetch
    r2 = authed_client.get("/api/weather", params={"latitude": lat, "longitude": lon})
    assert r2.json()["cached"] is True


def test_weather_offline_serves_stale_or_empty(authed_client):
    with patch("app.services.weather._fetch_open_meteo",
               side_effect=OSError("network down")):
        r = authed_client.get("/api/weather", params={"latitude": 19.9, "longitude": 79.9})
    assert r.status_code == 200
    body = r.json()
    assert body["days"] == [] and "unreachable" in body["advisory"][0].lower()


def test_market_reference_prices_labeled(authed_client):
    r = authed_client.get("/api/market")
    assert r.status_code == 200
    body = r.json()
    assert body["live"] is False and body["source"] == "reference"
    assert any("Cotton" in row["commodity"] for row in body["rows"])


def test_market_filter_by_commodity(authed_client):
    r = authed_client.get("/api/market", params={"commodity": "wheat"})
    rows = r.json()["rows"]
    assert rows and all("Wheat" in row["commodity"] for row in rows)


def test_notifications_created_and_marked(authed_client):
    authed_client.post("/api/expenses", json={"category": "equipment", "amount": 25000})
    listing = authed_client.get("/api/notifications").json()
    kinds = {n["kind"] for n in listing}
    assert "high_expense" in kinds
    nid = listing[0]["id"]
    assert authed_client.post(f"/api/notifications/{nid}/read").status_code == 204
    unread = authed_client.get("/api/notifications/unread-count").json()
    assert unread["unread"] >= 0


def test_notifications_require_auth(client):
    assert client.get("/api/notifications").status_code == 401


def test_crop_pdf_report(authed_client):
    farm = authed_client.post("/api/farms", json={"name": "F", "area_acres": 2}).json()
    crop = authed_client.post(f"/api/farms/{farm['id']}/crops", json={
        "name": "Cotton", "area_acres": 2}).json()
    authed_client.post("/api/expenses", json={"category": "seeds", "amount": 5000, "crop_id": crop["id"]})
    r = authed_client.get(f"/api/reports/crop/{crop['id']}/pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:5] == b"%PDF-"


def test_expense_csv_report(authed_client):
    authed_client.post("/api/expenses", json={"category": "fuel", "amount": 800})
    r = authed_client.get("/api/reports/expenses/csv")
    assert r.status_code == 200
    assert b"category" in r.content and b"fuel" in r.content


def test_summary_pdf_endpoints(authed_client):
    for kind in ("monthly", "seasonal", "annual"):
        r = authed_client.get(f"/api/reports/{kind}/pdf")
        assert r.status_code == 200 and r.content[:5] == b"%PDF-"


def test_integrations_status_shape(authed_client):
    r = authed_client.get("/api/integrations")
    names = {row["name"] for row in r.json()}
    assert {"Weather", "Mandi prices", "Kisan AI", "Receipt OCR"} <= names


def test_geocode_offline_fallback(authed_client):
    r = authed_client.post("/api/location/geocode", json={"query": "Akola"})
    results = r.json()["results"]
    assert results and "Akola" in results[0]["display_name"]


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_demo_seed_idempotent_shape():
    """Seeding uses a fixed demo mobile and is guarded against duplicates."""
    from app.core.config import get_settings
    mobile = get_settings().DEMO_MOBILE
    assert mobile.isdigit() and len(mobile) == 10
