from pydantic import BaseModel,Field
from typing import Optional
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
    session_id: Optional[str] = None
    mode: Optional[str] = "default"     
    format: Optional[str] = "auto"      
    tone: Optional[str] = "neutral"      

