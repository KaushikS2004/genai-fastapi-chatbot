from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from app.auth.auth import router as auth_router
from app.auth.deps import get_current_user
from app.llm.llm_service import generate_answer
from app.db.database import Base, engine
from app.models.models import PromptRequest

Base.metadata.create_all(bind=engine)

class GenerateRequest(BaseModel):
    prompt: str

app = FastAPI(
    title="Authenticated GenAI App",
    description="FastAPI + JWT + LLM",
    version="1.0.0"
)

app.include_router(auth_router)

@app.get("/")
def health():
    return {"status": "Application is running"}

@app.post("/generate")
def generate(
    payload: GenerateRequest,
    current_user: str = Depends(get_current_user)
):
    prompt = payload.prompt
    if not prompt:
        return {"error": "Prompt is required"}

    answer = generate_answer(prompt)
    return {
        "user": current_user,
        "answer": answer
    }

app.mount(
    "/static",
    StaticFiles(directory="app/static", html=True),
    name="static"
)
