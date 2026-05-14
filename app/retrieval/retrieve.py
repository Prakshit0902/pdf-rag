from app.embeddings.embedder import get_embedding

from app.vectorstore.qdrant_client import client

from app.retrieval.reranker import rerank_chunks
from app.retrieval.bm25_index import bm25_search
from app.retrieval.parent_retrieval import expand_parent_context


COLLECTION_NAME = "pdf_rag"


def vector_search(
    query: str,
    limit: int = 10
):

    query_embedding = get_embedding(query)

    results = client.query_points(
        collection_name=COLLECTION_NAME,

        query=query_embedding,

        limit=limit,
    )

    chunks = []

    for result in results.points:

        payload = result.payload

        payload["vector_score"] = result.score
        payload["id"] = str(result.id)

        chunks.append(payload)

    return chunks


def merge_results(
    vector_chunks,
    bm25_chunks
):

    merged = {}

    for chunk in vector_chunks + bm25_chunks:

        merged[chunk["id"]] = chunk

    return list(merged.values())


def retrieve_chunks(
    query: str,
    vector_limit: int = 10,
    bm25_limit: int = 10,
    rerank_top_k: int = 5
):

    vector_chunks = vector_search(
        query,
        limit=vector_limit
    )

    bm25_chunks = bm25_search(
        query,
        top_k=bm25_limit
    )

    merged_chunks = merge_results(
        vector_chunks,
        bm25_chunks
    )

    reranked_chunks = rerank_chunks(
        query,
        merged_chunks,
        top_k=rerank_top_k
    )

    expanded_chunks = expand_parent_context(
        reranked_chunks,
        window_size=1
    )
    
    return expanded_chunks