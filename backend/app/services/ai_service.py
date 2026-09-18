"""Kisan AI — chat answered from the farmer's own data.

The deterministic engine is authoritative: it computes every figure from the
user's records. When an LLM key is configured (AI_PROVIDER=auto/gemini/openai),
the LLM only rephrases the already-computed answer under a strict prompt.
"""
import json
import logging
import re
from urllib import request as urlrequest

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.models import Crop, Expense, Farm, Production, Sale
from app.services.finance import compute_crop_financials

log = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------- helpers
def _load_user_context(db: Session, user) -> list[dict]:
    """Compute financials for all the user's crops (for grounding)."""
    crops = (
        db.query(Crop)
        .join(Farm, Crop.farm_id == Farm.id)
        .filter(Farm.owner_id == user.id)
        .all()
    )
    out = []
    for c in crops:
        expenses = c.expenses
        productions = c.productions
        sales = c.sales
        out.append({
            "crop": c,
            "fin": compute_crop_financials(c, expenses, productions, sales),
        })
    return out


# ---------------------------------------------------------------- offline engine
def _offline_answer(question: str, ctx: list[dict]) -> str:
    q = question.lower()

    def all_expenses():
        return [e for item in ctx for e in item["crop"].expenses]

    def all_sales():
        return [s for item in ctx for s in item["crop"].sales]

    def fmt(n: float) -> str:
        return f"₹{n:,.0f}"

    if not ctx:
        return ("I don't have any farm data yet. Add a farm and crop first, then ask me "
                "about your spending, profit, or prices.")

    # spending / expense questions
    if re.search(r"spend|expense|kharch|खर्च|खर्चा", q):
        exps = all_expenses()
        if not exps:
            return "You haven't recorded any expenses yet."
        total = sum(e.amount for e in exps)
        by_cat: dict[str, float] = {}
        for e in exps:
            by_cat[e.category] = by_cat.get(e.category, 0.0) + e.amount
        top = max(by_cat, key=by_cat.get)
        share = by_cat[top] / total * 100
        detail = ", ".join(f"{c}: {fmt(a)}" for c, a in sorted(by_cat.items(), key=lambda kv: -kv[1])[:3])
        return (f"Total expenses so far: {fmt(total)}. You spend the most on {top} — "
                f"{fmt(by_cat[top])} ({share:.0f}%). Top categories: {detail}.")

    # profit questions
    if re.search(r"profit|munafa|नफ़ा|नफा|न्हफा|मुनाफ़ा|मुनाफा", q):
        total_profit = sum(i["fin"].profit for i in ctx)
        best = max(ctx, key=lambda i: i["fin"].profit_per_acre)
        lines = [f"Net profit across all crops: {fmt(total_profit)}."]
        for i in ctx:
            f = i["fin"]
            lines.append(f"{f.crop_name}: {fmt(f.profit)} ({f.roi_percent:.0f}% ROI, "
                         f"{fmt(f.profit_per_acre)}/acre)")
        lines.append(f"Best performer: {best['fin'].crop_name} at {fmt(best['fin'].profit_per_acre)}/acre.")
        return "\n".join(lines)

    # price questions
    if re.search(r"price|rate|भाव|दर|कीमत", q):
        parts = []
        for i in ctx:
            f = i["fin"]
            if f.sold_quintal > 0:
                gross = f.gross_revenue + f.selling_costs
                realized = gross / f.sold_quintal
                parts.append(f"{f.crop_name}: sold at {fmt(realized)}/quintal")
            elif f.break_even_price_per_quintal:
                parts.append(f"{f.crop_name}: not sold yet; break-even is {fmt(f.break_even_price_per_quintal)}/q — "
                             "sell above this to profit")
        return "\n".join(parts) if parts else "No sales recorded yet, so I can't quote realized prices."

    # best crop
    if re.search(r"best|top|worst", q):
        with_data = [i for i in ctx if i["fin"].total_cost > 0 or i["fin"].sold_quintal > 0]
        if len(with_data) < 2:
            return "I need at least two crops with data to compare."
        best = max(with_data, key=lambda i: i["fin"].profit_per_acre)
        worst = min(with_data, key=lambda i: i["fin"].profit_per_acre)
        return (f"{best['fin'].crop_name} performs best ({fmt(best['fin'].profit_per_acre)}/acre). "
                f"{worst['fin'].crop_name} trails ({fmt(worst['fin'].profit_per_acre)}/acre).")

    # help / fallback
    return (
        "I can answer from your own records — try:\n"
        "- \"Where am I spending the most?\"\n"
        "- \"What's my profit on cotton?\"\n"
        "- \"At what price did I sell soybean?\"\n"
        "- \"Which crop does best?\"\n\n"
        "I never invent numbers — I only report what you've recorded."
    )


# ---------------------------------------------------------------- LLM rephrasing
GROUNDING_PROMPT = (
    "You are Kisan AI, an assistant for Indian farmers. You will receive a farmer's question "
    "and a computed answer containing the REAL figures from their records. "
    "Restate the answer warmly and clearly in the same language as the question. "
    "You MUST use exactly the figures given — do NOT invent, round differently, or add any "
    "numbers not present. If the answer says data is missing, say that. Keep it under 120 words."
)


def _call_llm(question: str, computed: str) -> str | None:
    """Best-effort rephrase; any failure keeps the deterministic answer."""
    provider = settings.AI_PROVIDER
    try:
        if provider in ("gemini", "auto") and settings.GEMINI_API_KEY:
            url = ("https://generativelanguage.googleapis.com/v1beta/models/"
                   f"gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}")
            body = json.dumps({
                "contents": [{"parts": [{"text": f"{GROUNDING_PROMPT}\n\nQuestion: {question}\n\nComputed answer:\n{computed}"}]}],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 300},
            }).encode()
            req = urlrequest.Request(url, data=body, headers={"Content-Type": "application/json"})
            with urlrequest.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return text.strip() or None
        if provider == "openai" and settings.OPENAI_API_KEY:
            url = "https://api.openai.com/v1/chat/completions"
            body = json.dumps({
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": GROUNDING_PROMPT},
                    {"role": "user", "content": f"Question: {question}\n\nComputed answer:\n{computed}"},
                ],
                "temperature": 0.3,
                "max_tokens": 300,
            }).encode()
            req = urlrequest.Request(url, data=body, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            })
            with urlrequest.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            text = data["choices"][0]["message"]["content"]
            return text.strip() or None
    except Exception as exc:  # noqa: BLE001 - LLM failure must never break chat
        log.warning("LLM rephrase failed (%s); using deterministic answer", exc)
    return None


def answer_question(db: Session, user, question: str) -> tuple[str, str]:
    """Returns (answer, provider). provider: offline | gemini | openai."""
    ctx = _load_user_context(db, user)
    computed = _offline_answer(question, ctx)
    if settings.AI_PROVIDER == "offline":
        return computed, "offline"
    rephrased = _call_llm(question, computed)
    if rephrased:
        return rephrased, settings.AI_PROVIDER if settings.AI_PROVIDER in ("gemini", "openai") else "gemini"
    return computed, "offline"
