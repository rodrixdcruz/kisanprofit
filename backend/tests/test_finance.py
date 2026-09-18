"""Finance engine edge cases — pure functions, no API."""
from datetime import date

import pytest

from app.models.models import Crop, Expense, Production, Sale
from app.services.finance import comparison, compute_crop_financials, portfolio, simulate


class FakeCrop:
    def __init__(self, cid=1, name="Cotton", area=2.0, expected=None):
        self.id, self.name, self.area_acres = cid, name, area
        self.expected_yield_quintal = expected


def _exp(amount, cat="fertilizer"):
    e = Expense()
    e.category, e.amount = cat, amount
    return e


def _sale(qty, price, transport=0.0, other=0.0):
    s = Sale()
    s.quantity_quintal, s.price_per_quintal = qty, price
    s.transport_cost, s.other_charges = transport, other
    return s


def _prod(qty):
    p = Production()
    p.actual_yield_quintal = qty
    return p


def test_empty_crop_is_all_zeros():
    f = compute_crop_financials(FakeCrop(), [], [], [])
    assert f.total_cost == 0 and f.revenue == 0 and f.profit == 0
    assert f.roi_percent == 0 and f.break_even_price_per_quintal is None


def test_profit_and_roi():
    crop = FakeCrop(area=2.0)
    f = compute_crop_financials(crop, [_exp(10000)], [], [_sale(10, 2000, transport=1000)])
    # revenue = 20000 - 1000 = 19000; profit = 9000; ROI = 90%
    assert f.revenue == 19000 and f.profit == 9000
    assert f.roi_percent == 90.0
    assert f.cost_per_acre == 5000 and f.profit_per_acre == 4500


def test_break_even_includes_selling_costs():
    crop = FakeCrop(area=1.0)
    f = compute_crop_financials(crop, [_exp(10000)], [_prod(10)], [_sale(10, 2000, 1000)])
    # (10000 cost + 1000 selling) / 10 q = 1100
    assert f.break_even_price_per_quintal == 1100.0
    assert f.cost_per_quintal == 1000.0


def test_production_variance_negative_and_positive():
    crop = FakeCrop(expected=24.0)
    f = compute_crop_financials(crop, [], [_prod(22)], [])
    assert f.production_variance_percent == pytest.approx(-8.33, abs=0.01)
    f2 = compute_crop_financials(FakeCrop(expected=10.0), [], [_prod(12)], [])
    assert f2.production_variance_percent == pytest.approx(20.0)


def test_variance_none_when_no_expectation():
    f = compute_crop_financials(FakeCrop(), [], [_prod(5)], [])
    assert f.production_variance_percent is None


def test_portfolio_totals_and_month_filter():
    class E:
        def __init__(self, a, d):
            self.amount, self.spent_on, self.category = a, d, "seeds"

    class S:
        def __init__(self, q, p, t=0.0, o=0.0):
            self.quantity_quintal, self.price_per_quintal = q, p
            self.transport_cost, self.other_charges = t, o

    today = date.today()
    expenses = [E(1000, today), E(500, date(today.year, today.month, 1)), E(999, date(2020, 1, 1))]
    sales = [S(10, 100)]
    totals = portfolio(object(), [], [], expenses, [], sales, today)
    assert totals["total_investment"] == 2499
    assert totals["total_revenue"] == 1000
    assert totals["net_profit"] == -1499
    assert totals["this_month_expenses"] == 1500
    assert totals["largest_category"] == "seeds"


def test_simulator_break_even_and_profit():
    crop = FakeCrop(area=2.0, expected=None)
    f = compute_crop_financials(crop, [_exp(10000)], [_prod(10)], [])
    out = simulate(crop, f, price_per_quintal=1500, production_quintal=None, cost_multiplier=1.0)
    assert out["revenue"] == 15000
    assert out["profit"] == 5000
    assert out["break_even_price_per_quintal"] == 1000.0


def test_comparison_flags_best_by_profit_per_acre():
    a = compute_crop_financials(FakeCrop(cid=1, name="A", area=1.0), [_exp(5000)], [], [_sale(5, 2000)])
    b = compute_crop_financials(FakeCrop(cid=2, name="B", area=2.0), [_exp(5000)], [], [_sale(5, 2000)])
    rows = comparison([a, b])
    assert rows[0]["crop_name"] == "A" and rows[0]["is_best"] is True
    assert rows[1]["is_best"] is False
