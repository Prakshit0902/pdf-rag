from typing import Optional, List
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
    user_id: str = "default_tenant",
    selected_files: Optional[List[str]] = None
):

    query_embedding = get_embedding(query, task_type="RETRIEVAL_QUERY")

    from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny
    must_conditions = [
        FieldCondition(key="user_id", match=MatchValue(value=user_id))
    ]
    if selected_files:
        must_conditions.append(
            FieldCondition(key="source_file", match=MatchAny(any=selected_files))
        )
    query_filter = Filter(must=must_conditions)

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
    user_id: str = "default_tenant",
    selected_files: Optional[List[str]] = None
):

    vector_chunks = vector_search(
        query,
        limit=vector_limit,
        user_id=user_id,
        selected_files=selected_files
    )

    bm25_chunks = bm25_search(
        query,
        user_id=user_id,
        top_k=bm25_limit,
        selected_files=selected_files
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
    user_id: str = "default_tenant",
    selected_files: Optional[List[str]] = None
):
    query_embedding = await get_embedding_async(query, task_type="RETRIEVAL_QUERY")

    from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny
    must_conditions = [
        FieldCondition(key="user_id", match=MatchValue(value=user_id))
    ]
    if selected_files:
        must_conditions.append(
            FieldCondition(key="source_file", match=MatchAny(any=selected_files))
        )
    query_filter = Filter(must=must_conditions)

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
    user_id: str = "default_tenant",
    selected_files: Optional[List[str]] = None
):
    import asyncio
    vector_task = vector_search_async(query, limit=vector_limit, user_id=user_id, selected_files=selected_files)
    bm25_task = anyio.to_thread.run_sync(
        partial(bm25_search, query, user_id=user_id, top_k=bm25_limit, selected_files=selected_files)
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


async def retrieve_per_file_async(
    query: str,
    quota_per_file: int = 5,
    rerank_top_k: int = 7,
    user_id: str = "default_tenant",
    selected_files: Optional[List[str]] = None,
):
    """
    Guarantees at least `quota_per_file` chunks from EACH active document
    before global reranking.  Fixes the multi-PDF sourcing bias where one
    document consumes all K slots when its chunks happen to score higher.

    For single-file or no-selection cases, delegates to retrieve_chunks_async.
    """
    import asyncio
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    if not selected_files or len(selected_files) <= 1:
        return await retrieve_chunks_async(
            query,
            user_id=user_id,
            selected_files=selected_files,
            rerank_top_k=rerank_top_k,
        )

    # Embed the query once (reused across all per-file searches)
    query_embedding = await get_embedding_async(query, task_type="RETRIEVAL_QUERY")

    # Issue one vector search per active file concurrently
    async def _search_one_file(filename: str):
        results = await anyio.to_thread.run_sync(
            partial(
                client.query_points,
                collection_name=COLLECTION_NAME,
                query=query_embedding,
                query_filter=Filter(must=[
                    FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                    FieldCondition(key="source_file", match=MatchValue(value=filename)),
                ]),
                limit=quota_per_file,
            )
        )
        chunks = []
        for r in results.points:
            p = r.payload.copy()
            p["vector_score"] = r.score
            p["id"] = str(r.id)
            chunks.append(p)
        return chunks

    per_file_results = await asyncio.gather(
        *[_search_one_file(f) for f in selected_files],
        return_exceptions=True,
    )

    vector_chunks = []
    for result in per_file_results:
        if isinstance(result, list):
            vector_chunks.extend(result)

    # BM25 across all active files (already supports selected_files filtering)
    bm25_chunks = await anyio.to_thread.run_sync(
        partial(
            bm25_search,
            query,
            user_id=user_id,
            top_k=quota_per_file * len(selected_files),
            selected_files=selected_files,
        )
    )

    merged_chunks = merge_results(vector_chunks, bm25_chunks)

    reranked_chunks = await rerank_chunks_async(
        query,
        merged_chunks,
        top_k=rerank_top_k,
    )

    expanded_chunks = await anyio.to_thread.run_sync(
        partial(expand_parent_context, reranked_chunks, window_size=1, user_id=user_id)
    )

    return expanded_chunks
