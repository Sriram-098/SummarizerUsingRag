"""
========================================
Steps 1, 2, 3: Query → Embedding → Retrieval
========================================
Handles the query side of RAG:
  1 → User Query comes in
  2 → Query is embedded (same embedding model)
  3 → Relevant data retrieved from Vector Database
"""


def get_retriever(vectordb, top_k=3):
    """
    Create a retriever from the vector database.

    Architecture Mapping:
        Steps 1-3 → Query embedding + similarity search

    Args:
        vectordb: ChromaDB vector database
        top_k: Number of relevant documents to retrieve

    Returns:
        Retriever object
    """
    retriever = vectordb.as_retriever(
        search_type="similarity",
        search_kwargs={"k": top_k}
    )
    print(f"[Retriever] Ready - will return top {top_k} relevant chunks")
    return retriever


def retrieve_relevant_docs(retriever, query: str):
    """
    Execute the retrieval pipeline.

    Architecture Mapping:
        1 → Query received
        2 → Query embedded (automatic via retriever)
        3 → Relevant data fetched from Vector Database

    Args:
        retriever: Retriever object
        query: User's question

    Returns:
        List of relevant Document objects
    """
    print(f"[1] Query: {query}")
    print(f"[2] Embedding query...")
    relevant_docs = retriever.invoke(query)
    print(f"[3] Retrieved {len(relevant_docs)} relevant chunks from Vector Database")

    for i, doc in enumerate(relevant_docs):
        preview = doc.page_content[:100].replace("\n", " ")
        print(f"    Chunk {i+1}: {preview}...")

    return relevant_docs
