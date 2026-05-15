import json

from app.llm.gemini import (
    generate_answer
)


def critique_answer(
    question: str,
    answer: str,
    context: str
):

    prompt = f"""
You are a retrieval critique agent.

Your task:
Evaluate whether the answer is sufficiently supported.

QUESTION:
{question}

ANSWER:
{answer}

CONTEXT:
{context}

Determine:

1. Is evidence sufficient?
2. Are important details missing?
3. Is retrieval incomplete?
4. Should another search be performed?

Return STRICT JSON:

{{
  "sufficient": true/false,
  "missing_information": "...",
  "improved_queries": [
    "..."
  ]
}}
"""

    response = generate_answer(
        prompt
    )

    try:

        return json.loads(response)

    except Exception:

        return {
            "sufficient": True,
            "missing_information": "",
            "improved_queries": []
        }