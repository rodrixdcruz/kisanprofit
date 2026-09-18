"""Farms & crops CRUD: ownership scoping, validation, lifecycle transitions."""
import random

import pytest


def _unique_mobile() -> str:
    return f"9{random.randint(10**8, 10**9 - 1)}"


def _make_farm(client, name="Test Farm") -> int:
    r = client.post("/api/farms", json={"name": name, "area_acres": 5})
    assert r.status_code == 201
    return r.json()["id"]


def test_farm_requires_auth(client):
    assert client.get("/api/farms").status_code == 401


def test_farm_create_list_get_delete(authed_client):
    farm_id = _make_farm(authed_client, "Backyard")
    farms = authed_client.get("/api/farms").json()
    assert len(farms) == 1 and farms[0]["name"] == "Backyard"
    assert authed_client.get(f"/api/farms/{farm_id}").status_code == 200
    assert authed_client.delete(f"/api/farms/{farm_id}").status_code == 204
    assert authed_client.get(f"/api/farms/{farm_id}").status_code == 404


def test_farm_validation(authed_client):
    assert authed_client.post("/api/farms", json={"name": "", "area_acres": 1}).status_code == 422
    assert authed_client.post("/api/farms", json={"name": "X", "area_acres": -2}).status_code == 422


def test_crop_lifecycle(authed_client):
    farm_id = _make_farm(authed_client)
    r = authed_client.post(f"/api/farms/{farm_id}/crops", json={
        "name": "Cotton", "area_acres": 2,
        "sowing_date": "2026-06-01", "expected_yield_quintal": 20,
        "expected_price_per_quintal": 7500,
    })
    assert r.status_code == 201
    crop = r.json()
    assert crop["status"] == "active"

    r2 = authed_client.patch(
        f"/api/farms/{farm_id}/crops/{crop['id']}/status?status=harvested")
    assert r2.status_code == 200 and r2.json()["status"] == "harvested"

    bad = authed_client.patch(
        f"/api/farms/{farm_id}/crops/{crop['id']}/status?status=weird")
    assert bad.status_code == 422


def test_crop_cannot_escape_farm_ownership(client, authed_client):
    farm_id = _make_farm(authed_client)
    r = authed_client.post(f"/api/farms/{farm_id}/crops", json={"name": "Wheat", "area_acres": 1})
    crop_id = r.json()["id"]
    other = client.post("/api/auth/register", json={
        "name": "Other", "mobile": _unique_mobile(), "password": "secret123"})
    headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    assert client.get(f"/api/farms/{farm_id}/crops/{crop_id}", headers=headers).status_code == 404


def test_harvest_flips_active_to_harvested(authed_client):
    farm_id = _make_farm(authed_client)
    crop = authed_client.post(f"/api/farms/{farm_id}/crops", json={
        "name": "Soy", "area_acres": 1}).json()
    r = authed_client.post(f"/api/crops/{crop['id']}/production", json={
        "harvest_date": "2026-09-10", "actual_yield_quintal": 12})
    assert r.status_code == 201
    refreshed = authed_client.get(f"/api/farms/{farm_id}/crops/{crop['id']}").json()
    assert refreshed["status"] == "harvested"
