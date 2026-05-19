from app.retrieval.retrieve import retrieve_chunks
from app.llm.gemini import generate_answer
from app.memory.memory import (add_message)

from app.qa.query_rewriter import (rewrite_query)
from app.eval.evaluator import evaluate_answer


def build_context(chunks):

    context_parts = []

    for index, chunk in enumerate(chunks):
        # print(f"Processing chunk {index}: {chunk}")

        text = chunk["text"]

        source = chunk["source_file"]

        page = chunk.get("page")

        context = f"""
        CHUNK_ID: {chunk["id"]}

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
    from app.benchmark_tracker import BenchmarkTracker
    
    tracker = BenchmarkTracker("standard_qa")
    with tracker:

        with tracker.step("rewrite_query"):
            rewritten_question = rewrite_query(
                question
            )
            
        with tracker.step("retrieve_chunks"):
            chunks = retrieve_chunks(rewritten_question)

        with tracker.step("build_context"):
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

        ORIGINAL QUESTION:
        {question}

        REWRITTEN QUESTION:
        {rewritten_question}

        CONTEXT:
        {context}
        """

        with tracker.step("generate_answer"):
            answer = generate_answer(
                prompt,
                image_paths=image_paths + page_renders
            )
        
        with tracker.step("add_message"):
            add_message(
                "user",
                question
            )

            add_message(
                "assistant",
                answer
            )
        
        with tracker.step("evaluate_answer"):
            evaluation = evaluate_answer(question, answer, chunks)

    return {
        "question": question,
        "answer": answer,
        "evaluation": evaluation,

        "retrieved_chunks": [
            {
                "chunk_id": c["id"],

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

                "preview": c["text"][:300],
                "rewritten_question": rewritten_question,
                
            }
            for c in chunks
        ]
    }