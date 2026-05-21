from app.retrieval.retrieve import retrieve_chunks, retrieve_chunks_async

from app.memory.memory import (
    add_message
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


async def stream_question(question: str):

    rewritten_question = await rewrite_query_async(
        question
    )

    chunks = await retrieve_chunks_async(
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

    final_answer = ""

    async for token in stream_answer_async(
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