"""The financial calculation engine.

All money math lives here — the frontend only formats and displays.
Every function is zero-safe: empty data yields zeros, never exceptions.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.models.models import Crop, Expense, Production, Sale


def _z(v: float | None) -> float:
    return float(v or 0.0)


@dataclass
class CropFinancials:
    crop_id: int
    crop_name: str
    area_acres: float
    total_cost: float = 0.0
    revenue: float = 0.0
    gross_revenue: float = 0.0
    selling_costs: float = 0.0
    profit: float = 0.0
    roi_percent: float = 0.0
    cost_per_acre: float = 0.0
    profit_per_acre: float = 0.0
    cost_per_quintal: float | None = None
    break_even_price_per_quintal: float | None = None
    produced_quintal: float = 0.0
    sold_quintal: float = 0.0
    expected_yield_quintal: float | None = None
    production_variance_percent: float | None = None
    expense_by_category: dict = field(default_factory=dict)


def compute_crop_financials(crop: Crop, expenses: list[Expense],
                            productions: list[Production], sales: list[Sale]) -> CropFinancials:
    """Full P&L for one crop: costs → revenue (net of selling costs) → profit → ratios."""
    f = CropFinancials(
        crop_id=crop.id,
        crop_name=crop.name,
        area_acres=_z(crop.area_acres) or 1.0,
        expected_yield_quintal=crop.expected_yield_quintal,
    )

    for e in expenses:
        f.total_cost += _z(e.amount)
        f.expense_by_category[e.category] = f.expense_by_category.get(e.category, 0.0) + _z(e.amount)

    for p in productions:
        f.produced_quintal += _z(p.actual_yield_quintal)

    for s in sales:
        f.gross_revenue += _z(s.quantity_quintal) * _z(s.price_per_quintal)
        f.selling_costs += _z(s.transport_cost) + _z(s.other_charges)
        f.sold_quintal += _z(s.quantity_quintal)

    f.revenue = f.gross_revenue - f.selling_costs
    f.profit = f.revenue - f.total_cost

    if f.total_cost > 0:
        f.roi_percent = f.profit / f.total_cost * 100.0
        f.cost_per_acre = f.total_cost / f.area_acres
        f.cost_per_quintal = f.total_cost / f.produced_quintal if f.produced_quintal > 0 else None
        f.break_even_price_per_quintal = (
            (f.total_cost + f.selling_costs) / f.produced_quintal
            if f.produced_quintal > 0 else None
        )
    if f.area_acres > 0:
        f.profit_per_acre = f.profit / f.area_acres

    if f.expected_yield_quintal and f.expected_yield_quintal > 0 and f.produced_quintal > 0:
        f.production_variance_percent = (
            (f.produced_quintal - f.expected_yield_quintal) / f.expected_yield_quintal * 100.0
        )
    return f


def portfolio(user, farms, crops, expenses, productions, sales, today) -> dict:
    """Dashboard totals across the whole farm portfolio."""
    total_investment = sum(_z(e.amount) for e in expenses)
    total_revenue = sum(
        _z(s.quantity_quintal) * _z(s.price_per_quintal) - _z(s.transport_cost) - _z(s.other_charges)
        for s in sales
    )
    net_profit = total_revenue - total_investment
    roi = (net_profit / total_investment * 100.0) if total_investment > 0 else 0.0

    month_expenses = [e for e in expenses
                      if e.spent_on and e.spent_on.year == today.year and e.spent_on.month == today.month]
    this_month = sum(_z(e.amount) for e in month_expenses)

    by_cat: dict[str, float] = {}
    for e in expenses:
        by_cat[e.category] = by_cat.get(e.category, 0.0) + _z(e.amount)
    largest_cat, largest_amt = (max(by_cat.items(), key=lambda kv: kv[1]) if by_cat else (None, 0.0))

    upcoming_harvests = 0
    for c in crops:
        if c.status == "active" and c.expected_yield_quintal and not c.productions:
            upcoming_harvests += 1
    pending_sales = 0
    for c in crops:
        produced = sum(_z(p.actual_yield_quintal) for p in c.productions)
        sold = sum(_z(s.quantity_quintal) for s in c.sales)
        if produced > sold:
            pending_sales += 1

    return {
        "total_investment": round(total_investment, 2),
        "total_revenue": round(total_revenue, 2),
        "net_profit": round(net_profit, 2),
        "roi_percent": round(roi, 2),
        "active_crops": sum(1 for c in crops if c.status == "active"),
        "total_farms": len(farms),
        "upcoming_harvests": upcoming_harvests,
        "pending_sales": pending_sales,
        "this_month_expenses": round(this_month, 2),
        "largest_category": largest_cat,
        "largest_category_amount": round(largest_amt, 2),
    }


def simulate(crop: Crop, financials: CropFinancials, price_per_quintal: float,
             production_quintal: float | None, cost_multiplier: float) -> dict:
    """What-if engine: try any price/production/cost scenario against one crop."""
    produced = production_quintal if production_quintal is not None else (
        financials.produced_quintal if financials.produced_quintal > 0 else _z(crop.expected_yield_quintal)
    )
    cost = financials.total_cost * cost_multiplier
    revenue = produced * price_per_quintal
    profit = revenue - cost
    return {
        "revenue": round(revenue, 2),
        "total_cost": round(cost, 2),
        "profit": round(profit, 2),
        "break_even_price_per_quintal": round(cost / produced, 2) if produced > 0 else 0.0,
        "sold_out": produced <= financials.sold_quintal if financials.sold_quintal > 0 else False,
    }


def comparison(rows: list[CropFinancials]) -> list[dict]:
    """Side-by-side crop metrics with the best performer flagged."""
    if not rows:
        return []
    best = max(rows, key=lambda f: f.profit_per_acre)
    out = []
    for f in sorted(rows, key=lambda f: f.profit_per_acre, reverse=True):
        out.append({
            "crop_name": f.crop_name,
            "profit": round(f.profit, 2),
            "roi_percent": round(f.roi_percent, 2),
            "profit_per_acre": round(f.profit_per_acre, 2),
            "is_best": f is best,
        })
    return out
