import os
import json


PARSED_DIR = "data/parsed"


document_cache = {}


def load_document(
    source_file
):

    if source_file in document_cache:
        return document_cache[source_file]

    path = os.path.join(
        PARSED_DIR,
        source_file.replace(".pdf", ".json")
    )

    with open(path, "r", encoding="utf-8") as f:

        chunks = json.load(f)

    document_cache[source_file] = chunks

    return chunks


def expand_parent_context(
    retrieved_chunks,
    window_size: int = 1
):

    expanded_chunks = []

    seen = set()

    for chunk in retrieved_chunks:

        source_file = chunk["source_file"]

        chunk_id = chunk.get("id")

        parent_index = chunk.get(
            "parent_chunk_index",
            0
        )

        # Store all scores from retrieved chunk before we lose reference
        scores_to_preserve = {}

        if "vector_score" in chunk:
            scores_to_preserve["vector_score"] = chunk.get("vector_score", 0)

        if "bm25_score" in chunk:
            scores_to_preserve["bm25_score"] = chunk.get("bm25_score", 0)

        if "rerank_score" in chunk:
            scores_to_preserve["rerank_score"] = chunk.get("rerank_score", 0)

        all_chunks = load_document(
            source_file
        )

        start = max(
            0,
            parent_index - window_size
        )

        end = min(
            len(all_chunks),
            parent_index + window_size + 1
        )

        for i in range(start, end):

            candidate = all_chunks[i]

            if candidate["id"] in seen:
                continue

            seen.add(candidate["id"])

            # Copy candidate and preserve scores if IDs match
            expanded_chunk = candidate.copy()

            # Match by ID and copy scores
            if candidate["id"] == chunk_id and scores_to_preserve:
                expanded_chunk.update(scores_to_preserve)

            expanded_chunks.append(expanded_chunk)

    return expanded_chunks