"""Operator-only maintenance routes.

Currently one route: resetting the shared demo farm. The demo account is
read-only (see `require_writable_user`), so this exists purely as a safety net
that the nightly GitHub Actions workflow calls to guarantee the judge-facing
walkthrough looks pristine even if something drifts.

Auth is a shared secret header rather than a user token — the caller is a cron
job, not a person. With no RESEED_TOKEN configured the route 404s, so an
unconfigured deployment can never be reset by a stranger.
"""
import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.seed import reseed_demo_data

router = APIRouter(prefix="/admin", tags=["admin"])

settings = get_settings()

NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "Not found")


def require_reseed_token(x_reseed_token: str | None = Header(default=None)) -> None:
    expected = settings.RESEED_TOKEN
    if not expected:
        raise NOT_FOUND
    if not x_reseed_token or not hmac.compare_digest(x_reseed_token, expected):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid reseed token")


@router.post("/reseed-demo", dependencies=[Depends(require_reseed_token)])
def reseed_demo(db: Session = Depends(get_db)):
    return reseed_demo_data(db)
