"""Auth: register, login (mobile + password), demo entry, session, language.

The three unauthenticated entry points are rate limited per client IP: this is
reachable from a public demo link, so password guessing and scripted sign-ups
should cost the attacker something.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, rate_limit
from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.models import User
from app.schemas.schemas import LanguageUpdate, Token, UserCreate, UserOut
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

settings = get_settings()


class LoginRequest(BaseModel):
    mobile: str
    password: str


@router.post("/register", response_model=Token, status_code=201,
             dependencies=[Depends(rate_limit("register", "RATE_LIMIT_REGISTER"))])
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.mobile == payload.mobile).first():
        raise HTTPException(409, "An account with this mobile number already exists")
    user = User(
        name=payload.name,
        mobile=payload.mobile,
        password_hash=hash_password(payload.password),
        language=payload.language if payload.language in ("en", "hi", "mr") else "en",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return Token(access_token=create_access_token(str(user.id)), user=UserOut.model_validate(user))


@router.post("/login", response_model=Token,
             dependencies=[Depends(rate_limit("login", "RATE_LIMIT_LOGIN"))])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.mobile == payload.mobile).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid mobile number or password")
    return Token(access_token=create_access_token(str(user.id)), user=UserOut.model_validate(user))


@router.post("/demo-login", response_model=Token,
             dependencies=[Depends(rate_limit("demo_login", "RATE_LIMIT_DEMO_LOGIN"))])
def demo_login(db: Session = Depends(get_db)):
    """One-tap entry to the read-only demo farm, with no credentials.

    The demo account is public by design (the README documents its login) and
    read-only, so this is not a weaker door than the password — it just keeps
    the credentials out of the frontend bundle and lets an operator rotate the
    password without breaking the "Explore Demo Farm" button. Set
    DEMO_LOGIN_ENABLED=false to close it; the route then 404s.
    """
    if settings.DEMO_LOGIN_ENABLED.lower() not in ("1", "true", "yes"):
        raise HTTPException(404, "Not found")
    user = db.query(User).filter(User.mobile == settings.DEMO_MOBILE).first()
    if user is None or not user.is_demo:
        raise HTTPException(503, "The demo farm is not available right now")
    return Token(access_token=create_access_token(str(user.id)), user=UserOut.model_validate(user))


@router.get("/session", response_model=UserOut)
def session_info(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


@router.put("/language", response_model=UserOut)
def set_language(payload: LanguageUpdate, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    user.language = payload.language
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)
