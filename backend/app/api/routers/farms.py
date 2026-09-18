"""Farms CRUD — everything scoped to the authenticated owner."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.models import Farm, User
from app.schemas.schemas import FarmCreate, FarmOut

router = APIRouter(prefix="/farms", tags=["farms"])


@router.get("", response_model=list[FarmOut])
def list_farms(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Farm).filter(Farm.owner_id == user.id).order_by(Farm.name).all()


@router.post("", response_model=FarmOut, status_code=201)
def create_farm(payload: FarmCreate, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    farm = Farm(owner_id=user.id, **payload.model_dump())
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.get("/{farm_id}", response_model=FarmOut)
def get_farm(farm_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.owner_id == user.id).first()
    if not farm:
        raise HTTPException(404, "Farm not found")
    return farm


@router.put("/{farm_id}", response_model=FarmOut)
def update_farm(farm_id: int, payload: FarmCreate, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.owner_id == user.id).first()
    if not farm:
        raise HTTPException(404, "Farm not found")
    for k, v in payload.model_dump().items():
        setattr(farm, k, v)
    db.commit()
    db.refresh(farm)
    return farm


@router.delete("/{farm_id}", status_code=204)
def delete_farm(farm_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.owner_id == user.id).first()
    if not farm:
        raise HTTPException(404, "Farm not found")
    db.delete(farm)
    db.commit()
