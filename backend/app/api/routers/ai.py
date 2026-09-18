"""Kisan AI chat — grounded in the farmer's own records, never invented."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.models import AIConversation, User
from app.schemas.schemas import ChatRequest, ChatResponse
from app.services.ai_service import answer_question

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=ChatResponse)
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
