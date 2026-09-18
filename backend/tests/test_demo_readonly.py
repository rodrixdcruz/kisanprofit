"""The shared demo account must be read-only, and re-seedable by an operator.

Guards the judge-facing walkthrough: a public visitor can explore the seeded
farm but cannot add, edit or delete anything, and the nightly reset can rebuild
it from scratch behind a shared secret.
"""
import pytest

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.seed import seed_demo_data

# The demo credentials are env-overridable now; read them from Settings so the
# tests follow a deployment that rotated them.
DEMO_MOBILE = get_settings().DEMO_MOBILE
DEMO_PASSWORD = get_settings().DEMO_PASSWORD


@pytest.fixture()
def demo_headers(client, monkeypatch):
    """Seed the demo farmer, then log in as it."""
    monkeypatch.setattr(get_settings(), "SEED_DEMO_DATA", "true")
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()
    r = client.post("/api/auth/login", json={"mobile": DEMO_MOBILE, "password": DEMO_PASSWORD})
    assert r.status_code == 200, r.text
    assert r.json()["user"]["is_demo"] is True
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_demo_can_still_read_the_farm(client, demo_headers):
    r = client.get("/api/expenses", headers=demo_headers)
    assert r.status_code == 200
    assert len(r.json()) == 14  # the walkthrough's seeded expense roster
    farms = client.get("/api/farms", headers=demo_headers)
    assert farms.status_code == 200 and farms.json()
    dash = client.get("/api/analytics/dashboard", headers=demo_headers)
    assert dash.status_code == 200
    assert dash.json()["net_profit"] == pytest.approx(85400.0)


def test_demo_writes_are_rejected(client, demo_headers):
    farm_id = client.get("/api/farms", headers=demo_headers).json()[0]["id"]
    crop_id = client.get(f"/api/farms/{farm_id}/crops", headers=demo_headers).json()[0]["id"]
    exp_id = client.get("/api/expenses", headers=demo_headers).json()[0]["id"]

    attempts = [
        ("POST", "/api/farms", {"name": "Rogue Farm", "area_acres": 1.0}),
        ("PUT", f"/api/farms/{farm_id}", {"name": "Renamed", "area_acres": 10.0}),
        ("DELETE", f"/api/farms/{farm_id}", None),
        ("POST", f"/api/farms/{farm_id}/crops",
         {"name": "Rogue", "area_acres": 1.0}),
        ("DELETE", f"/api/farms/{farm_id}/crops/{crop_id}", None),
        ("POST", "/api/expenses", {"category": "labor", "amount": 5.0}),
        ("PUT", f"/api/expenses/{exp_id}", {"category": "labor", "amount": 5.0}),
        ("DELETE", f"/api/expenses/{exp_id}", None),
        ("POST", f"/api/crops/{crop_id}/production",
         {"harvest_date": "2026-09-10", "actual_yield_quintal": 1.0}),
        ("POST", f"/api/crops/{crop_id}/sales",
         {"sale_date": "2026-09-12", "quantity_quintal": 1.0, "price_per_quintal": 100.0}),
    ]
    for method, path, body in attempts:
        r = client.request(method, path, headers=demo_headers, json=body)
        assert r.status_code == 403, f"{method} {path} -> {r.status_code} {r.text}"
        assert "read-only" in r.json()["detail"].lower()

    # ...and nothing actually changed.
    assert len(client.get("/api/expenses", headers=demo_headers).json()) == 14
    assert client.get("/api/analytics/dashboard", headers=demo_headers).json()["total_farms"] == 1


def test_normal_user_is_unaffected(authed_client):
    farms = authed_client.post("/api/farms", json={"name": "My Farm", "area_acres": 2.0})
    assert farms.status_code == 201, farms.text
    exp = authed_client.post("/api/expenses", json={"category": "seeds", "amount": 1200.0})
    assert exp.status_code == 201, exp.text


def test_reseed_route_is_hidden_without_a_configured_token(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "RESEED_TOKEN", "")
    r = client.post("/api/admin/reseed-demo", headers={"X-Reseed-Token": "anything"})
    assert r.status_code == 404


def test_reseed_route_requires_the_right_token(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "RESEED_TOKEN", "s3cret-token")
    assert client.post("/api/admin/reseed-demo").status_code == 403
    assert client.post("/api/admin/reseed-demo",
                       headers={"X-Reseed-Token": "wrong"}).status_code == 403


def test_reseed_puts_the_canonical_demo_password_back(client, demo_headers, monkeypatch):
    """A hand-edited password is reverted, so the documented login always works."""
    from app.models.models import User

    db = SessionLocal()
    try:
        demo = db.query(User).filter(User.mobile == DEMO_MOBILE).one()
        demo.password_hash = "not-a-real-hash"
        db.commit()
    finally:
        db.close()
    assert client.post("/api/auth/login", json={
        "mobile": DEMO_MOBILE, "password": DEMO_PASSWORD}).status_code == 401

    monkeypatch.setattr(get_settings(), "SEED_DEMO_DATA", "true")
    monkeypatch.setattr(get_settings(), "RESEED_TOKEN", "s3cret-token")
    r = client.post("/api/admin/reseed-demo", headers={"X-Reseed-Token": "s3cret-token"})
    assert r.status_code == 200, r.text
    assert client.post("/api/auth/login", json={
        "mobile": DEMO_MOBILE, "password": DEMO_PASSWORD}).status_code == 200


def test_reseed_restores_a_polluted_demo_farm(client, demo_headers, monkeypatch):
    """Even a direct data mutation is wiped by the nightly reset."""
    from app.models.models import Expense, User

    db = SessionLocal()
    try:
        demo = db.query(User).filter(User.mobile == DEMO_MOBILE).one()
        before_id = demo.id
        db.add(Expense(user_id=demo.id, category="other", amount=99999.0))
        db.commit()
    finally:
        db.close()
    assert len(client.get("/api/expenses", headers=demo_headers).json()) == 15

    monkeypatch.setattr(get_settings(), "SEED_DEMO_DATA", "true")
    monkeypatch.setattr(get_settings(), "RESEED_TOKEN", "s3cret-token")
    r = client.post("/api/admin/reseed-demo", headers={"X-Reseed-Token": "s3cret-token"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "reseeded"
    assert body["expenses"] == 14 and body["crops"] == 3
    # The account row is reused, so a visitor's in-flight session survives.
    assert body["demo_user_id"] == before_id
    assert len(client.get("/api/expenses", headers=demo_headers).json()) == 14
    dash = client.get("/api/analytics/dashboard", headers=demo_headers).json()
    assert dash["net_profit"] == pytest.approx(85400.0)
    assert dash["total_farms"] == 1
