"""The public demo's open doors: one-tap demo entry, and the throttles that
keep password guessing, scripted sign-ups and LLM-quota burn from being free.

The suite disables rate limiting globally (conftest) because it hammers one
"IP"; these tests switch it on per bucket, from Settings, and reset the
buckets so nothing leaks between cases.
"""
import pytest

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.seed import seed_demo_data

DEMO_MOBILE = get_settings().DEMO_MOBILE
DEMO_PASSWORD = get_settings().DEMO_PASSWORD

XFF = {"X-Forwarded-For": "203.0.113.7"}


@pytest.fixture()
def demo_ready(client):
    """Seed the demo account (conftest disables auto-seeding)."""
    settings = get_settings()
    original = settings.SEED_DEMO_DATA
    settings.SEED_DEMO_DATA = "true"
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()
    yield
    settings.SEED_DEMO_DATA = original


def _enable(monkeypatch, **limits):
    """Turn throttling on, with optional per-bucket overrides."""
    settings = get_settings()
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", "true")
    for name, value in limits.items():
        monkeypatch.setattr(settings, name, value)


def test_login_is_throttled_per_ip(monkeypatch, client):
    _enable(monkeypatch, RATE_LIMIT_LOGIN=3)
    body = {"mobile": "9000000001", "password": "wrong-password"}
    for _ in range(3):
        assert client.post("/api/auth/login", json=body, headers=XFF).status_code == 401

    blocked = client.post("/api/auth/login", json=body, headers=XFF)
    assert blocked.status_code == 429
    assert blocked.json()["detail"].startswith("Too many requests")
    assert int(blocked.headers["Retry-After"]) >= 1


def test_the_configured_forwarded_position_decides_the_bucket(monkeypatch, client):
    """The parser must follow PROXY_IP_POSITION, since the trustworthy entry
    differs between Render's edge (leftmost) and the bundled nginx (rightmost)."""
    body = {"mobile": "9000000003", "password": "wrong-password"}

    # Render: the real client IP is first; anything after it is client-supplied
    # (or an internal hop), so vary the tail and expect the same bucket.
    _enable(monkeypatch, RATE_LIMIT_LOGIN=1)
    assert client.post("/api/auth/login", json=body,
                       headers={"X-Forwarded-For": "203.0.113.7, 10.0.0.1"}).status_code == 401
    assert client.post("/api/auth/login", json=body,
                       headers={"X-Forwarded-For": "203.0.113.7, 10.0.0.9"}).status_code == 429

    # nginx: the peer it saw is appended last, so the tail is the client.
    from app.core import ratelimit

    monkeypatch.setattr(get_settings(), "PROXY_IP_POSITION", "last")
    ratelimit.reset_limiters()
    assert client.post("/api/auth/login", json=body,
                       headers={"X-Forwarded-For": "10.0.0.9, 198.51.100.4"}).status_code == 401
    assert client.post("/api/auth/login", json=body,
                       headers={"X-Forwarded-For": "10.0.0.1, 198.51.100.4"}).status_code == 429


def test_another_ip_has_its_own_budget(monkeypatch, client):
    _enable(monkeypatch, RATE_LIMIT_LOGIN=1)
    body = {"mobile": "9000000002", "password": "wrong-password"}
    assert client.post("/api/auth/login", json=body, headers=XFF).status_code == 401
    assert client.post("/api/auth/login", json=body, headers=XFF).status_code == 429

    other = client.post("/api/auth/login", json=body,
                        headers={"X-Forwarded-For": "198.51.100.9"})
    assert other.status_code == 401  # its own window, not a shared one


def test_register_is_throttled(monkeypatch, client):
    _enable(monkeypatch, RATE_LIMIT_REGISTER=2)
    for i in range(2):
        r = client.post("/api/auth/register", headers=XFF, json={
            "name": "Flood Bot", "mobile": f"91111111{i:02d}", "password": "secret123",
        })
        assert r.status_code == 201, r.text
    assert client.post("/api/auth/register", headers=XFF, json={
        "name": "Flood Bot", "mobile": "9111111199", "password": "secret123",
    }).status_code == 429


def test_chat_is_throttled_per_user_and_per_ip(monkeypatch, client, user_token):
    headers, _ = user_token
    _enable(monkeypatch, RATE_LIMIT_CHAT_PER_USER=2, RATE_LIMIT_CHAT_PER_IP=50)
    for _ in range(2):
        assert client.post("/api/ai/chat", headers=headers,
                           json={"message": "Where am I spending the most?"}).status_code == 200

    blocked = client.post("/api/ai/chat", headers=headers,
                          json={"message": "and again?"})
    assert blocked.status_code == 429

    # A different account on the same IP still has room (per-user bucket).
    other = client.post("/api/auth/register", json={
        "name": "Second Farmer", "mobile": "9222222222", "password": "secret123",
    }).json()["access_token"]
    assert client.post("/api/ai/chat", headers={"Authorization": f"Bearer {other}"},
                       json={"message": "hello"}).status_code == 200


def test_limits_are_off_by_default_in_the_suite(client):
    """Sanity check that the suite's own traffic is never throttled."""
    assert client.post("/api/auth/login", json={
        "mobile": "9333333333", "password": "nope"}).status_code == 401
    assert get_settings().RATE_LIMIT_ENABLED.lower() == "false"


# ---------------------------------------------------------------- demo entry
def test_demo_login_needs_no_credentials(demo_ready, client):
    r = client.post("/api/auth/demo-login")
    assert r.status_code == 200, r.text
    assert r.json()["user"]["is_demo"] is True
    assert r.json()["user"]["mobile"] == DEMO_MOBILE

    token = r.json()["access_token"]
    reads = client.get("/api/expenses", headers={"Authorization": f"Bearer {token}"})
    assert reads.status_code == 200 and len(reads.json()) == 14


def test_demo_login_can_be_switched_off(monkeypatch, demo_ready, client):
    monkeypatch.setattr(get_settings(), "DEMO_LOGIN_ENABLED", "false")
    assert client.post("/api/auth/demo-login").status_code == 404


def test_demo_login_is_throttled(monkeypatch, demo_ready, client):
    _enable(monkeypatch, RATE_LIMIT_DEMO_LOGIN=2)
    for _ in range(2):
        assert client.post("/api/auth/demo-login", headers=XFF).status_code == 200
    assert client.post("/api/auth/demo-login", headers=XFF).status_code == 429


def test_documented_password_still_works(demo_ready, client):
    """The README's login must keep working — the demo link is an extra door."""
    r = client.post("/api/auth/login", json={"mobile": DEMO_MOBILE, "password": DEMO_PASSWORD})
    assert r.status_code == 200
    assert r.json()["user"]["is_demo"] is True
