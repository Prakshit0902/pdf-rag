from app.retrieval.retrieve import retrieve_chunks

from app.memory.memory import (
    add_message
)

from app.qa.query_rewriter import (
    rewrite_query
)

from app.llm.gemini import (
    stream_answer
)

from app.qa.ask import build_context


def stream_question(question: str):

    rewritten_question = rewrite_query(
        question
    )

    chunks = retrieve_chunks(
        rewritten_question
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
You are a highly accurate multimodal document QA system.

Answer ONLY from the provided context and images.

Always:
- cite SOURCE_FILE
- cite PAGE
- cite CHUNK_ID
- avoid hallucinations

QUESTION:
{question}

REWRITTEN QUESTION:
{rewritten_question}

CONTEXT:
{context}
"""

    final_answer = ""

    for token in stream_answer(
        prompt,
        image_paths=image_paths + page_renders
    ):

        final_answer += token

        yield token

    add_message(
        "user",
        question
    )

    add_message(
        "assistant",
        final_answer
    )