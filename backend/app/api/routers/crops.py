"""Crops CRUD — scoped through farm ownership."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_writable_user
from app.core.db import get_db
from app.models.models import Crop, Farm, User
from app.schemas.schemas import CropCreate, CropOut

router = APIRouter(prefix="/farms/{farm_id}/crops", tags=["crops"])


def _own_farm(db: Session, user: User, farm_id: int) -> Farm:
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.owner_id == user.id).first()
    if not farm:
        raise HTTPException(404, "Farm not found")
    return farm


@router.get("", response_model=list[CropOut])
def list_crops(farm_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _own_farm(db, user, farm_id)
    return db.query(Crop).filter(Crop.farm_id == farm_id).order_by(Crop.id.desc()).all()


@router.post("", response_model=CropOut, status_code=201)
def create_crop(farm_id: int, payload: CropCreate, user: User = Depends(require_writable_user),
                db: Session = Depends(get_db)):
    _own_farm(db, user, farm_id)
    crop = Crop(farm_id=farm_id, **payload.model_dump())
    db.add(crop)
    db.commit()
    db.refresh(crop)
    return crop


@router.get("/{crop_id}", response_model=CropOut)
def get_crop(farm_id: int, crop_id: int, user: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    _own_farm(db, user, farm_id)
    crop = db.query(Crop).filter(Crop.id == crop_id, Crop.farm_id == farm_id).first()
    if not crop:
        raise HTTPException(404, "Crop not found")
    return crop


@router.put("/{crop_id}", response_model=CropOut)
def update_crop(farm_id: int, crop_id: int, payload: CropCreate,
                user: User = Depends(require_writable_user), db: Session = Depends(get_db)):
    _own_farm(db, user, farm_id)
    crop = db.query(Crop).filter(Crop.id == crop_id, Crop.farm_id == farm_id).first()
    if not crop:
        raise HTTPException(404, "Crop not found")
    data = payload.model_dump()
    for k, v in data.items():
        if k != "farm_id":
            setattr(crop, k, v)
    db.commit()
    db.refresh(crop)
    return crop


@router.patch("/{crop_id}/status", response_model=CropOut)
def set_status(farm_id: int, crop_id: int, status: str,
               user: User = Depends(require_writable_user), db: Session = Depends(get_db)):
    if status not in ("active", "harvested", "sold"):
        raise HTTPException(422, "status must be active | harvested | sold")
    _own_farm(db, user, farm_id)
    crop = db.query(Crop).filter(Crop.id == crop_id, Crop.farm_id == farm_id).first()
    if not crop:
        raise HTTPException(404, "Crop not found")
    crop.status = status
    db.commit()
    db.refresh(crop)
    return crop


@router.delete("/{crop_id}", status_code=204)
def delete_crop(farm_id: int, crop_id: int, user: User = Depends(require_writable_user),
                db: Session = Depends(get_db)):
    _own_farm(db, user, farm_id)
    crop = db.query(Crop).filter(Crop.id == crop_id, Crop.farm_id == farm_id).first()
    if not crop:
        raise HTTPException(404, "Crop not found")
    db.delete(crop)
    db.commit()
