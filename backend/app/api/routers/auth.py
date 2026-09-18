"""Auth: register, login (mobile + password), session, language preference."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.models import User
from app.schemas.schemas import LanguageUpdate, Token, UserCreate, UserOut
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    mobile: str
    password: str


@router.post("/register", response_model=Token, status_code=201)
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


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.mobile == payload.mobile).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid mobile number or password")
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
