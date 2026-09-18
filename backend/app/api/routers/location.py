"""Location: geocoding for the map picker."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.models import User
from app.services.location import geocode

router = APIRouter(prefix="/location", tags=["location"])


class _GeocodeBody(BaseModel):
    query: str


@router.post("/geocode")
def geocode_endpoint(body: _GeocodeBody, user: User = Depends(get_current_user)):
    return {"results": geocode(body.query)}
