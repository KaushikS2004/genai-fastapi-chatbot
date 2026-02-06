from typing import Dict, List, Tuple

# Key = (user_id, session_id)
# Value = list of messages
from sqlalchemy.orm import Session
from app.db.conversation import Message


def get_history(db: Session, conversation_id: str):
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .all()
    )


def save_message(db: Session, conversation_id: str, role: str, content: str):
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )
    db.add(msg)
    db.commit()


def clear_history(db: Session, conversation_id: str):
    db.query(Message)\
      .filter(Message.conversation_id == conversation_id)\
      .delete()
    db.commit()
