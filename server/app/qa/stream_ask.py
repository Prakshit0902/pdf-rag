from typing import Optional, List
from app.retrieval.retrieve import retrieve_chunks, retrieve_chunks_async, retrieve_per_file_async

from app.memory.memory import (
    add_message_async
)

from app.qa.query_rewriter import (
    rewrite_query,
    rewrite_query_async
)

from app.llm.gemini import (
    stream_answer,
    stream_answer_async
)

from app.qa.ask import build_context

from app.agent.router import classify_query
from app.agent.handlers import (
    handle_document_summary,
    handle_aggregation,
    handle_comparison,
)


async def stream_question(
    question: str,
    user_id: str = "default_tenant",
    session_id: Optional[str] = None,
    selected_files: Optional[List[str]] = None
):

    rewritten_question = await rewrite_query_async(
        question,
        user_id=user_id,
        session_id=session_id
    )

    # ── Intent classification ────────────────────────────────────────
    intent = await classify_query(rewritten_question, selected_files or [])
    print(f"[router] Query intent: {intent} | Files: {selected_files}")

    final_answer = ""

    # ── Tier dispatch for non-chunk intents ───────────────────────────
    if intent == "document_summary":
        async for token in handle_document_summary(
            rewritten_question, selected_files or [], user_id
        ):
            final_answer += token
            yield token

    elif intent == "aggregation":
        async for token in handle_aggregation(
            rewritten_question, selected_files or [], user_id
        ):
            final_answer += token
            yield token

    elif intent == "comparison":
        async for token in handle_comparison(
            rewritten_question, selected_files or [], user_id,
            selected_files or []
        ):
            final_answer += token
            yield token

    else:
        # ── CHUNK_RETRIEVAL: existing pipeline with per-file fairness ─
        chunks = await retrieve_per_file_async(
            rewritten_question,
            user_id=user_id,
            selected_files=selected_files
        )

        context = build_context(chunks)

        image_paths = []

        page_renders = []

        for chunk in chunks:

            images = chunk.get(
                "images",
                []
            )

            image_paths.extend(images)

            page_render = chunk.get(
                "page_render"
            )

            if page_render:

                page_renders.append(
                    page_render
                )

        image_paths = list(
            set(image_paths)
        )

        page_renders = list(
            set(page_renders)
        )

        prompt = f"""
You are a helpful AI assistant answering questions from documents.

Answer in clean markdown format. Use:
- **bold** for key terms
- bullet points for lists
- code blocks for any code/technical content

Only answer from the provided context. If uncertain, say so. 
Exception: If the user asks to solve, answer, or complete questions/tasks/assignments that are listed or found within the document (e.g., a test paper or problem set) and the document itself does not contain the answers/solutions, you should use your own knowledge to solve and answer them, while clearly noting that you are solving/answering the questions from the document using external knowledge.

QUESTION:
{question}

REWRITTEN QUESTION:
{rewritten_question}

CONTEXT:
{context}

Provide a well-formatted answer in markdown. List sources at the end as:
**Sources:** [file.pdf, page X], [file2.pdf, page Y]
"""

        async for token in stream_answer_async(
            prompt,
            image_paths=image_paths + page_renders
        ):

            final_answer += token

            yield token

    # ── Save to chat history (all tiers) ─────────────────────────────
    await add_message_async(
        "user",
        question,
        user_id=user_id,
        session_id=session_id
    )

    await add_message_async(
        "assistant",
        final_answer,
        user_id=user_id,
        session_id=session_id
    )