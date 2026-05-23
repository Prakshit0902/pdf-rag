from functools import partial
import json
from concurrent.futures import ThreadPoolExecutor

from app.retrieval.retrieve import (
    retrieve_chunks
)


def gather_evidence(
    queries,
    user_id: str = "default_tenant"
):
    if not queries:
        return []

    all_chunks = []
    seen = set()

    retrieve_func = partial(retrieve_chunks, user_id=user_id)

    with ThreadPoolExecutor(max_workers=min(len(queries), 8)) as executor:
        results = executor.map(retrieve_func, queries)

    for chunks in results:
        for chunk in chunks:
            if chunk["id"] in seen:
                continue

            seen.add(chunk["id"])
            all_chunks.append(chunk)

    return all_chunks