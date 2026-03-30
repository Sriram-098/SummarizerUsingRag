"""
RAG Routes — Ingest documents & query the RAG pipeline (per-user).
"""
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db
from backend.models import User, Document
from backend.auth import get_current_user
from backend.routes.documents import get_user_data_path

# ── RAG imports (reusing existing src/) ──
from src.loader import load_documents
from src.chunker import chunk_documents
from src.embedder import get_embedding_model, store_in_vectordb, load_vectordb
from src.retriever import get_retriever
from src.generator import get_llm, create_rag_chain, generate_response

router = APIRouter(prefix="/api/rag", tags=["rag"])

# ── In-memory cache for per-user pipelines ──
_user_pipelines: dict = {}


def get_user_vectordb_path(user_id: str) -> str:
    """Each user gets their own vector DB."""
    path = os.path.join("storage", "vectors", user_id)
    os.makedirs(path, exist_ok=True)
    return path


class IngestRequest(BaseModel):
    chunk_size: int = 1000
    chunk_overlap: int = 100
    model: str = "z-ai/glm-4.5-air:free"


class QueryRequest(BaseModel):
    question: str
    top_k: int = 3
    model: str = "z-ai/glm-4.5-air:free"


class IngestResponse(BaseModel):
    message: str
    documents_loaded: int
    chunks_created: int
    vectors_stored: int


class QueryResponse(BaseModel):
    answer: str
    sources: list
    time_seconds: float


@router.post("/ingest", response_model=IngestResponse)
def ingest_documents(
    body: IngestRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Ingest all of the user's uploaded documents into their private vector DB.
    A → B → C → D pipeline.
    """
    user_data_path = get_user_data_path(user.id)
    vectordb_path = get_user_vectordb_path(user.id)

    # Check for documents
    if not os.path.exists(user_data_path) or not os.listdir(user_data_path):
        raise HTTPException(400, "No documents uploaded. Upload files first.")

    # Step A+B: Load documents
    documents = load_documents(user_data_path)
    if not documents:
        raise HTTPException(400, "Could not extract text from any document.")

    # Step C: Chunk
    chunks = chunk_documents(documents, body.chunk_size, body.chunk_overlap)

    # Step D: Embed + store
    embeddings = get_embedding_model()
    vectordb = store_in_vectordb(chunks, embeddings, vectordb_path)

    # Update chunk counts in DB
    user_docs = db.query(Document).filter(Document.user_id == user.id).all()
    chunks_per_doc = len(chunks) // max(len(user_docs), 1)
    for doc in user_docs:
        doc.chunk_count = chunks_per_doc
    db.commit()

    # Clear cached pipeline so it reloads
    _user_pipelines.pop(user.id, None)

    vector_count = vectordb._collection.count()
    return {
        "message": "Ingestion complete",
        "documents_loaded": len(documents),
        "chunks_created": len(chunks),
        "vectors_stored": vector_count,
    }


@router.post("/query", response_model=QueryResponse)
def query_rag(
    body: QueryRequest,
    user: User = Depends(get_current_user),
):
    """
    Query the user's private RAG pipeline.
    1 → 2 → 3 → 4 → 5 pipeline.
    """
    import time

    vectordb_path = get_user_vectordb_path(user.id)
    if not os.path.exists(vectordb_path):
        raise HTTPException(400, "No ingested data. Please ingest documents first.")

    start = time.time()

    cache_key = user.id
    pipeline = _user_pipelines.get(cache_key)

    if pipeline is None or pipeline.get("model") != body.model:
        # Build pipeline for this user
        embeddings = get_embedding_model()
        vectordb = load_vectordb(embeddings, vectordb_path)
        retriever = get_retriever(vectordb, top_k=body.top_k)
        llm = get_llm(body.model)
        rag_chain = create_rag_chain(llm, retriever)

        pipeline = {
            "model": body.model,
            "retriever": retriever,
            "rag_chain": rag_chain,
            "vectordb": vectordb,
        }
        _user_pipelines[cache_key] = pipeline
    else:
        # Update top_k if different
        retriever = get_retriever(pipeline["vectordb"], top_k=body.top_k)
        llm = get_llm(body.model)
        pipeline["rag_chain"] = create_rag_chain(llm, retriever)
        pipeline["retriever"] = retriever

    answer, sources = generate_response(
        pipeline["rag_chain"], body.question, pipeline["retriever"]
    )
    elapsed = time.time() - start

    source_data = []
    for src in sources:
        meta = src.metadata if hasattr(src, "metadata") else {}
        source_data.append({
            "filename": os.path.basename(meta.get("source", "Unknown")),
            "preview": (src.page_content[:250].replace("\n", " ") + "...") if hasattr(src, "page_content") else "",
        })

    return {
        "answer": answer,
        "sources": source_data,
        "time_seconds": round(elapsed, 2),
    }


@router.get("/stats")
def get_stats(user: User = Depends(get_current_user)):
    """Get vector DB stats for the current user."""
    vectordb_path = get_user_vectordb_path(user.id)
    if not os.path.exists(vectordb_path):
        return {"vectors": 0, "exists": False}

    try:
        embeddings = get_embedding_model()
        vectordb = load_vectordb(embeddings, vectordb_path)
        count = vectordb._collection.count()
        return {"vectors": count, "exists": True}
    except Exception:
        return {"vectors": 0, "exists": True}
