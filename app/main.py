from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

from app.auth.auth import router as auth_router
from app.auth.deps import get_current_user
from app.llm.llm_service import generate_answer
from app.db.database import Base, engine
from app.models.models import PromptRequest

class GenerateRequest(BaseModel):
    prompt: str

app = FastAPI(
    title="Authenticated GenAI App",
    description="FastAPI + JWT + LLM",
    version="1.0.0"
)

@app.on_event("startup")
async def startup():
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ DB ready")
    except Exception as e:
        print("⚠️ DB issue:", e)

app.include_router(auth_router)

@app.get("/")
def health():
    return {"status": "Application is running"}

@app.post("/generate")
def generate(
    payload: GenerateRequest,
    current_user: str = Depends(get_current_user)
):
    return {
        "user": current_user,
        "answer": generate_answer(payload.prompt)
    }

if os.path.isdir("app/static"):
    app.mount(
        "/static",
        StaticFiles(directory="app/static", html=True),
        name="static"
    )
