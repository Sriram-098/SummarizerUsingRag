"""
========================================
Step A: Raw Data Sources
Step B: Information Extraction (PDF, TXT)
========================================
Loads documents from files - supports PDF and TXT formats.
This maps to steps A and B in the RAG architecture diagram.
"""
import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader


def load_documents(data_path: str):
    """
    Load all documents from the data folder.

    Architecture Mapping:
        A → Raw Data Sources (PDF, TXT files in ./data/)
        B → Information Extraction (extract text from files)

    Args:
        data_path: Path to folder containing documents

    Returns:
        List of Document objects with extracted text
    """
    documents = []

    if not os.path.exists(data_path):
        print(f"[A] Data path '{data_path}' does not exist!")
        return documents

    files = os.listdir(data_path)
    print(f"[A] Found {len(files)} files in '{data_path}'")

    for file in files:
        file_path = os.path.join(data_path, file)

        try:
            if file.lower().endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                docs = loader.load()
                documents.extend(docs)
                print(f"[B] Extracted {len(docs)} pages from PDF: {file}")

            elif file.lower().endswith(".txt"):
                loader = TextLoader(file_path, encoding="utf-8")
                docs = loader.load()
                documents.extend(docs)
                print(f"[B] Extracted {len(docs)} document(s) from TXT: {file}")

            else:
                print(f"[B] Skipping unsupported file: {file}")

        except Exception as e:
            print(f"[B] Error loading {file}: {e}")

    print(f"[B] Total extracted: {len(documents)} documents")
    return documents
