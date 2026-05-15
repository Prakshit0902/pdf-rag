from sentence_transformers import CrossEncoder


MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


model = CrossEncoder(MODEL_NAME)


def rerank_chunks(
    query: str,
    chunks: list,
    top_k: int = 5
):

    pairs = [
        [query, chunk["text"]]
        for chunk in chunks
    ]

    scores = model.predict(pairs)

    scored_chunks = []

    for chunk, score in zip(chunks, scores):

        chunk["rerank_score"] = float(score)

        scored_chunks.append(chunk)

    scored_chunks.sort(
        key=lambda x: x["rerank_score"],
        reverse=True
    )

    return scored_chunks[:top_k]