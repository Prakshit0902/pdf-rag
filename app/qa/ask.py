from app.retrieval.retrieve import retrieve_chunks
from app.llm.gemini import generate_answer


def build_context(chunks):

    context_parts = []

    for index, chunk in enumerate(chunks):

        text = chunk["text"]

        source = chunk["source_file"]

        page = chunk.get("page")

        score = round(chunk["score"], 4)

        context = f"""
SOURCE: {source}
PAGE: {page}
RELEVANCE: {score}

CONTENT:
{text}
"""

        context_parts.append(context)

    return "\n\n-------------------\n\n".join(
        context_parts
    )


def ask_question(question: str):

    chunks = retrieve_chunks(question)

    context = build_context(chunks)

    image_paths = []
    page_renders = []

    for chunk in chunks:

        images = chunk.get("images", [])

        image_paths.extend(images)
        
        page_render = chunk.get("page_render")
        
        if page_render:
            page_renders.append(page_render)

    # deduplicate
    image_paths = list(set(image_paths))
    page_renders = list(set(page_renders))

    prompt = f"""
You are a highly accurate multimodal document QA system.

Answer ONLY from the provided context and images.

If the answer is not present,
say:
"I could not find this in the documents."

Always:
- cite source file names
- mention page numbers if available
- use image evidence when relevant
- avoid hallucinations

QUESTION:
{question}

CONTEXT:
{context}
"""

    answer = generate_answer(
        prompt,
        image_paths=image_paths + page_renders
    )

    return {
        "question": question,
        "answer": answer,
        "retrieved_chunks": chunks
    }