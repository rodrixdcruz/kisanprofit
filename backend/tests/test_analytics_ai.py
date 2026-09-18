"""Analytics + Kisan AI: dashboard, simulator, insights, grounded chat."""
import random

import pytest


def _unique_mobile() -> str:
    return f"9{random.randint(10**8, 10**9 - 1)}"


def _seed_two_crops(authed_client):
    """Returns (cotton_id, soy_id) with realistic expenses/sales."""
    farm = authed_client.post("/api/farms", json={"name": "F", "area_acres": 10}).json()
    cotton = authed_client.post(f"/api/farms/{farm['id']}/crops", json={
        "name": "Cotton", "area_acres": 4, "expected_yield_quintal": 24}).json()
    authed_client.post("/api/expenses", json={"category": "seeds", "amount": 5000, "crop_id": cotton["id"]})
    authed_client.post("/api/expenses", json={"category": "fertilizer", "amount": 12000, "crop_id": cotton["id"]})
    authed_client.post(f"/api/crops/{cotton['id']}/production", json={
        "harvest_date": "2026-09-10", "actual_yield_quintal": 22})
    authed_client.post(f"/api/crops/{cotton['id']}/sales", json={
        "sale_date": "2026-09-12", "quantity_quintal": 22, "price_per_quintal": 7400,
        "transport_cost": 1400})

    soy = authed_client.post(f"/api/farms/{farm['id']}/crops", json={
        "name": "Soybean", "area_acres": 3, "expected_yield_quintal": 18}).json()
    authed_client.post("/api/expenses", json={"category": "seeds", "amount": 3600, "crop_id": soy["id"]})
    return cotton["id"], soy["id"]


def test_dashboard_totals(authed_client):
    cotton_id, soy_id = _seed_two_crops(authed_client)
    d = authed_client.get("/api/analytics/dashboard").json()
    assert d["total_investment"] == 20600
    assert d["total_revenue"] == 161400  # 22*7400 - 1400
    assert d["net_profit"] == 140800
    assert d["active_crops"] == 1 and d["total_farms"] == 1
    assert d["largest_category"] == "fertilizer"


def test_crop_profitability_shape(authed_client):
    cotton_id, _ = _seed_two_crops(authed_client)
    rows = authed_client.get("/api/analytics/crops").json()
    cotton = next(r for r in rows if r["crop_id"] == cotton_id)
    assert cotton["profit"] == 144400  # 161400 revenue - 17000 costs
    assert cotton["production_variance_percent"] == pytest.approx(-8.3, abs=0.1)
    assert cotton["break_even_price_per_quintal"] == pytest.approx((17000 + 1400) / 22, abs=0.5)


def test_comparison_flags_best(authed_client):
    _seed_two_crops(authed_client)
    rows = authed_client.get("/api/analytics/comparison").json()
    assert len(rows) == 2
    assert sum(1 for r in rows if r["is_best"]) == 1


def test_simulator_scenario(authed_client):
    cotton_id, _ = _seed_two_crops(authed_client)
    r = authed_client.post(f"/api/analytics/simulator/{cotton_id}", json={
        "price_per_quintal": 7500, "cost_multiplier": 1.1})
    body = r.json()
    assert body["revenue"] == 165000
    assert body["total_cost"] == pytest.approx(18700)
    assert body["profit"] == pytest.approx(146300)


def test_insights_cover_variance(authed_client):
    _seed_two_crops(authed_client)
    insights = authed_client.get("/api/analytics/insights").json()
    titles = " ".join(i["title"] for i in insights)
    assert "below expected yield" in titles
    assert all(i["severity"] in ("info", "good", "warning") for i in insights)


def test_insights_empty_state(authed_client):
    insights = authed_client.get("/api/analytics/insights").json()
    assert insights and "No data yet" in insights[0]["title"]


def test_chat_answers_from_records_only(authed_client):
    _seed_two_crops(authed_client)
    r = authed_client.post("/api/ai/chat", json={"message": "Where am I spending the most?"})
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "offline"
    assert "12,000" in body["answer"] or "fertilizer" in body["answer"].lower()


def test_chat_no_data_is_honest(client):
    other = client.post("/api/auth/register", json={
        "name": "Fresh", "mobile": _unique_mobile(), "password": "secret123"})
    headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    r = client.post("/api/ai/chat", json={"message": "What's my profit?"}, headers=headers)
    assert "don't have any farm data" in r.json()["answer"]


def test_chat_history_recorded(authed_client):
    authed_client.post("/api/ai/chat", json={"message": "Which crop does best?"})
    h = authed_client.get("/api/ai/history").json()
    assert len(h) >= 1 and h[0]["provider"] == "offline"


def test_chat_requires_auth(client):
    assert client.post("/api/ai/chat", json={"message": "hi"}).status_code == 401
