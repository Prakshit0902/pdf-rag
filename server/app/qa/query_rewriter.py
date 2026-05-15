from app.memory.memory import get_history

from app.llm.gemini import generate_answer


def rewrite_query(
    current_question: str
):

    history = get_history()

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