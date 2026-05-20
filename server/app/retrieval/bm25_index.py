import os
import json

from rank_bm25 import BM25Okapi


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PARSED_DIR = os.path.join(BASE_DIR, "data", "parsed")


all_chunks = []
tokenized_chunks = []


def load_chunks():

    global all_chunks
    global tokenized_chunks
    # If the parsed data directory doesn't exist yet (e.g. fresh deploy),
    # don't raise — leave the index empty and allow the app to start.
    if not os.path.isdir(PARSED_DIR):
        return

    json_files = [
        f for f in os.listdir(PARSED_DIR)
        if f.endswith(".json")
    ]

    for file in json_files:

        path = os.path.join(PARSED_DIR, file)

        with open(path, "r", encoding="utf-8") as f:

            chunks = json.load(f)

            all_chunks.extend(chunks)

    tokenized_chunks = [
        chunk["text"].lower().split()
        for chunk in all_chunks
    ]


load_chunks()

bm25 = BM25Okapi(tokenized_chunks) if tokenized_chunks else None


def bm25_search(
    query: str,
    top_k: int = 5
):
    if not bm25:
        return []

    tokenized_query = query.lower().split()

    scores = bm25.get_scores(
        tokenized_query
    )

    scored_results = list(
        zip(all_chunks, scores)
    )

    scored_results.sort(
        key=lambda x: x[1],
        reverse=True
    )

    results = []

    for chunk, score in scored_results[:top_k]:

        chunk["bm25_score"] = float(score)

        results.append(chunk)

    return results