"""FastAPI dependencies: JWT bearer auth resolving to a User row."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_token
from app.models.models import User

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    payload = decode_token(creds.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


def require_owned_crop(db: Session, user: User, crop_id: int):
    """Load a crop owned by the user or 404 — per-user scoping helper."""
    from app.models.models import Crop

    crop = db.get(Crop, crop_id)
    if not crop or crop.farm.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Crop not found")
    return crop
