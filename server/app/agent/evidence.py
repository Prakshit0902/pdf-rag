import json

from app.retrieval.retrieve import (
    retrieve_chunks
)


def gather_evidence(
    queries
):

    all_chunks = []

    seen = set()

    for query in queries:

        chunks = retrieve_chunks(
            query
        )

        for chunk in chunks:

            if chunk["id"] in seen:
                continue

            seen.add(chunk["id"])

            all_chunks.append(chunk)

    return all_chunks