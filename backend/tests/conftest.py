"""Shared fixtures: isolated SQLite DB per test, TestClient, auth helpers."""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["SEED_DEMO_DATA"] = "false"
os.environ["DATABASE_URL"] = "sqlite:///./test_kisanprofit.db"
os.environ["SECRET_KEY"] = "test-secret-key"
# The suite registers/logs in far more often than a real client would, and all
# from one "IP", so throttling is off here. test_rate_limit.py turns it back on
# for the buckets it exercises.
os.environ["RATE_LIMIT_ENABLED"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

from app.core.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _db():
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    try:
        os.remove("./test_kisanprofit.db")
    except OSError:
        pass


@pytest.fixture()
def client():
    # Schema persists across tests in the session; tests use unique mobiles.
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _fresh_limiters():
    """No rate-limit state leaks between tests (see core/ratelimit.py)."""
    from app.core import ratelimit

    ratelimit.reset_limiters()
    yield
    ratelimit.reset_limiters()


@pytest.fixture()
def user_token(client):
    """A fresh user per test; returns (headers, mobile)."""
    import random
    mobile = f"9{random.randint(10**8, 10**9 - 1)}"
    r = client.post("/api/auth/register", json={
        "name": "Test Farmer", "mobile": mobile, "password": "secret123",
    })
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, mobile


@pytest.fixture()
def authed_client(client, user_token):
    headers, _ = user_token
    client.headers.update(headers)
    yield client
    client.headers.pop("Authorization", None)
