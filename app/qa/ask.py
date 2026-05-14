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

    prompt = f"""
You are a highly accurate document QA system.

Answer ONLY from the provided context.

If the answer is not present,
say:
"I could not find this in the documents."

Always:
- cite source file names
- mention page numbers if available
- be concise but complete
- avoid hallucinations

QUESTION:
{question}

CONTEXT:
{context}
"""

    answer = generate_answer(prompt)

    return {
        "question": question,
        "answer": answer,
        "retrieved_chunks": chunks
    }