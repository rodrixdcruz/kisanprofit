"""Demo data seeding — idempotent, runs at startup when SEED_DEMO_DATA=true.

The numbers are engineered so the README's 60-second judge walkthrough
reconciles exactly:
- 14 expenses totaling ₹80,000, frozen at that value because the demo account
  is read-only (a visitor explores, they don't mutate);
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
from app.models.models import (AIConversation, Crop, Expense, Farm,
                               Notification, Production, Sale, User)

log = logging.getLogger(__name__)
settings = get_settings()

DEMO_MOBILE = "9999999999"
DEMO_PASSWORD = "demo1234"
DEMO_NAME = "Demo Farmer"


def _seeding_enabled() -> bool:
    return settings.SEED_DEMO_DATA.lower() in ("1", "true", "yes")


def seed_demo_data(db: Session) -> None:
    """Create the demo farm once; a no-op if it already exists."""
    if not _seeding_enabled():
        return
    if db.query(User).filter(User.mobile == DEMO_MOBILE).first():
        return  # already seeded
    _build_demo_farm(db, _get_or_create_demo_user(db))


def reseed_demo_data(db: Session) -> dict:
    """Rebuild the demo farm in place, on the same account row.

    The account itself is deliberately kept: JWTs are minted against the demo
    user's id, so deleting and recreating it would sign out any visitor who
    happened to be mid-walkthrough. Only the farm data — plus the demo's chat
    log and alerts — is wiped and rebuilt.

    The demo account is read-only at the API level, so drift should be
    impossible; this is the belt-and-braces pass that also covers anything a
    future code path (or a direct DB edit) might introduce. Returns a small
    non-secret summary for the caller's log.
    """
    if not _seeding_enabled():
        return {"status": "disabled", "detail": "SEED_DEMO_DATA is off"}
    farmer = _get_or_create_demo_user(db)
    removed = _purge_demo_farm_data(db, farmer)
    _restore_demo_credentials(db, farmer)
    _build_demo_farm(db, farmer)
    db.refresh(farmer)
    summary = {
        "status": "reseeded",
        "demo_user_id": farmer.id,
        "removed": removed,
        "expenses": db.query(Expense).filter(Expense.user_id == farmer.id).count(),
        "crops": (db.query(Crop).join(Farm, Crop.farm_id == Farm.id)
                  .filter(Farm.owner_id == farmer.id).count()),
    }
    log.info("Demo farm re-seeded: %s", summary)
    return summary


def _get_or_create_demo_user(db: Session) -> User:
    farmer = db.query(User).filter(User.mobile == DEMO_MOBILE).first()
    if farmer is None:
        farmer = User(name=DEMO_NAME, mobile=DEMO_MOBILE,
                      password_hash=hash_password(DEMO_PASSWORD),
                      language="en", is_demo=True)
        db.add(farmer)
        db.flush()
    return farmer


def _restore_demo_credentials(db: Session, farmer: User) -> None:
    """Put the canonical demo credentials back, in case they were edited."""
    farmer.name = DEMO_NAME
    farmer.is_demo = True
    farmer.password_hash = hash_password(DEMO_PASSWORD)
    db.commit()


def _purge_demo_farm_data(db: Session, farmer: User) -> dict:
    """Delete everything the demo account owns, except the account itself."""
    farm_ids = [row[0] for row in db.query(Farm.id).filter(Farm.owner_id == farmer.id)]
    crop_ids = ([row[0] for row in db.query(Crop.id).filter(Crop.farm_id.in_(farm_ids))]
                if farm_ids else [])
    counts = {
        "farms": len(farm_ids),
        "crops": len(crop_ids),
        "expenses": db.query(Expense).filter(Expense.user_id == farmer.id).count(),
        "sales": db.query(Sale).filter(Sale.user_id == farmer.id).count(),
        "production": (db.query(Production).filter(Production.crop_id.in_(crop_ids)).count()
                       if crop_ids else 0),
    }

    # Children first — expenses/sales reference crops, crops reference farms.
    if crop_ids:
        db.query(Production).filter(Production.crop_id.in_(crop_ids)).delete(synchronize_session=False)
    db.query(Expense).filter(Expense.user_id == farmer.id).delete(synchronize_session=False)
    db.query(Sale).filter(Sale.user_id == farmer.id).delete(synchronize_session=False)
    if crop_ids:
        db.query(Crop).filter(Crop.id.in_(crop_ids)).delete(synchronize_session=False)
    db.query(Farm).filter(Farm.owner_id == farmer.id).delete(synchronize_session=False)
    db.query(Notification).filter(Notification.user_id == farmer.id).delete(synchronize_session=False)
    db.query(AIConversation).filter(AIConversation.user_id == farmer.id).delete(synchronize_session=False)
    db.commit()
    return counts


def _build_demo_farm(db: Session, farmer: User) -> None:
    """Write the pristine demo farm for an existing demo account, then commit."""
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
        title="Welcome to KisanProfit (demo, read-only)",
        body=("This is a shared demo farm, so it is read-only and always looks "
              "exactly as documented. Explore the dashboard, run the profit "
              "simulator, and ask Kisan AI about the data — then create your own "
              "free account to add expenses, try voice entry and scan receipts."),
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
    log.info("Demo farm seeded (mobile %s)", DEMO_MOBILE)


def seed_at_startup() -> None:
    """Called from lifespan; creates tables then seeds the demo user."""
    from app.core.db import Base, SessionLocal, engine

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()
