"""
Query Intent Router — Phase B of Multi-Tier RAG.

Classifies incoming user queries into one of four tiers:
  - chunk_retrieval:    Specific fact/detail lookup (existing hybrid RAG)
  - document_summary:   High-level summary or overview
  - aggregation:        Mathematical calculation, counting, totaling
  - comparison:         Compare or contrast multiple documents

Uses rule-based keyword matching first (zero latency, no LLM call).
Falls back to a lightweight LLM classification only for ambiguous queries.
"""

from typing import Literal

from app.llm.gemini import generate_answer_async


QueryIntent = Literal[
    "chunk_retrieval",
    "document_summary",
    "aggregation",
    "comparison",
]


# ── Rule-based keyword sets (fast path, no LLM call needed) ──────────

_SUMMARY_KEYWORDS = frozenset([
    "summarize", "summary", "overview", "what is this about",
    "what does this document", "describe the document", "main points",
    "key points", "gist", "tldr", "tl;dr", "what is this paper",
    "give me a summary", "explain the document", "what are the key",
    "main themes", "high level", "high-level", "brief overview",
    "document overview", "overall description",
])

_AGGREGATION_KEYWORDS = frozenset([
    "total", "sum", "average", "count", "how many", "calculate",
    "add up", "aggregate", "tally", "overall cost", "grand total",
    "how much", "expenditure", "net", "gross", "list all",
    "enumerate all", "count the", "number of",
])

_COMPARISON_KEYWORDS = frozenset([
    "compare", "comparison", "difference between", "contrast",
    "versus", " vs ", "similarities", "how do they differ",
    "which is better", "both documents", "differences",
])


async def classify_query(
    question: str,
    active_files: list,
) -> QueryIntent:
    """
    Classify user query into a retrieval tier.

    Args:
        question: The (possibly rewritten) user query.
        active_files: List of selected filenames in the current chat.

    Returns:
        One of the QueryIntent literal values.
    """
    q = question.lower()

    # ── Fast path: rule-based heuristics ─────────────────────────────
    if any(kw in q for kw in _SUMMARY_KEYWORDS):
        return "document_summary"

    if any(kw in q for kw in _AGGREGATION_KEYWORDS):
        return "aggregation"

    if any(kw in q for kw in _COMPARISON_KEYWORDS) and len(active_files) > 1:
        return "comparison"

    # ── Slow path: LLM fallback for ambiguous queries ────────────────
    prompt = (
        "Classify this user query about PDF documents into exactly one category:\n"
        "- chunk_retrieval: specific fact, detail, definition, or page-level lookup\n"
        "- document_summary: high-level overview, summary, or global description\n"
        "- aggregation: mathematical calculation, counting, totaling across the document\n"
        "- comparison: compare or contrast two or more documents\n\n"
        f"Active documents: {', '.join(active_files) if active_files else 'none selected'}\n"
        f"Query: {question}\n\n"
        "Respond with ONLY the category label, nothing else."
    )

    try:
        result = (await generate_answer_async(prompt)).strip().lower()
        valid = {"chunk_retrieval", "document_summary", "aggregation", "comparison"}
        return result if result in valid else "chunk_retrieval"
    except Exception as e:
        print(f"[router] LLM classification failed, defaulting to chunk_retrieval: {e}")
        return "chunk_retrieval"
