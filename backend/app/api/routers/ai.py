"""Kisan AI chat — grounded in the farmer's own records, never invented.

Throttled twice: per account, and per IP. The demo login is public, and when
an LLM key is configured every chat call spends real quota — without this, a
single visitor with the demo credentials could drain it.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, rate_limit, rate_limit_user
from app.core.db import get_db
from app.models.models import AIConversation, User
from app.schemas.schemas import ChatRequest, ChatResponse
from app.services.ai_service import answer_question

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=ChatResponse, dependencies=[
    Depends(rate_limit("ai_chat_ip", "RATE_LIMIT_CHAT_PER_IP")),
    Depends(rate_limit_user("ai_chat_user", "RATE_LIMIT_CHAT_PER_USER")),
])
def chat(payload: ChatRequest, user: User = Depends(get_current_user),
         db: Session = Depends(get_db)):
    answer, provider = answer_question(db, user, payload.message)
    db.add(AIConversation(user_id=user.id, question=payload.message,
                          answer=answer, provider=provider))
    db.commit()
    return ChatResponse(answer=answer, provider=provider)


@router.get("/history")
def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(AIConversation)
        .filter(AIConversation.user_id == user.id)
        .order_by(AIConversation.created_at.desc())
        .limit(50)
        .all()
    )
    return [{"question": r.question, "answer": r.answer, "provider": r.provider,
             "created_at": r.created_at.isoformat()} for r in rows]
