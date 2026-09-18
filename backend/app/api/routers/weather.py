"""Weather: keyless Open-Meteo forecast + rain advisories for the farm location."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.models import User
from app.schemas.schemas import WeatherOut
from app.services.weather import get_forecast

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("", response_model=WeatherOut)
def weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return WeatherOut(**get_forecast(db, latitude, longitude))
