from app.embeddings.embedder import get_embedding
from app.vectorstore.qdrant_client import client


COLLECTION_NAME = "pdf_rag"


def retrieve_chunks(
    query: str,
    limit: int = 5
):

    query_embedding = get_embedding(query)

    results = client.query_points(
        collection_name=COLLECTION_NAME,

        query=query_embedding,

        limit=limit,
    )

    retrieved_chunks = []

    for result in results.points:

        payload = result.payload

        payload["score"] = result.score

        retrieved_chunks.append(payload)

    return retrieved_chunks