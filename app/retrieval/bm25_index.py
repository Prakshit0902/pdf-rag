import os
import json

from rank_bm25 import BM25Okapi


PARSED_DIR = "data/parsed"


all_chunks = []
tokenized_chunks = []


def load_chunks():

    global all_chunks
    global tokenized_chunks

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

bm25 = BM25Okapi(tokenized_chunks)


def bm25_search(
    query: str,
    top_k: int = 5
):

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