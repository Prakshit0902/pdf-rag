from functools import partial
import anyio
from app.embeddings.embedder import get_embedding, get_embedding_async

from app.vectorstore.qdrant_client import client

from app.retrieval.reranker import rerank_chunks, rerank_chunks_async
from app.retrieval.bm25_index import bm25_search
from app.retrieval.parent_retrieval import expand_parent_context


COLLECTION_NAME = "pdf_rag"


def vector_search(
    query: str,
    limit: int = 10,
    user_id: str = "default_tenant"
):

    query_embedding = get_embedding(query, task_type="RETRIEVAL_QUERY")

    from qdrant_client.models import Filter, FieldCondition, MatchValue
    query_filter = Filter(
        must=[
            FieldCondition(key="user_id", match=MatchValue(value=user_id))
        ]
    )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        query_filter=query_filter,
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

    # Add vector chunks first
    for chunk in vector_chunks:
        merged[chunk["id"]] = chunk

    # Merge BM25 scores into existing chunks (don't overwrite)
    for chunk in bm25_chunks:

        chunk_id = chunk["id"]

        if chunk_id in merged:
            # Preserve vector scores, add BM25 score
            existing = merged[chunk_id]
            if "bm25_score" in chunk:
                existing["bm25_score"] = chunk["bm25_score"]
        else:
            # New chunk from BM25
            merged[chunk_id] = chunk

    return list(merged.values())


def retrieve_chunks(
    query: str,
    vector_limit: int = 10,
    bm25_limit: int = 10,
    rerank_top_k: int = 5,
    user_id: str = "default_tenant"
):

    vector_chunks = vector_search(
        query,
        limit=vector_limit,
        user_id=user_id
    )

    bm25_chunks = bm25_search(
        query,
        user_id=user_id,
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
        window_size=1,
        user_id=user_id
    )
    
    return expanded_chunks


async def vector_search_async(
    query: str,
    limit: int = 10,
    user_id: str = "default_tenant"
):
    query_embedding = await get_embedding_async(query, task_type="RETRIEVAL_QUERY")

    from qdrant_client.models import Filter, FieldCondition, MatchValue
    query_filter = Filter(
        must=[
            FieldCondition(key="user_id", match=MatchValue(value=user_id))
        ]
    )

    results = await anyio.to_thread.run_sync(
        partial(
            client.query_points,
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            query_filter=query_filter,
            limit=limit
        )
    )

    chunks = []
    for result in results.points:
        payload = result.payload
        payload["vector_score"] = result.score
        payload["id"] = str(result.id)
        chunks.append(payload)

    return chunks


async def retrieve_chunks_async(
    query: str,
    vector_limit: int = 10,
    bm25_limit: int = 10,
    rerank_top_k: int = 5,
    user_id: str = "default_tenant"
):
    import asyncio
    vector_task = vector_search_async(query, limit=vector_limit, user_id=user_id)
    bm25_task = anyio.to_thread.run_sync(
        partial(bm25_search, query, user_id=user_id, top_k=bm25_limit)
    )

    vector_chunks, bm25_chunks = await asyncio.gather(vector_task, bm25_task)

    merged_chunks = merge_results(
        vector_chunks,
        bm25_chunks
    )

    reranked_chunks = await rerank_chunks_async(
        query,
        merged_chunks,
        top_k=rerank_top_k
    )

    expanded_chunks = await anyio.to_thread.run_sync(
        partial(expand_parent_context, reranked_chunks, window_size=1, user_id=user_id)
    )

    return expanded_chunks