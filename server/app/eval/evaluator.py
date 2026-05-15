from app.llm.gemini import generate_answer


def evaluate_answer(
    question: str,
    answer: str,
    retrieved_chunks: list
):

    context = "\n\n".join([
        chunk["text"]
        for chunk in retrieved_chunks
    ])

    prompt = f"""
You are an expert RAG evaluator.

Evaluate the following answer.

QUESTION:
{question}

ANSWER:
{answer}

RETRIEVED CONTEXT:
{context}

Evaluate on:

1. Groundedness
- Is answer supported by context?

2. Hallucination Risk
- Did answer invent unsupported claims?

3. Context Relevance
- Were retrieved chunks relevant?

4. Completeness
- Did answer fully address question?

Return STRICT JSON:

{{
  "groundedness": 0-10,
  "hallucination_risk": 0-10,
  "context_relevance": 0-10,
  "completeness": 0-10,
  "overall_reasoning": "..."
}}
"""

    evaluation = generate_answer(
        prompt
    )

    return evaluation