# app/routers/conversations.py
from uuid import uuid4
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.auth.deps import get_current_user
from app.db.database import get_db
from app.db.conversation import Conversation, Message
from app.schemas import (
    ConversationOut,
    ConversationUpdate,
    MessagesResponse,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])

# --- Add this schema to app/schemas.py and import here if you prefer ---
class ConversationCreate(BaseModel):
    title: Optional[str] = None


def _get_user_conversation_or_404(db: Session, user_id: str, conversation_id: str) -> Conversation:
    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo

# ✅ CREATE conversation (this was missing)
@router.post("", response_model=ConversationOut)
def create_conversation(
    payload: ConversationCreate | None = None,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    convo = Conversation(
        id=str(uuid4()),
        user_id=current_user,
        title=(payload.title if payload and payload.title else "New chat"),
        # created_at / updated_at should be defaulted in your model; if not, set them here:
        # created_at=datetime.utcnow(),
        # updated_at=datetime.utcnow(),
    )
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return convo

@router.get("", response_model=list[ConversationOut])
def list_conversations(
    query: Optional[str] = Query(default=None, description="Search by title"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    q = db.query(Conversation).filter(Conversation.user_id == current_user)
    if query:
        # Try ilike (Postgres). If using SQLite, fallback will be handled by DB (case-sensitive)
        try:
            q = q.filter(Conversation.title.ilike(f"%{query}%"))  # type: ignore[attr-defined]
        except Exception:
            q = q.filter(Conversation.title.like(f"%{query}%"))
    convos = (
        q.order_by(desc(Conversation.updated_at), desc(Conversation.created_at))
         .offset(offset)
         .limit(limit)
         .all()
    )
    return convos

@router.get("/{conversation_id}/messages", response_model=MessagesResponse)
def get_conversation_messages(
    conversation_id: str = Path(...),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    _ = _get_user_conversation_or_404(db, current_user, conversation_id)
    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {"messages": msgs}

@router.patch("/{conversation_id}", response_model=ConversationOut)
def rename_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    convo = _get_user_conversation_or_404(db, current_user, conversation_id)
    convo.title = payload.title
    convo.updated_at = datetime.utcnow()
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return convo

@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    convo = _get_user_conversation_or_404(db, current_user, conversation_id)
    db.delete(convo)
    db.commit()
    return None