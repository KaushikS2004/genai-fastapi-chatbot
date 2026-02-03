from pydantic import BaseModel,Field

class UserCreate(BaseModel):
    username: str
    password: str = Field(..., min_length=6, max_length=72)

class Token(BaseModel):
    access_token: str
    token_type: str

class PromptRequest(BaseModel):
    prompt: str
