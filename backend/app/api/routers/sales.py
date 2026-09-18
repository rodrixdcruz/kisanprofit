"""Sales — scoped through crop ownership; revenue math stays server-side."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_owned_crop
from app.core.db import get_db
from app.models.models import Sale, User
from app.schemas.schemas import SaleCreate, SaleOut

router = APIRouter(prefix="/crops/{crop_id}/sales", tags=["sales"])


@router.get("", response_model=list[SaleOut])
def list_sales(crop_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    crop = require_owned_crop(db, user, crop_id)
    return db.query(Sale).filter(Sale.crop_id == crop.id).order_by(Sale.sale_date).all()


@router.post("", response_model=SaleOut, status_code=201)
def add_sale(crop_id: int, payload: SaleCreate, user: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    crop = require_owned_crop(db, user, crop_id)
    sale = Sale(user_id=user.id, crop_id=crop.id, **payload.model_dump())
    if crop.status in ("active", "harvested"):
        crop.status = "sold"
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale
