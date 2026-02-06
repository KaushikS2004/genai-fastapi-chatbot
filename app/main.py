# main.py
from datetime import datetime
import os
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query, Path, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session
from sqlalchemy import desc

from uuid import uuid4

# --- App & DB ---
from app.db.database import Base, engine, get_db

# --- Auth ---
from app.auth.auth import router as auth_router
from app.auth.deps import get_current_user

# --- LLM / RAG / Memory ---
from app.llm.llm_service import stream_answer
from app.memory import get_history, save_message
from app.message_builder import build_messages
from app.schemas import GenerateRequest,ConversationCreate,ConversationOut,ConversationUpdate,MessageOut,MessagesResponse
from app.prompt_builder import build_system_prompt

from app.file_parser import extract_text
from app.chunker import chunk_text
from app.embeddings import embed_texts, embed_query
from app.rag_store import get_store

# --- Models ---
from app.db.conversation import Conversation, Message
from app.routers.conversations import router as conversations_router

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


# Routers
app.include_router(auth_router)
app.include_router(conversations_router)

# -------------------- Health --------------------
@app.get("/")
def health():
    return {"status": "Application is running"}

# -------------------- Generate (Streaming) --------------------
@app.post("/generate/stream")
def generate_stream(
    payload: GenerateRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    conversation_id = payload.conversation_id

    # Validate conversation ownership
    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user)
        .first()
    )
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 1) Load persistent chat history
    history_records = get_history(db, conversation_id)
    history = [{"role": m.role, "content": m.content} for m in history_records]

    # 2) Build system prompt
    system_prompt = build_system_prompt(
        mode=payload.mode,
        format=payload.format,
        tone=payload.tone
    )

    # 3) RAG retrieval
    retrieved_chunks = []
    store = get_store(current_user, conversation_id)
    try:
        if getattr(store, "index", None) and getattr(store.index, "ntotal", 0) > 0:
            query_embedding = embed_query(payload.prompt)
            retrieved_chunks = store.search(query_embedding, k=4)
    except Exception as e:
        print("RAG error:", e)

    if retrieved_chunks:
        system_prompt += "\n\nUse the following context:\n"
        for i, chunk in enumerate(retrieved_chunks, 1):
            system_prompt += f"\n[Context {i}]\n{chunk}\n"

    # 4) Build messages for LLM
    messages = build_messages(
        system_prompt=system_prompt,
        history=history,
        user_prompt=payload.prompt
    )

    # 5) Stream response
    def event_stream():
        full_answer = ""
        try:
            for token in stream_answer(messages):
                full_answer += token
                yield token
        finally:
            # 6) Save BOTH messages AFTER streaming completes
            try:
                save_message(db, conversation_id, "user", payload.prompt)
                save_message(db, conversation_id, "assistant", full_answer)
                # bump conversation timestamp
                convo.updated_at = datetime.utcnow()
                db.add(convo)
                db.commit()
            except Exception as e:
                print("⚠️ Failed to persist messages:", e)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# -------------------- Upload (RAG ingest) --------------------
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    conversation_id: str = "",
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    # Validate conversation ownership
    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user)
        .first()
    )
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    try:
        content = await file.read()
        text = extract_text(file.filename, content)

        if not text.strip():
            raise HTTPException(status_code=400, detail="Empty document")

        chunks = chunk_text(text)
        embeddings = embed_texts(chunks)

        # Attach to conversation store
        store = get_store(current_user, conversation_id)
        store.add(embeddings, chunks)

        # update conversation timestamp
        convo.updated_at = datetime.utcnow()
        db.add(convo)
        db.commit()

        return {
            "filename": file.filename,
            "message": "File uploaded and processed successfully",
            "chunks_stored": len(chunks)
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print("Upload error:", e)
        raise HTTPException(status_code=500, detail="Failed to process file")


# -------------------- Static --------------------
if os.path.isdir("app/static"):
    app.mount(
        "/static",
        StaticFiles(directory="app/static", html=True),
        name="static"
    )