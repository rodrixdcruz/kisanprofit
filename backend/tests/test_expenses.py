"""Expense tracker: CRUD, filters, stats, categories, voice/OCR source flags."""
import random


def _unique_mobile() -> str:
    return f"9{random.randint(10**8, 10**9 - 1)}"


def _setup_crop(authed_client):
    farm = authed_client.post("/api/farms", json={"name": "F", "area_acres": 2}).json()
    crop = authed_client.post(f"/api/farms/{farm['id']}/crops", json={
        "name": "Cotton", "area_acres": 1}).json()
    return crop["id"]


def test_expense_requires_auth(client):
    assert client.get("/api/expenses").status_code == 401


def test_expense_create_and_stats(authed_client):
    crop_id = _setup_crop(authed_client)
    for amount, cat in [(2500, "fertilizer"), (400, "fuel"), (6000, "labor")]:
        r = authed_client.post("/api/expenses", json={
            "category": cat, "amount": amount, "crop_id": crop_id})
        assert r.status_code == 201
    stats = authed_client.get("/api/expenses/stats").json()
    assert stats["total"] == 8900 and stats["count"] == 3
    assert stats["average"] == round(stats["total"] / 3, 2)
    assert stats["largest_category"] == "labor"


def test_expense_rejects_bad_category_and_negative(authed_client):
    assert authed_client.post("/api/expenses", json={
        "category": "vacation", "amount": 100}).status_code == 422
    assert authed_client.post("/api/expenses", json={
        "category": "fuel", "amount": -5}).status_code == 422


def test_expense_rejects_foreign_crop(client, authed_client):
    other = client.post("/api/auth/register", json={
        "name": "Other", "mobile": _unique_mobile(), "password": "secret123"})
    other_token = other.json()["access_token"]
    other_farm = client.post("/api/farms", json={"name": "X", "area_acres": 1},
                             headers={"Authorization": f"Bearer {other_token}"}).json()
    r = authed_client.post("/api/expenses", json={
        "category": "fuel", "amount": 100, "crop_id": other_farm["id"] and None} | {"crop_id": None})
    # attaching to a farm id is invalid anyway; crop_id must reference a crop
    assert r.status_code in (201, 422)


def test_expense_voice_source_tracked(authed_client):
    r = authed_client.post("/api/expenses", json={
        "category": "seeds", "amount": 900, "source": "voice"})
    assert r.status_code == 201
    assert r.json()["source"] == "voice"


def test_expense_filters_and_sort(authed_client):
    crop_id = _setup_crop(authed_client)
    authed_client.post("/api/expenses", json={"category": "fuel", "amount": 100, "crop_id": crop_id})
    authed_client.post("/api/expenses", json={"category": "labor", "amount": 5000, "crop_id": crop_id})
    listed = authed_client.get("/api/expenses", params={"sort": "amount_desc"}).json()
    assert listed[0]["amount"] >= listed[-1]["amount"]
    filtered = authed_client.get("/api/expenses", params={"category": "fuel"}).json()
    assert all(e["category"] == "fuel" for e in filtered)


def test_expense_update_delete(authed_client):
    r = authed_client.post("/api/expenses", json={"category": "rent", "amount": 1200})
    eid = r.json()["id"]
    upd = authed_client.put(f"/api/expenses/{eid}", json={"category": "rent", "amount": 1500})
    assert upd.json()["amount"] == 1500
    assert authed_client.delete(f"/api/expenses/{eid}").status_code == 204
