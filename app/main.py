from pyexpat.errors import messages
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from uuid import uuid4
from app.auth.auth import router as auth_router
from app.auth.deps import get_current_user
from app.llm.llm_service import generate_answer
from app.db.database import Base, engine
from app.models.models import PromptRequest
from uuid import uuid4
from fastapi import Depends, HTTPException
from app.memory import get_history, save_message
from app.message_builder import build_messages
from app.schemas import GenerateRequest 
from app.prompt_builder import build_system_prompt
from fastapi.responses import StreamingResponse
from app.llm.llm_service import stream_answer
from fastapi import UploadFile, File
from app.file_parser import extract_text
from app.chunker import chunk_text
from app.embeddings import embed_texts
from app.rag_store import get_store
from app.embeddings import embed_query


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
    # 1️⃣ Create or reuse session
    session_id = payload.session_id or str(uuid4())

    # 2️⃣ Load previous conversation
    history = get_history(current_user, session_id)

    # 3️⃣ System prompt (simple for now)
    system_prompt = build_system_prompt(
        mode=payload.mode,
        format=payload.format,
        tone=payload.tone
    )

    # 4️⃣ Build full message list
    messages = build_messages(
        system_prompt=system_prompt,
        history=history,
        user_prompt=payload.prompt
    )

    try:
        answer = generate_answer(messages)
    except Exception:
        raise HTTPException(status_code=500, detail="LLM failed")

    # 5️⃣ Save messages
    save_message(current_user, session_id, "user", payload.prompt)
    save_message(current_user, session_id, "assistant", answer)

    return {
        "session_id": session_id,
        "answer": answer
    }
@app.post("/generate/stream")
def generate_stream(
    payload: GenerateRequest,
    current_user: str = Depends(get_current_user)
):
    session_id = payload.session_id or str(uuid4())
    history = get_history(current_user, session_id)

    system_prompt = build_system_prompt(
        mode=payload.mode,
        format=payload.format,
        tone=payload.tone
    )

    # 🔍 RAG retrieval
    store = get_store(current_user, session_id)
    print("VectorStore size:", len(store.texts))
    print("User question:", payload.prompt)


    retrieved_chunks = []

    if store.index.ntotal > 0:
        try:
            query_embedding = embed_query(payload.prompt)
            retrieved_chunks = store.search(query_embedding, k=4)
            print(f"Retrieved chunks: {len(retrieved_chunks)}")
        except Exception as e:
            print("RAG retrieval error:", e)
    print("Retrieved chunks:", retrieved_chunks)

    if retrieved_chunks:
        system_prompt += "\n\nUse the following context to answer:\n"
        for i, chunk in enumerate(retrieved_chunks, 1):
            system_prompt += f"\n[Context {i}]\n{chunk}\n"

    messages = build_messages(
        system_prompt=system_prompt,
        history=history,
        user_prompt=payload.prompt
    )

    def event_stream():
        full_answer = ""
        for token in stream_answer(messages):
            full_answer += token
            yield f"{token}"


        save_message(current_user, session_id, "user", payload.prompt)
        save_message(current_user, session_id, "assistant", full_answer)

    return StreamingResponse(
    event_stream(),
    media_type="text/event-stream"
)


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = "",
    current_user: str = Depends(get_current_user)
):
    try:
        content = await file.read()
        text = extract_text(file.filename, content)

        if not text.strip():
            raise HTTPException(status_code=400, detail="Empty document")

        chunks = chunk_text(text)
        embeddings = embed_texts(chunks)
        store = get_store(current_user, session_id)
        store.add(embeddings, chunks)
        return {
            "filename": file.filename,
            "message": "File uploaded and processed successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    print("Chunks stored:", len(chunks))



if os.path.isdir("app/static"):
    app.mount(
        "/static",
        StaticFiles(directory="app/static", html=True),
        name="static"
    )
