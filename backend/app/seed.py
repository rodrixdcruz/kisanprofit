"""Demo data seeding — idempotent, runs at startup when SEED_DEMO_DATA=true.

The numbers are engineered so the README's 60-second judge walkthrough
reconciles exactly:
- 14 expenses totaling ₹80,000 (after the walkthrough's ₹2,500 fertilizer
  add: 15 expenses, ₹82,500 total, ₹5,500 average — as documented);
- cotton produced 22 q against a 24 q expectation (exactly −8.3% variance);
- net profit ₹85,400 at login on ₹165,400 net revenue;
- wheat has an unsold balance (pending sale) and soybean is the active crop
  inside its harvest window (feeds "upcoming harvests" + the reminder).
"""
import logging
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.models import (Crop, Expense, Farm, Notification, Production,
                               Sale, User)

log = logging.getLogger(__name__)
settings = get_settings()

DEMO_MOBILE = "9999999999"
DEMO_PASSWORD = "demo1234"


def seed_demo_data(db: Session) -> None:
    if settings.SEED_DEMO_DATA.lower() not in ("1", "true", "yes"):
        return
    if db.query(User).filter(User.mobile == DEMO_MOBILE).first():
        return  # already seeded

    farmer = User(
        name="Demo Farmer",
        mobile=DEMO_MOBILE,
        password_hash=hash_password(DEMO_PASSWORD),
        language="en",
        is_demo=True,
    )
    db.add(farmer)
    db.flush()

    farm = Farm(
        owner_id=farmer.id, name="Akola Main Farm", area_acres=10.0,
        latitude=20.7002, longitude=77.0082, village="Akola",
    )
    db.add(farm)
    db.flush()

    # ---- Cotton: harvested & sold. Expected 24 q -> produced 22 q (-8.3%). ----
    cotton = Crop(
        farm_id=farm.id, name="Cotton", area_acres=4.0,
        sowing_date=date(2026, 5, 20), expected_yield_quintal=24.0,
        expected_price_per_quintal=7500.0, status="harvested",
    )
    db.add(cotton)
    db.flush()
    for cat, amt, day in [
        ("seeds", 5000.0, date(2026, 5, 22)),
        ("fertilizer", 12000.0, date(2026, 6, 8)),
        ("pesticide", 7000.0, date(2026, 7, 2)),
        ("labor", 14000.0, date(2026, 7, 18)),
        ("fuel", 4000.0, date(2026, 8, 5)),
        ("irrigation", 3000.0, date(2026, 8, 20)),
    ]:
        db.add(Expense(user_id=farmer.id, crop_id=cotton.id, category=cat,
                       amount=amt, spent_on=day, source="manual"))
    db.add(Production(crop_id=cotton.id, harvest_date=date(2026, 9, 10),
                      actual_yield_quintal=22.0, note="First picking"))
    db.add(Sale(user_id=farmer.id, crop_id=cotton.id, sale_date=date(2026, 9, 12),
                quantity_quintal=22.0, price_per_quintal=7400.0, transport_cost=1400.0,
                buyer="Akola Cotton Market"))

    # ---- Soybean: active, inside its harvest window. ----
    soybean = Crop(
        farm_id=farm.id, name="Soybean", area_acres=3.0,
        sowing_date=date(2026, 5, 30), expected_yield_quintal=18.0,
        expected_price_per_quintal=4800.0, status="active",
    )
    db.add(soybean)
    db.flush()
    for cat, amt, day in [
        ("seeds", 3600.0, date(2026, 6, 1)),
        ("fertilizer", 5400.0, date(2026, 6, 15)),
        ("labor", 6000.0, date(2026, 9, 5)),
        ("fuel", 1500.0, date(2026, 9, 10)),
    ]:
        db.add(Expense(user_id=farmer.id, crop_id=soybean.id, category=cat,
                       amount=amt, spent_on=day, source="manual"))

    # ---- Wheat: last rabi season, partially sold (pending balance). ----
    wheat = Crop(
        farm_id=farm.id, name="Wheat", area_acres=3.0,
        sowing_date=date(2025, 11, 15), expected_yield_quintal=12.0,
        expected_price_per_quintal=2600.0, status="harvested",
    )
    db.add(wheat)
    db.flush()
    for cat, amt, day in [
        ("seeds", 4000.0, date(2025, 11, 18)),
        ("fertilizer", 8500.0, date(2025, 12, 20)),
        ("labor", 5500.0, date(2026, 1, 15)),
        ("electricity", 500.0, date(2026, 2, 10)),
    ]:
        db.add(Expense(user_id=farmer.id, crop_id=wheat.id, category=cat,
                       amount=amt, spent_on=day, source="manual"))
    db.add(Production(crop_id=wheat.id, harvest_date=date(2026, 3, 25),
                      actual_yield_quintal=11.0))
    db.add(Sale(user_id=farmer.id, crop_id=wheat.id, sale_date=date(2026, 4, 2),
                quantity_quintal=2.0, price_per_quintal=2400.0, transport_cost=800.0))

    # ---- Notifications ----
    db.add(Notification(
        user_id=farmer.id, kind="system",
        title="Welcome to KisanProfit",
        body=("This is the demo farm. Explore the dashboard, add an expense, "
              "try the profit simulator, and ask Kisan AI about your data."),
    ))
    db.add(Notification(
        user_id=farmer.id, kind="high_expense",
        title="High expense recorded: fertilizer",
        body="Cotton fertilizer: 12,000 on 2026-06-08. Check it matches your records.",
    ))
    db.add(Notification(
        user_id=farmer.id, kind="harvest_due",
        title="Soybean: harvest window approaching",
        body="Sown 2026-05-30; expected around 2026-09-27. Plan labor and logistics.",
    ))

    db.commit()
    log.info("Demo farmer seeded (mobile %s)", DEMO_MOBILE)


def seed_at_startup() -> None:
    """Called from lifespan; creates tables then seeds the demo user."""
    from app.core.db import Base, SessionLocal, engine

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()
