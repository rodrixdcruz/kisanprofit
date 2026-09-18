"""Analytics: dashboard, per-crop P&L, comparison, simulator, insights."""
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_owned_crop
from app.core.db import get_db
from app.models.models import Crop, Expense, Farm, Sale, User
from app.schemas.schemas import (CropComparisonRow, CropProfitOut, DashboardOut,
                                 Insight, SimulatorOut, SimulatorRequest)
from app.services.finance import comparison, compute_crop_financials, portfolio, simulate
from app.services.insights import build_insights
from app.services.notifications import notify_harvest_due

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _user_financials(db: Session, user: User) -> list:
    crops = (
        db.query(Crop)
        .join(Farm, Crop.farm_id == Farm.id)
        .filter(Farm.owner_id == user.id)
        .all()
    )
    return [
        compute_crop_financials(c, c.expenses, c.productions, c.sales)
        for c in crops
    ]


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    farms = user.farms
    crops = [c for f in farms for c in f.crops]
    expenses = db.query(Expense).filter(Expense.user_id == user.id).all()
    sales = db.query(Sale).filter(Sale.user_id == user.id).all()
    productions = [p for c in crops for p in c.productions]
    totals = portfolio(user, farms, crops, expenses, productions, sales, date.today())
    notify_harvest_due(db, user)  # opportunistic reminder generation
    return DashboardOut(**totals)


@router.get("/crops", response_model=list[CropProfitOut])
def crop_profitability(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    fins = _user_financials(db, user)
    out = []
    for f in fins:
        out.append(CropProfitOut(
            crop_id=f.crop_id, crop_name=f.crop_name, area_acres=f.area_acres,
            total_cost=round(f.total_cost, 2), revenue=round(f.revenue, 2),
            profit=round(f.profit, 2), roi_percent=round(f.roi_percent, 2),
            cost_per_acre=round(f.cost_per_acre, 2),
            profit_per_acre=round(f.profit_per_acre, 2),
            break_even_price_per_quintal=round(f.break_even_price_per_quintal, 2)
            if f.break_even_price_per_quintal else None,
            produced_quintal=f.produced_quintal, sold_quintal=f.sold_quintal,
            expected_yield_quintal=f.expected_yield_quintal,
            production_variance_percent=round(f.production_variance_percent, 1)
            if f.production_variance_percent is not None else None,
        ))
    return out


@router.get("/comparison", response_model=list[CropComparisonRow])
def crop_comparison(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [CropComparisonRow(**row) for row in comparison(_user_financials(db, user))]


@router.post("/simulator/{crop_id}", response_model=SimulatorOut)
def profit_simulator(crop_id: int, payload: SimulatorRequest,
                     user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    crop = require_owned_crop(db, user, crop_id)
    fin = compute_crop_financials(crop, crop.expenses, crop.productions, crop.sales)
    return SimulatorOut(**simulate(crop, fin, payload.price_per_quintal,
                                   payload.production_quintal, payload.cost_multiplier))


@router.get("/insights", response_model=list[Insight])
def ai_insights(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [Insight(**i) for i in build_insights(_user_financials(db, user))]
