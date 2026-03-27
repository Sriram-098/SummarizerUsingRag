# RAG System — Retrieval Augmented Generation

A complete, production-ready RAG (Retrieval Augmented Generation) pipeline built with Python. It processes your documents, stores them in a vector database, and lets you ask questions answered by a Large Language Model grounded in your own data.

**100% free** — uses open-source embeddings (HuggingFace) + free LLM via OpenRouter.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA PREPARATION (run once)                  │
│                                                                 │
│  ┌───────────┐   ┌──────────────┐   ┌──────────┐   ┌────────┐  │
│  │ A. Raw     │──▶│ B. Extract   │──▶│ C. Chunk │──▶│D. Embed│  │
│  │    Data    │   │    Text      │   │          │   │        │  │
│  │ (PDF/TXT)  │   │ (PyPDF)      │   │ (500     │   │(HF     │  │
│  │            │   │              │   │  chars)  │   │ model) │  │
│  └───────────┘   └──────────────┘   └──────────┘   └───┬────┘  │
│                                                         │       │
│                                                         ▼       │
│                                                 ┌──────────────┐│
│                                                 │ Vector DB    ││
│                                                 │ (ChromaDB)   ││
│                                                 └──────┬───────┘│
└────────────────────────────────────────────────────────┼────────┘
                                                         │
┌────────────────────────────────────────────────────────┼────────┐
│                 QUERY TIME (run many times)             │        │
│                                                         │        │
│  ┌───────────┐   ┌──────────────┐   ┌──────────────┐   │        │
│  │ 1. User   │──▶│ 2. Embed     │──▶│ 3. Retrieve  │◀──┘        │
│  │    Query   │   │    Query     │   │    Top-K     │            │
│  └───────────┘   └──────────────┘   └──────┬───────┘            │
│                                             │                    │
│                                             ▼                    │
│                                     ┌──────────────┐             │
│                                     │ 4. LLM       │             │
│                                     │ (GLM-4.5-Air)│             │
│                                     └──────┬───────┘             │
│                                             │                    │
│                                             ▼                    │
│                                     ┌──────────────┐             │
│                                     │ 5. Response  │             │
│                                     └──────────────┘             │
└──────────────────────────────────────────────────────────────────┘
```

---

## How It Works

### Data Preparation (Steps A → D)

| Step | What Happens | Code | Tool Used |
|------|-------------|------|-----------|
| **A. Raw Data** | Load PDF/TXT files from `./data/` folder | `src/loader.py` | PyPDF, TextLoader |
| **B. Extract** | Extract text content from each file | `src/loader.py` | LangChain Loaders |
| **C. Chunk** | Split text into 500-char pieces with 50-char overlap | `src/chunker.py` | RecursiveCharacterTextSplitter |
| **D. Embed + Store** | Convert chunks to vectors, store in ChromaDB | `src/embedder.py` | HuggingFace `all-MiniLM-L6-v2`, ChromaDB |

### Query Time (Steps 1 → 5)

| Step | What Happens | Code | Tool Used |
|------|-------------|------|-----------|
| **1. Query** | User asks a question | `src/retriever.py` | — |
| **2. Embed Query** | Question is converted to a vector | `src/retriever.py` | Same HuggingFace model |
| **3. Retrieve** | Find top-3 most similar chunks from VectorDB | `src/retriever.py` | ChromaDB similarity search |
| **4. LLM** | Send retrieved context + question to LLM | `src/generator.py` | OpenRouter (GLM-4.5-Air) |
| **5. Response** | LLM generates an answer grounded in your documents | `src/generator.py` | — |

---

## Project Structure

```
ldsrag/
├── app.py                 # Main entry point (CLI interface)
├── requirements.txt       # Python dependencies
├── .env                   # API key (OpenRouter) — DO NOT COMMIT
├── .gitignore             # Ignores .env, venv, vectordb, __pycache__
├── data/                  # Put your PDF/TXT files here
│   └── sample_document.txt
├── vectordb/              # ChromaDB storage (auto-created after ingest)
│   ├── chroma.sqlite3
│   └── <uuid>/
└── src/
    ├── __init__.py
    ├── loader.py          # Steps A + B: Load & extract documents
    ├── chunker.py         # Step C: Split into chunks
    ├── embedder.py        # Step D: Embed + store in Vector DB
    ├── retriever.py       # Steps 1, 2, 3: Query → Embed → Retrieve
    ├── generator.py       # Steps 4, 5: LLM → Response
    └── pipeline.py        # Full pipeline connecting everything
```

---

## Source Code Breakdown (`src/`)

Below is a detailed explanation of every file inside `src/` — what it does, how it works, and where it fits in the RAG architecture.

---

### `src/loader.py` — Document Loading (Steps A + B)

**Purpose:** Reads raw files from the `data/` folder and extracts their text content.

**How it works:**
1. Scans the `data/` directory for all files
2. For each `.pdf` file → uses `PyPDFLoader` to extract text page by page
3. For each `.txt` file → uses `TextLoader` to read the full text content
4. Unsupported file types (e.g., `.docx`, `.csv`) are skipped with a warning
5. Returns a list of `Document` objects, where each object holds the extracted text and metadata (filename, page number)

**Key function:**
```python
load_documents(data_path="./data/")
# Input:  path to folder containing PDF/TXT files
# Output: list of Document objects with .page_content and .metadata
```

**Example output:**
```
[A] Found 3 files in './data'
[B] Extracted 12 pages from PDF: ai_complete_reference.pdf
[B] Extracted 1 document(s) from TXT: sample_document.txt
[B] Total extracted: 14 documents
```

---

### `src/chunker.py` — Text Splitting (Step C)

**Purpose:** Splits large documents into smaller, overlapping chunks so they can be embedded and searched efficiently.

**Why chunking is needed:**
- Embedding models have input size limits
- Smaller chunks allow more precise retrieval (finding the exact paragraph that answers a question)
- Overlap between chunks ensures no information is lost at boundaries

**How it works:**
1. Uses `RecursiveCharacterTextSplitter` from LangChain
2. Splits text using a hierarchy of separators: paragraph breaks (`\n\n`) → line breaks (`\n`) → sentences (`. `) → words (` `) → characters (`""`)
3. Each chunk is at most `chunk_size` characters (default: 1000)
4. Adjacent chunks share `chunk_overlap` characters (default: 100) to preserve context

**Key function:**
```python
chunk_documents(documents, chunk_size=1000, chunk_overlap=100)
# Input:  list of Document objects from loader.py
# Output: list of smaller Document objects (chunks)
```

**Example:** A 30,000-character document → ~33 chunks of ~1000 characters each

---

### `src/embedder.py` — Embedding + Vector Storage (Step D)

**Purpose:** Converts text chunks into numerical vectors (embeddings) and stores them in ChromaDB for fast similarity search.

**How it works:**
1. Loads the HuggingFace embedding model `sentence-transformers/all-MiniLM-L6-v2` (runs locally, free, no API key)
2. Each text chunk is converted into a 384-dimensional vector that captures its semantic meaning
3. All vectors are stored in ChromaDB, a local vector database persisted at `./vectordb/`
4. Also supports loading an existing vector database from disk (used when querying without re-ingesting)

**Key functions:**
```python
get_embedding_model()
# Returns: HuggingFaceEmbeddings model (runs on CPU, free)

store_in_vectordb(chunks, embeddings, persist_directory="./vectordb")
# Input:  chunks from chunker.py + embedding model
# Output: ChromaDB vector database instance (saved to disk)

load_vectordb(embeddings, persist_directory="./vectordb")
# Loads an existing vector database from disk (no re-embedding needed)
```

**How embeddings work:**
- The sentence `"RAG reduces hallucination"` becomes a vector like `[0.23, -0.41, 0.87, ...]` (384 numbers)
- Semantically similar sentences produce similar vectors (close in vector space)
- This enables finding relevant chunks by vector similarity rather than keyword matching

---

### `src/retriever.py` — Query & Retrieval (Steps 1, 2, 3)

**Purpose:** Takes a user's question, embeds it into a vector, and retrieves the most relevant chunks from the vector database.

**How it works:**
1. **Step 1** — Receives the user's natural language question
2. **Step 2** — Embeds the question using the same HuggingFace model used during ingestion (this happens automatically inside the retriever)
3. **Step 3** — Performs cosine similarity search in ChromaDB to find the top-K chunks closest to the question vector

**Key functions:**
```python
get_retriever(vectordb, top_k=3)
# Input:  ChromaDB instance + number of results to return
# Output: a LangChain Retriever object (callable)

retrieve_relevant_docs(retriever, query="What is RAG?")
# Input:  retriever + user question string
# Output: list of top-K Document objects most relevant to the question
```

**Example output:**
```
[1] Query: What is overfitting?
[2] Embedding query...
[3] Retrieved 3 relevant chunks from Vector Database
    Chunk 1: Overfitting occurs when a model learns the training data too well...
    Chunk 2: Regularization techniques like L1 and L2 penalties prevent overfitting...
    Chunk 3: Early stopping monitors validation loss and stops training when...
```

---

### `src/generator.py` — LLM Response Generation (Steps 4, 5)

**Purpose:** Sends the retrieved context chunks + user question to the LLM and generates a grounded answer.

**How it works:**
1. Loads the LLM (GLM-4.5-Air) via OpenRouter API using an OpenAI-compatible interface
2. Loads the API key from the `.env` file automatically using `python-dotenv`
3. Uses a **strict prompt template** (from `prompts/strict/strict_qa.py`) that instructs the LLM to ONLY answer from the provided context — never from its own training data
4. Builds an LCEL (LangChain Expression Language) chain: `Retriever → Format Docs → Prompt → LLM → Parse Output`
5. Returns the answer text + source documents used

**Key functions:**
```python
get_llm(model_name="z-ai/glm-4.5-air:free", temperature=0.3)
# Returns: ChatOpenAI instance connected to OpenRouter API

create_rag_chain(llm, retriever)
# Builds the full chain: retriever | format_docs + question | prompt | llm | parser
# Returns: an invokable LCEL chain

generate_response(rag_chain, query, retriever)
# Input:  the chain + user question + retriever (for fetching sources)
# Output: tuple of (answer_string, source_documents)
```

**The LCEL chain flow:**
```
User Question
     ↓
┌────────────────────┐
│ Retriever          │ → finds top-K relevant chunks
├────────────────────┤
│ format_docs()      │ → joins chunks into one context string
├────────────────────┤
│ Prompt Template    │ → fills {context} and {question} into the strict prompt
├────────────────────┤
│ LLM (GLM-4.5-Air) │ → generates answer based on context only
├────────────────────┤
│ StrOutputParser    │ → extracts plain text from LLM response
└────────────────────┘
     ↓
  Final Answer
```

**Prompt switching:** You can change the active prompt by editing the import at the top of `generator.py`. 9 prompt templates are available in the `prompts/` folder.

---

### `src/pipeline.py` — Full Pipeline Orchestrator

**Purpose:** Connects ALL the above files into a single `RAGPipeline` class with simple `ingest()`, `setup_qa()`, and `query()` methods.

**How it works:**
- Acts as the **central controller** that calls `loader.py` → `chunker.py` → `embedder.py` → `retriever.py` → `generator.py` in the correct order
- `app.py` (the CLI) only talks to `pipeline.py` — it never imports the individual src files directly

**Key class and methods:**
```python
class RAGPipeline:
    def __init__(self, data_path="./data", vectordb_path="./vectordb", llm_model="z-ai/glm-4.5-air:free")

    def ingest(chunk_size=500, chunk_overlap=50)
        # Runs: loader.py → chunker.py → embedder.py
        # Result: documents are embedded and stored in ChromaDB

    def setup_qa(top_k=3)
        # Runs: embedder.py (load) → retriever.py → generator.py (create chain)
        # Result: RAG chain is ready to answer questions

    def query(question)
        # Runs: retriever.py → generator.py
        # Result: returns (answer, source_documents)
```

**Complete flow when user types `ingest` then `query`:**
```
ingest:
  loader.py    → loads PDFs/TXTs from data/
  chunker.py   → splits into 1000-char chunks
  embedder.py  → embeds chunks → stores in ChromaDB

query "What is RAG?":
  retriever.py → embeds question → searches ChromaDB → returns top-3 chunks
  generator.py → sends chunks + question to LLM → returns grounded answer
```

---

## Tech Stack

| Component | Tool | Cost |
|-----------|------|------|
| **Framework** | LangChain | Free |
| **Embeddings** | HuggingFace `sentence-transformers/all-MiniLM-L6-v2` | Free (local) |
| **Vector Database** | ChromaDB | Free (local) |
| **LLM** | Z.ai GLM-4.5-Air via OpenRouter | Free |
| **Document Parsing** | PyPDF | Free |
| **Language** | Python 3.10+ | Free |

---

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- Git (optional, for cloning)

### Step 1: Clone or Download

```bash
git clone <your-repo-url>
cd ldsrag
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
```

Activate it:

- **Windows (PowerShell):**
  ```powershell
  venv\Scripts\Activate.ps1
  ```
- **Windows (CMD):**
  ```cmd
  venv\Scripts\activate.bat
  ```
- **macOS/Linux:**
  ```bash
  source venv/bin/activate
  ```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Get OpenRouter API Key (Free)

1. Go to [https://openrouter.ai](https://openrouter.ai) and sign up (free)
2. Navigate to [https://openrouter.ai/keys](https://openrouter.ai/keys)
3. Create a new API key
4. Open the `.env` file and paste your key:

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### Step 5: Add Your Documents

Place your PDF or TXT files in the `data/` folder:

```
data/
├── your_document.pdf
├── notes.txt
└── research_paper.pdf
```

### Step 6: Run the Application

```bash
python app.py
```

### Step 7: Run the Streamlit Web UI (Optional)

Instead of the CLI, you can use the beautiful Streamlit web interface:

```bash
streamlit run streamlit_app.py
```

This opens a web app at **http://localhost:8501** with:
- **Chat interface** — ask questions and get answers in a conversation view
- **Sidebar controls** — switch LLM models, adjust chunk size/overlap/top-k
- **Document list** — see all files in `data/` with sizes
- **Vector DB status** — view how many vectors are stored
- **Ingest button** — process documents with one click
- **Source chunks** — expandable view of which chunks were used per answer
- **Response time** — see how long each query took

> **Note:** Both `app.py` (CLI) and `streamlit_app.py` (Web UI) use the same RAG pipeline. You can use either one.

---

## Usage

### Ingest Documents (A → B → C → D)

This processes your documents and stores them in the vector database. Run this once, or whenever you add new documents.

```
> ingest
```

Output:
```
--- Step A + B: Raw Data Sources + Information Extraction ---
[A] Found 1 files in './data'
[B] Extracted 1 document(s) from TXT: sample_document.txt

--- Step C: Chunking ---
[C] Chunking: 1 documents → 3 chunks

--- Step D: Embedding → Vector Database ---
[D] Embedding model loaded: sentence-transformers/all-MiniLM-L6-v2
[D] Stored 3 chunks in Vector Database (ChromaDB)
```

### Query Documents (1 → 2 → 3 → 4 → 5)

Ask questions about your documents:

```
> query

[?] What is RAG?

[Answer]: RAG (Retrieval Augmented Generation) is a technique that combines
the strengths of large language models with external knowledge retrieval...
```

### Commands

| Command | Description |
|---------|-------------|
| `ingest` | Process documents and build vector database |
| `query` | Ask questions about your documents |
| `help` | Show available commands |
| `exit` | Quit the application |

---

## Changing the LLM Model

Edit the `LLM_MODEL` variable in `app.py`:

```python
# Free models available on OpenRouter:
LLM_MODEL = "z-ai/glm-4.5-air:free"          # Default — best balance
LLM_MODEL = "stepfun/step-3.5-flash:free"     # Fast + good reasoning
LLM_MODEL = "openai/gpt-oss-120b:free"        # Strong reasoning
LLM_MODEL = "arcee-ai/trinity-mini:free"      # Efficient + long context
```

---

## Configuration

### Chunk Size

Edit `src/pipeline.py` → `ingest()` method:

```python
rag.ingest(chunk_size=500, chunk_overlap=50)  # Default
rag.ingest(chunk_size=1000, chunk_overlap=100)  # For longer documents
```

### Number of Retrieved Chunks

Edit `src/pipeline.py` → `setup_qa()` method:

```python
rag.setup_qa(top_k=3)  # Default: returns 3 most relevant chunks
rag.setup_qa(top_k=5)  # More context for complex questions
```

### Embedding Model

Edit `src/embedder.py`:

```python
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"        # Default (fast)
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"        # Better quality
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # Multilingual
```

> **Note:** If you change the embedding model, delete the `vectordb/` folder and re-run `ingest`.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Make sure venv is activated: `venv\Scripts\Activate.ps1` |
| `OPENROUTER_API_KEY not set` | Add your key to the `.env` file |
| `No documents found` | Put PDF/TXT files in the `data/` folder |
| `Vector DB empty` | Run `ingest` first to process documents |
| Model ID error (400) | Check [OpenRouter models](https://openrouter.ai/models) for valid free model IDs |

---

## How RAG Solves LLM Limitations

| LLM Problem | How RAG Fixes It |
|-------------|------------------|
| **Hallucination** | Grounds answers in your actual documents |
| **Outdated knowledge** | Uses your latest documents, no retraining needed |
| **No private data access** | Works with your proprietary/internal documents |
| **Expensive fine-tuning** | No model training required — just add documents |
| **Black box answers** | Shows which source chunks were used |

---

## License

This project is open-source. Feel free to use, modify, and distribute.
# SummarizerUsingRag
