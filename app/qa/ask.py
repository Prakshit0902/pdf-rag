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
        CHUNK_ID: {chunk["retrieval_id"]}

        SOURCE_FILE: {source}

        PAGE: {page}

        VECTOR_SCORE: {round(chunk.get("vector_score", 0), 4)}

        BM25_SCORE: {round(chunk.get("bm25_score", 0), 4)}

        RERANK_SCORE: {round(chunk.get("rerank_score", 0), 4)}

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
        - cite SOURCE_FILE
        - cite PAGE
        - cite CHUNK_ID
        - mention when evidence is weak
        - avoid unsupported claims
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

        "retrieved_chunks": [
            {
                "chunk_id": c["retrieval_id"],

                "source_file": c["source_file"],

                "page": c["page"],

                "vector_score": c.get(
                    "vector_score"
                ),

                "bm25_score": c.get(
                    "bm25_score"
                ),

                "rerank_score": c.get(
                    "rerank_score"
                ),

                "preview": c["text"][:300]
            }
            for c in chunks
        ]
    }