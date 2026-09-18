"""Auth: registration, login, session, validation, authorization."""
import random

import pytest


def _unique_mobile() -> str:
    return f"9{random.randint(10**8, 10**9 - 1)}"


def test_register_creates_user_and_token(client):
    r = client.post("/api/auth/register", json={
        "name": "Asha Patil", "mobile": _unique_mobile(), "password": "secret123",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["access_token"]
    assert body["user"]["name"] == "Asha Patil"
    assert "password" not in body["user"]


def test_register_rejects_duplicate_mobile(client):
    mobile = _unique_mobile()
    payload = {"name": "First", "mobile": mobile, "password": "secret123"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    r = client.post("/api/auth/register", json={**payload, "name": "Second"})
    assert r.status_code == 409


def test_register_rejects_non_numeric_mobile(client):
    r = client.post("/api/auth/register", json={
        "name": "X", "mobile": "abcdefghij", "password": "secret123",
    })
    assert r.status_code == 422


def test_register_rejects_short_password(client):
    r = client.post("/api/auth/register", json={
        "name": "X", "mobile": _unique_mobile(), "password": "abc",
    })
    assert r.status_code == 422


def test_login_success_and_wrong_password(client):
    mobile = _unique_mobile()
    client.post("/api/auth/register", json={
        "name": "Ravi", "mobile": mobile, "password": "secret123",
    })
    ok = client.post("/api/auth/login", json={"mobile": mobile, "password": "secret123"})
    assert ok.status_code == 200
    bad = client.post("/api/auth/login", json={"mobile": mobile, "password": "wrong"})
    assert bad.status_code == 401


def test_session_requires_token(client):
    assert client.get("/api/auth/session").status_code == 401


def test_session_with_token(authed_client):
    r = authed_client.get("/api/auth/session")
    assert r.status_code == 200
    assert r.json()["name"] == "Test Farmer"


def test_language_update(authed_client):
    r = authed_client.put("/api/auth/language", json={"language": "mr"})
    assert r.status_code == 200
    assert r.json()["language"] == "mr"
    bad = authed_client.put("/api/auth/language", json={"language": "fr"})
    assert bad.status_code == 422


def test_foreign_data_is_404_not_403(client, authed_client):
    """User B must never see user A's farm — indistinguishable from missing."""
    r = authed_client.post("/api/farms", json={"name": "A's farm", "area_acres": 2})
    farm_id = r.json()["id"]
    other = client.post("/api/auth/register", json={
        "name": "Bee", "mobile": _unique_mobile(), "password": "secret123"})
    assert other.status_code == 201, other.text
    headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    assert client.get(f"/api/farms/{farm_id}", headers=headers).status_code == 404
