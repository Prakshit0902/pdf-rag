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

        parent_index = chunk[
            "parent_chunk_index"
        ]

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

            expanded_chunks.append(candidate)

    return expanded_chunks