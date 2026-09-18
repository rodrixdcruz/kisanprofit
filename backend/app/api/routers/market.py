"""Market prices: live mandi quotes when keyed; labeled reference prices otherwise."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.models import User
from app.services.market import get_prices

router = APIRouter(prefix="/market", tags=["market"])


@router.get("")
def prices(commodity: str | None = Query(default=None, max_length=80),
           user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_prices(db, commodity)
