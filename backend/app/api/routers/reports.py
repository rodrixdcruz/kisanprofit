"""Reports: crop PDF, summary PDFs, CSV exports."""
from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_owned_crop
from app.core.db import get_db
from app.models.models import Expense, Sale, User
from app.services.finance import compute_crop_financials
from app.services.reports import _money, crop_profitability_pdf, csv_bytes, summary_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


def _pdf(title: str, headers: list[str], rows: list[list[str]]) -> Response:
    return Response(
        content=summary_pdf(title, headers, rows),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{title.lower().replace(" ", "_")}.pdf"'},
    )


def _csv(title: str, headers: list[str], rows: list[list[str]]) -> Response:
    return Response(
        content=csv_bytes(headers, rows),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{title.lower().replace(" ", "_")}.csv"'},
    )


@router.get("/crop/{crop_id}/pdf")
def crop_pdf(crop_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    crop = require_owned_crop(db, user, crop_id)
    fin = compute_crop_financials(crop, crop.expenses, crop.productions, crop.sales)
    return Response(
        content=crop_profitability_pdf(crop.name, fin),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="crop_{crop.name.lower()}.pdf"'},
    )


@router.get("/expenses/pdf")
def expenses_pdf(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    exps = db.query(Expense).filter(Expense.user_id == user.id).order_by(Expense.spent_on.desc()).all()
    rows = [[e.spent_on.isoformat(), e.category, _money(e.amount), e.note or ""] for e in exps]
    return _pdf("Expense Report", ["Date", "Category", "Amount", "Note"], rows)


@router.get("/expenses/csv")
def expenses_csv(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    exps = db.query(Expense).filter(Expense.user_id == user.id).order_by(Expense.spent_on.desc()).all()
    rows = [[e.spent_on.isoformat(), e.category, f"{e.amount:.2f}", e.note or ""] for e in exps]
    return _csv("Expense Export", ["date", "category", "amount", "note"], rows)


@router.get("/sales/pdf")
def sales_pdf(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sales = db.query(Sale).filter(Sale.user_id == user.id).order_by(Sale.sale_date.desc()).all()
    rows = []
    for s in sales:
        net = s.quantity_quintal * s.price_per_quintal - s.transport_cost - s.other_charges
        rows.append([s.sale_date.isoformat(), s.crop.name, f"{s.quantity_quintal:.2f} q",
                     _money(s.price_per_quintal), _money(net)])
    return _pdf("Sales Report", ["Date", "Crop", "Qty", "Price/q", "Net revenue"], rows)


def _period_rows(db: Session, user: User, since: date):
    exps = db.query(Expense).filter(Expense.user_id == user.id, Expense.spent_on >= since).all()
    sales = db.query(Sale).filter(Sale.user_id == user.id, Sale.sale_date >= since).all()
    spent = sum(e.amount for e in exps)
    earned = sum(s.quantity_quintal * s.price_per_quintal - s.transport_cost - s.other_charges for s in sales)
    return [["Expenses", _money(spent)], ["Net revenue", _money(earned)],
            ["Net profit", _money(earned - spent)]]


@router.get("/monthly/pdf")
def monthly_pdf(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = date.today()
    since = today.replace(day=1)
    return _pdf("Monthly Summary", ["Metric", "Value"], _period_rows(db, user, since))


@router.get("/seasonal/pdf")
def seasonal_pdf(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = date.today()
    # Kharif (Jun-Oct) / rabi (Nov-Mar) rough season start
    if 6 <= today.month <= 10:
        season_start = date(today.year, 6, 1)
    elif today.month >= 11:
        season_start = date(today.year, 11, 1)
    else:
        season_start = date(today.year - 1, 11, 1)
    return _pdf("Seasonal Summary", ["Metric", "Value"], _period_rows(db, user, season_start))


@router.get("/annual/pdf")
def annual_pdf(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    since = date.today().replace(month=1, day=1)
    return _pdf("Annual Summary", ["Metric", "Value"], _period_rows(db, user, since))
