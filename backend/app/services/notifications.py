"""Notification generation: harvest-due reminders and high-expense alerts.

Runs opportunistically on dashboard/API hits (lifespan task also seeds the
demo user); everything is per-user and idempotent-ish (only creates a
notification when none unread of the same kind exists for the subject).
"""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.models import Crop, Expense, Farm, Notification

# An expense above this fraction of the crop's running total is flagged.
HIGH_EXPENSE_FRACTION = 0.35
HIGH_EXPENSE_ABSOLUTE = 20_000.0


def _has_unread(db: Session, user_id: int, kind: str, title: str) -> bool:
    return bool(
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.kind == kind,
                Notification.title == title, Notification.read_at.is_(None))
        .first()
    )


def notify_harvest_due(db: Session, user) -> None:
    """Crops within 30 days of a full season (assumed 120 days from sowing)."""
    horizon = date.today() + timedelta(days=30)
    for crop in db.query(Crop).join(Farm, Crop.farm_id == Farm.id).filter(Farm.owner_id == user.id).all():
        if crop.status != "active" or not crop.sowing_date:
            continue
        expected = crop.sowing_date + timedelta(days=120)
        if date.today() <= expected <= horizon:
            title = f"{crop.name}: harvest window approaching"
            if not _has_unread(db, user.id, "harvest_due", title):
                db.add(Notification(
                    user_id=user.id, kind="harvest_due", title=title,
                    body=(f"Sown {crop.sowing_date.isoformat()}; expected around "
                          f"{expected.isoformat()}. Plan labor and logistics."),
                ))
    db.commit()


def notify_high_expense(db: Session, user, expense: Expense) -> None:
    """Flag a single unusually large expense right after it is recorded."""
    total = sum(e.amount for e in db.query(Expense).filter(Expense.user_id == user.id).all())
    if expense.amount >= HIGH_EXPENSE_ABSOLUTE or (total > 0 and expense.amount / total >= HIGH_EXPENSE_FRACTION):
        title = f"High expense recorded: {expense.category}"
        if not _has_unread(db, user.id, "high_expense", title):
            db.add(Notification(
                user_id=user.id, kind="high_expense", title=title,
                body=f"{expense.category}: {expense.amount:,.0f} on {expense.spent_on.isoformat()}. "
                     "Check it matches your records.",
            ))
    db.commit()
