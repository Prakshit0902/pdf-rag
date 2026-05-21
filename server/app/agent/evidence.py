import json
from concurrent.futures import ThreadPoolExecutor

from app.retrieval.retrieve import (
    retrieve_chunks
)


def gather_evidence(
    queries
):
    if not queries:
        return []

    all_chunks = []
    seen = set()

    with ThreadPoolExecutor(max_workers=min(len(queries), 8)) as executor:
        results = executor.map(retrieve_chunks, queries)

    for chunks in results:
        for chunk in chunks:
            if chunk["id"] in seen:
                continue

            seen.add(chunk["id"])
            all_chunks.append(chunk)

    return all_chunks