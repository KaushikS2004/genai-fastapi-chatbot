
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel,Field

class UserCreate(BaseModel):
    username: str
    password: str = Field(..., min_length=6, max_length=72)

class Token(BaseModel):
    access_token: str
    token_type: str

class PromptRequest(BaseModel):
    prompt: str

class GenerateRequest(BaseModel):
    prompt: str
    conversation_id: str   # REQUIRED
    mode: Optional[str] = "default"
    format: Optional[str] = "auto"
    tone: Optional[str] = "neutral"

class ConversationCreate(BaseModel):
    title: Optional[str] = None

class ConversationUpdate(BaseModel):
    title: str

class ConversationOut(BaseModel):
    id: str
    title: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        orm_mode = True

class MessagesResponse(BaseModel):
    messages: List[MessageOut]


