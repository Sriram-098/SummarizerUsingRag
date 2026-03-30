"""
========================================
Steps 4, 5: LLM → Response
========================================
Sends relevant data + query to LLM and generates response.
Uses OpenRouter API (FREE models available) - needs API key from https://openrouter.ai/keys

Supported FREE models (change in app.py):
  - z-ai/glm-4.5-air:free       → BEST BALANCE (agents + chat)
  - stepfun/step-3.5-flash:free  → fast + good reasoning
  - openai/gpt-oss-120b:free     → strong reasoning
  - arcee-ai/trinity-mini:free   → efficient + long context
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Load .env file automatically
load_dotenv()

# Import strict prompt from prompts folder
from prompts.strict.strict_qa import STRICT_PROMPT

# Active prompt template (change this to switch prompt styles)
# Options:
#   from prompts.strict.strict_qa import STRICT_PROMPT
#   from prompts.strict.strict_cited import STRICT_CITED_PROMPT
#   from prompts.conversational.friendly import CONVERSATIONAL_PROMPT
#   from prompts.conversational.eli5 import ELI5_PROMPT
#   from prompts.analytical.summarizer import SUMMARY_PROMPT
#   from prompts.analytical.comparison import COMPARISON_PROMPT
#   from prompts.analytical.step_by_step import STEP_BY_STEP_PROMPT
#   from prompts.domain.technical import TECHNICAL_PROMPT
#   from prompts.domain.academic import ACADEMIC_PROMPT
#   from prompts.domain.legal import LEGAL_PROMPT
PROMPT_TEMPLATE = STRICT_PROMPT


def get_llm(model_name="z-ai/glm-4.5-air:free", temperature=0.3):
    """
    Load the LLM using OpenRouter API (FREE models).

    Architecture Mapping:
        4 → LLM(s) - Large Language Model (via OpenRouter cloud)

    Prerequisites:
        1. Sign up at https://openrouter.ai (free)
        2. Get API key from https://openrouter.ai/keys
        3. Set environment variable: OPENROUTER_API_KEY=sk-or-...

    Args:
        model_name: OpenRouter model name
        temperature: Creativity (0=focused, 1=creative)

    Returns:
        ChatOpenAI instance configured for OpenRouter
    """
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY not set!\n"
            "1. Get free key at: https://openrouter.ai/keys\n"
            "2. Set it: $env:OPENROUTER_API_KEY='sk-or-...'\n"
        )

    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
    )
    print(f"[4] LLM loaded: {model_name} (via OpenRouter, temperature={temperature})")
    return llm


def format_docs(docs):
    """Format retrieved documents into a single context string."""
    return "\n\n".join(doc.page_content for doc in docs)


def create_rag_chain(llm, retriever):
    """
    Create the complete RAG chain connecting retriever → LLM.

    Architecture Mapping:
        Full chain: Query(1) → Embed(2) → Retrieve(3) → LLM(4) → Response(5)

    Args:
        llm: Language model
        retriever: Vector database retriever

    Returns:
        LCEL RAG chain
    """
    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["context", "question"]
    )

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    print("[4+5] RAG Chain created: Retriever → LLM → Response")
    return rag_chain


def generate_response(rag_chain, query: str, retriever=None):
    """
    Generate a response using the full RAG pipeline.

    Architecture Mapping:
        4 → Relevant data + Query sent to LLM
        5 → Response generated

    Args:
        rag_chain: Complete RAG chain
        query: User's question
        retriever: Optional retriever to fetch source docs separately

    Returns:
        Tuple of (answer_text, source_documents)
    """
    print(f"\n{'='*60}")
    print(f"[1] Query: {query}")

    answer = rag_chain.invoke(query)

    # Fetch source docs separately if retriever is provided
    sources = retriever.invoke(query) if retriever else []

    print(f"[5] Response generated ({len(answer)} chars, {len(sources)} sources)")
    print(f"{'='*60}\n")

    return answer, sources
