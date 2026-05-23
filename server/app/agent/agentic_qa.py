from typing import Optional
import json

from app.agent.planner import (
    generate_search_queries
)

from app.agent.evidence import (
    gather_evidence
)

from app.qa.ask import (
    build_context
)

from app.llm.gemini import (
    generate_answer
)

from app.qa.query_rewriter import (
    rewrite_query
)


def ask_agentic_question(
    question: str,
    user_id: str = "default_tenant",
    session_id: Optional[str] = None
):

    # -------------------------
    # Query Rewriting
    # -------------------------

    rewritten_question = rewrite_query(
        question,
        user_id=user_id,
        session_id=session_id
    )

    # -------------------------
    # Context-Aware Query Planning
    # (planner now uses two-stage retrieval)
    # -------------------------

    raw_queries = generate_search_queries(
        rewritten_question,
        user_id=user_id
    )

    try:
        queries = json.loads(raw_queries)
    except Exception:
        queries = [rewritten_question]

    all_queries = list(queries)

    # -------------------------
    # Gather Evidence
    # -------------------------

    chunks = gather_evidence(
        all_queries,
        user_id=user_id
    )

    context = build_context(
        chunks
    )

    # -------------------------
    # Generate Answer
    # -------------------------

    prompt = f"""
You are an advanced multimodal RAG system.

Answer the question using the evidence.
Exception: If the user asks to solve, answer, or complete questions/tasks/assignments that are listed or found within the document (e.g., a test paper or problem set) and the document itself does not contain the answers/solutions, you should use your own knowledge to solve and answer them, while clearly noting that you are solving/answering the questions from the document using external knowledge.

ORIGINAL QUESTION:
{question}

REWRITTEN QUESTION:
{rewritten_question}

SEARCH QUERIES:
{all_queries}

EVIDENCE:
{context}
"""

    answer = generate_answer(
        prompt
    )

    return {
        "question": question,

        "rewritten_question": rewritten_question,

        "queries": all_queries,

        "answer": answer,

        "retrieved_chunks": [
            {
                "chunk_id": c.get(
                    "retrieval_id",
                    c.get("id")
                ),

                "source_file": c.get(
                    "source_file"
                ),

                "page": c.get(
                    "page"
                ),

                "vector_score": c.get(
                    "vector_score"
                ),

                "bm25_score": c.get(
                    "bm25_score"
                ),

                "rerank_score": c.get(
                    "rerank_score"
                ),

                "preview": c.get(
                    "text",
                    ""
                )[:300]
            }
            for c in chunks
        ]
    }