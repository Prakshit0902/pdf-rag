from app.memory.memory import get_history, get_history_async
from typing import Optional

from app.llm.gemini import generate_answer, generate_answer_async


def rewrite_query(
    current_question: str,
    user_id: str = "default_tenant",
    session_id: Optional[str] = None
):

    history = get_history(user_id=user_id, session_id=session_id)

    if not history:
        return current_question

    history_text = "\n".join([
        f"{m['role']}: {m['content']}"
        for m in history
    ])

    prompt = f"""
You are a query rewriting system.

Your task:
Rewrite the user's latest question into a fully self-contained question.

Rules:
- preserve original meaning
- resolve pronouns/references
- include relevant context from chat history
- do NOT answer the question
- only rewrite it

CHAT HISTORY:
{history_text}

LATEST QUESTION:
{current_question}
"""

    rewritten = generate_answer(prompt)

    return rewritten.strip()


async def rewrite_query_async(
    current_question: str,
    user_id: str = "default_tenant",
    session_id: Optional[str] = None
):

    history = await get_history_async(user_id=user_id, session_id=session_id)

    if not history:
        return current_question

    history_text = "\n".join([
        f"{m['role']}: {m['content']}"
        for m in history
    ])

    prompt = f"""
You are a query rewriting system.

Your task:
Rewrite the user's latest question into a fully self-contained question.

Rules:
- preserve original meaning
- resolve pronouns/references
- include relevant context from chat history
- do NOT answer the question
- only rewrite it

CHAT HISTORY:
{history_text}

LATEST QUESTION:
{current_question}
"""

    rewritten = await generate_answer_async(prompt)

    return rewritten.strip()