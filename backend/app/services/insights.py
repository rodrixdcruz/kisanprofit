"""Deterministic insights — computed from real data only, never invented.

An LLM (if configured) may rephrase `detail`, never change the numbers.
"""
from app.services.finance import CropFinancials


def build_insights(financials: list[CropFinancials]) -> list[dict]:
    insights: list[dict] = []
    if not financials:
        insights.append({
            "title": "No data yet",
            "detail": "Add your first expense or sale and insights will appear here.",
            "severity": "info",
        })
        return insights

    # 1. Expense concentration
    by_cat: dict[str, float] = {}
    for f in financials:
        for cat, amt in f.expense_by_category.items():
            by_cat[cat] = by_cat.get(cat, 0.0) + amt
    if by_cat:
        total = sum(by_cat.values())
        cat = max(by_cat, key=by_cat.get)
        amt = by_cat[cat]
        share = amt / total * 100 if total > 0 else 0.0
        if share >= 40:
            insights.append({
                "title": f"{cat.title()} dominates spending",
                "detail": (f"{cat.title()} is {share:.0f}% of all expenses "
                           f"(₹{amt:,.0f}). Compare with neighbors' costs or look for savings here first."),
                "severity": "warning" if share >= 55 else "info",
            })
        else:
            top3 = sorted(by_cat.items(), key=lambda kv: -kv[1])[:3]
            spending = ", ".join(f"{c}: ₹{a:,.0f}" for c, a in top3)
            insights.append({
                "title": "Where money goes",
                "detail": f"Top categories — {spending}.",
                "severity": "info",
            })

    # 2. Production variance
    for f in financials:
        if f.production_variance_percent is None:
            continue
        v = f.production_variance_percent
        if v <= -5:
            insights.append({
                "title": f"{f.crop_name}: below expected yield",
                "detail": (f"{abs(v):.1f}% below expectation "
                           f"({f.produced_quintal:.1f} vs {f.expected_yield_quintal:.1f} q). "
                           "Check seed quality, irrigation, pests."),
                "severity": "warning",
            })
        elif v >= 5:
            practices = ("pests were controlled, irrigation was timely, and the seed variety matched the season"
                         if v >= 20 else
                         "irrigation and inputs were well timed")
            insights.append({
                "title": f"{f.crop_name}: above expected yield",
                "detail": (f"{v:.1f}% above expectation "
                           f"({f.produced_quintal:.1f} vs {f.expected_yield_quintal:.1f} q) — {practices}. "
                           "Note what worked this season."),
                "severity": "good",
            })

    # 3. Break-even margin
    for f in financials:
        if f.break_even_price_per_quintal and f.sold_quintal > 0:
            gross = f.gross_revenue + f.selling_costs
            realized = gross / f.sold_quintal
            be = f.break_even_price_per_quintal
            margin = (realized - be) / be * 100
            if margin < -5:
                insights.append({
                    "title": f"{f.crop_name}: sold below break-even",
                    "detail": (f"Realized ₹{realized:,.0f}/q vs break-even ₹{be:,.0f}/q ({margin:.0f}%). "
                               "Next season, hold for better prices or cut the biggest cost."),
                    "severity": "warning",
                })
            elif margin > 5:
                insights.append({
                    "title": f"{f.crop_name}: healthy margin over break-even",
                    "detail": (f"Realized ₹{realized:,.0f}/q vs break-even ₹{be:,.0f}/q ({margin:.0f}%). "
                               "This crop pays well."),
                    "severity": "good",
                })

    # 4. Unsold harvest nudge
    for f in financials:
        unsold = f.produced_quintal - f.sold_quintal
        if unsold > 0.5:
            insights.append({
                "title": f"{f.crop_name}: {unsold:.1f} quintal unsold",
                "detail": f"{unsold:.1f} q harvested but not yet sold. Record the sale to see true profit.",
                "severity": "info",
            })

    # 5. Best performer
    with_data = [f for f in financials if f.total_cost > 0 or f.sold_quintal > 0]
    if len(with_data) >= 2:
        best = max(with_data, key=lambda f: f.profit_per_acre)
        insights.append({
            "title": f"{best.crop_name} is your best performer",
            "detail": f"Highest profit per acre (₹{best.profit_per_acre:,.0f}/acre). "
                      "Consider what makes it work before expanding others.",
            "severity": "good",
        })

    return insights
