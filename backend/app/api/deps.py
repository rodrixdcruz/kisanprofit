"""FastAPI dependencies: auth (JWT → User row), the demo guard, throttling."""
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core import ratelimit
from app.core.config import get_settings
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


def require_writable_user(user: User = Depends(get_current_user)) -> User:
    """Auth dependency for every route that mutates farm data.

    The shared demo account is deliberately read-only: it is the judge-facing
    walkthrough, so a public visitor must not be able to pollute (or delete)
    the seeded farm. A nightly workflow re-seeds it as a safety net.
    """
    if user.is_demo:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "The demo account is read-only. Create your own free account to add or edit data.",
        )
    return user


def _enforce(bucket: str, key: str, limit: int) -> None:
    allowed, retry_after = ratelimit.window(bucket, limit).hit(key)
    if not allowed:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many requests — please wait a moment and try again.",
            headers={"Retry-After": str(int(retry_after) + 1)},
        )


def rate_limit(name: str, limit_setting: str):
    """Throttle a route per client IP.

    `limit_setting` names the Settings field holding the allowance, so the
    bucket can be retuned from the environment without a code change.
    """
    def dependency(request: Request) -> None:
        if not ratelimit.enabled():
            return
        _enforce(name, f"{name}:ip:{ratelimit.client_ip(request)}",
                 int(getattr(get_settings(), limit_setting)))

    return dependency


def rate_limit_user(name: str, limit_setting: str):
    """Throttle a route per signed-in account (stack after auth).

    Used alongside the per-IP bucket on the AI chat so a single account cannot
    drain a shared LLM quota, and a single IP cannot rotate accounts to.
    """
    def dependency(request: Request, user: User = Depends(get_current_user)) -> None:
        if not ratelimit.enabled():
            return
        _enforce(name, f"{name}:user:{user.id}",
                 int(getattr(get_settings(), limit_setting)))

    return dependency


def require_owned_crop(db: Session, user: User, crop_id: int):
    """Load a crop owned by the user or 404 — per-user scoping helper."""
    from app.models.models import Crop

    crop = db.get(Crop, crop_id)
    if not crop or crop.farm.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Crop not found")
    return crop
