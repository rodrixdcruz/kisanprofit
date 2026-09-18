"""Production (harvest) records — scoped through crop ownership."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_owned_crop
from app.core.db import get_db
from app.models.models import Crop, Production, User
from app.schemas.schemas import ProductionCreate, ProductionOut

router = APIRouter(prefix="/crops/{crop_id}/production", tags=["production"])


@router.get("", response_model=list[ProductionOut])
def list_production(crop_id: int, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    crop = require_owned_crop(db, user, crop_id)
    return db.query(Production).filter(Production.crop_id == crop.id).order_by(Production.harvest_date).all()


@router.post("", response_model=ProductionOut, status_code=201)
def add_production(crop_id: int, payload: ProductionCreate, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    crop: Crop = require_owned_crop(db, user, crop_id)
    rec = Production(crop_id=crop.id, **payload.model_dump())
    if crop.status == "active":
        crop.status = "harvested"
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec
