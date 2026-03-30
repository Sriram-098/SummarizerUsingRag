"""
============================================================
RAG Application - Retrieval Augmented Generation
============================================================
Main entry point that implements the EXACT architecture:

  DATA PREPARATION (run once):
    A (Raw Data) → B (Extract) → C (Chunk) → D (Embed) → Vector DB

  QUERY TIME (run many times):
    1 (Query) → 2 (Embed Query) → 3 (Retrieve) → 4 (LLM) → 5 (Response)

HOW TO USE:
  1. Install Ollama: https://ollama.com
  2. Pull a model: ollama pull llama3.2
  3. pip install -r requirements.txt
  4. Put PDF/TXT files in ./data/ folder
  5. python app.py
============================================================
"""
import os
from src.pipeline import RAGPipeline


def print_banner():
    print("\n" + "=" * 60)
    print("""
    ╔═══════════════════════════════════════╗
    ║   RAG - Retrieval Augmented Generation ║
    ╚═══════════════════════════════════════╝

    Architecture:
    A (Data) → B (Extract) → C (Chunk) → D (Embed) → VectorDB
    Query(1) → Embed(2) → Retrieve(3) → LLM(4) → Response(5)
    """)
    print("=" * 60)


def print_help():
    print("""
    Commands:
    ─────────────────────────────────────────
    ingest   Process documents (A → B → C → D)
    query    Ask questions     (1 → 2 → 3 → 4 → 5)
    exit     Quit the application
    ─────────────────────────────────────────
    """)


def main():
    # Ensure folders exist
    os.makedirs("data", exist_ok=True)
    os.makedirs(os.path.join("storage", "shared_vectors"), exist_ok=True)

    print_banner()

    # ──────────────────────────────────────────
    # CONFIGURE YOUR MODEL HERE (OpenRouter FREE models)
    # Options:
    #   z-ai/glm-4.5-air:free       → BEST BALANCE
    #   stepfun/step-3.5-flash:free  → fast + good reasoning
    #   openai/gpt-oss-120b:free     → strong reasoning
    #   arcee-ai/trinity-mini:free   → efficient + long context
    # ──────────────────────────────────────────
    LLM_MODEL = "z-ai/glm-4.5-air:free"

    rag = RAGPipeline(
        data_path="./data",
        vectordb_path="./storage/shared_vectors",
        llm_model=LLM_MODEL
    )

    print(f"    LLM Model: {LLM_MODEL}")
    print(f"    Data Path: {os.path.abspath('./data')}")
    print(f"    VectorDB:  {os.path.abspath('./storage/shared_vectors')}")
    print_help()

    while True:
        try:
            command = input("\n> ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        # ─── INGEST: A → B → C → D ───
        if command == "ingest":
            data_files = os.listdir("./data")
            if not data_files:
                print(f"\n[!] No files found in: {os.path.abspath('./data')}")
                print("    Add PDF or TXT files to the data folder and try again.")
                continue

            print(f"\n    Found {len(data_files)} file(s): {', '.join(data_files)}")
            confirm = input("    Start ingestion? (y/n): ").strip().lower()

            if confirm == "y":
                success = rag.ingest()
                if success:
                    print("    Ready for queries! Type 'query' to start asking.")

        # ─── QUERY: 1 → 2 → 3 → 4 → 5 ───
        elif command == "query":
            # Check if vector database exists
            vectordb_files = os.listdir("./vectordb") if os.path.exists("./vectordb") else []
            if not vectordb_files:
                print("\n[!] No vector database found.")
                print("    Run 'ingest' first to process your documents.")
                continue

            # Setup RAG chain if not already done
            if rag.rag_chain is None:
                success = rag.setup_qa()
                if not success:
                    continue

            print("\n    Ask questions about your documents.")
            print("    Type 'back' to return to main menu.\n")

            while True:
                try:
                    question = input("    [?] ").strip()
                except (KeyboardInterrupt, EOFError):
                    break

                if question.lower() in ("back", "exit", "quit", "q"):
                    break

                if not question:
                    continue

                answer, sources = rag.query(question)

                print(f"\n    Answer: {answer}")
                print(f"\n    ({len(sources)} source chunks used)")
                print("    " + "-" * 40)

        # ─── EXIT ───
        elif command in ("exit", "quit", "q"):
            print("Goodbye!")
            break

        # ─── HELP ───
        elif command in ("help", "h", "?"):
            print_help()

        else:
            print("    Unknown command. Type 'help' for available commands.")


if __name__ == "__main__":
    main()
