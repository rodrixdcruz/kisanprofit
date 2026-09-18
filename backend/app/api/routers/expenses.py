"""Expenses: CRUD + search/filter/sort + stats + high-expense alerts."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import (get_current_user, require_owned_crop,
                          require_writable_user)
from app.core.db import get_db
from app.models.models import Expense, User
from app.schemas.schemas import ExpenseCreate, ExpenseOut
from app.services.notifications import notify_high_expense

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("", response_model=list[ExpenseOut])
def list_expenses(
    crop_id: int | None = None,
    category: str | None = None,
    search: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    sort: str = "date_desc",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Expense).filter(Expense.user_id == user.id)
    if crop_id is not None:
        q = q.filter(Expense.crop_id == crop_id)
    if category:
        q = q.filter(Expense.category == category)
    if date_from:
        q = q.filter(Expense.spent_on >= date_from)
    if date_to:
        q = q.filter(Expense.spent_on <= date_to)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Expense.note.ilike(like), Expense.category.ilike(like)))
    if sort == "date_asc":
        q = q.order_by(Expense.spent_on.asc())
    elif sort == "amount_desc":
        q = q.order_by(Expense.amount.desc())
    elif sort == "amount_asc":
        q = q.order_by(Expense.amount.asc())
    else:
        q = q.order_by(Expense.spent_on.desc(), Expense.id.desc())
    return q.all()


@router.post("", response_model=ExpenseOut, status_code=201)
def create_expense(payload: ExpenseCreate, user: User = Depends(require_writable_user),
                   db: Session = Depends(get_db)):
    if payload.crop_id is not None:
        require_owned_crop(db, user, payload.crop_id)
    expense = Expense(
        user_id=user.id,
        crop_id=payload.crop_id,
        category=payload.category,
        amount=payload.amount,
        spent_on=payload.spent_on or date.today(),
        note=payload.note,
        source=payload.source,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    notify_high_expense(db, user, expense)
    return expense


@router.get("/stats")
def expense_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    exps = db.query(Expense).filter(Expense.user_id == user.id).all()
    today = date.today()
    this_month = sum(e.amount for e in exps if e.spent_on.year == today.year and e.spent_on.month == today.month)
    by_cat: dict[str, float] = {}
    for e in exps:
        by_cat[e.category] = by_cat.get(e.category, 0.0) + e.amount
    largest = max(by_cat, key=by_cat.get) if by_cat else None
    return {
        "total": round(sum(e.amount for e in exps), 2),
        "count": len(exps),
        "this_month": round(this_month, 2),
        "average": round(sum(e.amount for e in exps) / len(exps), 2) if exps else 0.0,
        "largest_category": largest,
        "largest_category_amount": round(by_cat.get(largest, 0.0), 2) if largest else 0.0,
    }


@router.put("/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: int, payload: ExpenseCreate,
                   user: User = Depends(require_writable_user), db: Session = Depends(get_db)):
    exp = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == user.id).first()
    if not exp:
        raise HTTPException(404, "Expense not found")
    if payload.crop_id is not None:
        require_owned_crop(db, user, payload.crop_id)
    for k, v in payload.model_dump().items():
        if v is not None:
            setattr(exp, k, v)
    db.commit()
    db.refresh(exp)
    return exp


@router.delete("/{expense_id}", status_code=204)
def delete_expense(expense_id: int, user: User = Depends(require_writable_user),
                   db: Session = Depends(get_db)):
    exp = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == user.id).first()
    if not exp:
        raise HTTPException(404, "Expense not found")
    db.delete(exp)
    db.commit()
