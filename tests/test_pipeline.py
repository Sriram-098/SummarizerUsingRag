"""
RAG Pipeline — Unit Tests
"""
import os
import pytest


def test_loader_loads_txt():
    """Verify TXT loader extracts text from sample document."""
    from src.loader import load_documents

    docs = load_documents("./data")
    assert len(docs) > 0, "Should load at least one document from data/"
    assert docs[0].page_content, "Document should have text content"


def test_chunker_splits():
    """Verify chunker produces more chunks than input documents."""
    from src.loader import load_documents
    from src.chunker import chunk_documents

    docs = load_documents("./data")
    chunks = chunk_documents(docs, chunk_size=500, chunk_overlap=50)
    assert len(chunks) >= len(docs), "Chunks should be >= number of documents"
    for chunk in chunks:
        assert len(chunk.page_content) <= 600, "Chunk should respect size limit (with tolerance)"


def test_embedding_model_loads():
    """Verify HuggingFace embedding model initializes."""
    from src.embedder import get_embedding_model

    model = get_embedding_model()
    assert model is not None, "Embedding model should load"


def test_pipeline_init():
    """Verify RAGPipeline initializes with correct defaults."""
    from src.pipeline import RAGPipeline

    rag = RAGPipeline()
    assert rag.data_path == "./data"
    assert rag.vectordb_path == "./storage/shared_vectors"
    assert rag.llm_model == "z-ai/glm-4.5-air:free"


def test_env_has_api_key():
    """Verify OPENROUTER_API_KEY is set in environment."""
    from dotenv import load_dotenv

    load_dotenv()
    key = os.environ.get("OPENROUTER_API_KEY", "")
    assert key.startswith("sk-or-"), "OPENROUTER_API_KEY should be set in .env"
