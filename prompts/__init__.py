"""
Prompt Templates for RAG System
================================

Available prompt categories:

1. strict/        — Answers ONLY from documents, no outside knowledge
   - strict_qa.py       : Default strict Q&A
   - strict_cited.py    : Strict with source citations

2. conversational/ — Friendly, natural tone
   - friendly.py        : Conversational Q&A
   - eli5.py            : Explain Like I'm 5

3. analytical/     — Structured analysis of document content
   - summarizer.py      : Bullet-point summaries
   - comparison.py      : Compare/contrast information
   - step_by_step.py    : Extract procedures as numbered steps

4. domain/         — Domain-specific professional formats
   - technical.py       : Technical expert responses
   - academic.py        : Formal academic style
   - legal.py           : Legal/compliance cautious style

Usage:
    from prompts.strict.strict_qa import STRICT_PROMPT
    from prompts.conversational.eli5 import ELI5_PROMPT
"""
