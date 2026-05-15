from app.llm.gemini import generate_answer
from app.retrieval.retrieve import retrieve_chunks
from app.qa.ask import build_context


def generate_search_queries(
    question: str,
    context_limit: int = 3
):
    """
    Two-stage retrieval planning:
    1. Quick retrieval to get document context
    2. Generate queries specific to retrieved content
    """

    # -------------------------
    # Stage 1: Get document context
    # -------------------------
    initial_chunks = retrieve_chunks(
        question,
        vector_limit=context_limit,
        bm25_limit=context_limit,
        rerank_top_k=context_limit
    )

    context = build_context(initial_chunks)

    # -------------------------
    # Stage 2: Generate context-aware queries
    # -------------------------
    prompt = f"""
You are a retrieval planning agent for a local document system.

Generate up to 4 specific search queries based on the document context provided.

Rules:
- queries should be specific to the document content below
- use keywords from the documents
- explore different aspects of the question
- keep queries concise and focused
- avoid generic web-search style queries
- return ONLY JSON array of strings

DOCUMENT CONTEXT:
{context}

QUESTION:
{question}
"""

    response = generate_answer(
        prompt
    )

    return response