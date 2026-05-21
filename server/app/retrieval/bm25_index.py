import os
import json
import threading

from rank_bm25 import BM25Okapi


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PARSED_DIR = os.path.join(BASE_DIR, "data", "parsed")

os.makedirs(PARSED_DIR, exist_ok=True)

# Lock to synchronize swaps and captures of global variables
_lock = threading.Lock()

all_chunks = []
tokenized_chunks = []


def _load_chunks_internal():
    """Internal helper to load all chunks from disk without modifying globals."""
    if not os.path.isdir(PARSED_DIR):
        return [], []

    new_chunks = []
    json_files = [
        f for f in os.listdir(PARSED_DIR)
        if f.endswith(".json")
    ]

    for file in json_files:
        path = os.path.join(PARSED_DIR, file)
        try:
            with open(path, "r", encoding="utf-8") as f:
                chunks = json.load(f)
                new_chunks.extend(chunks)
        except Exception as e:
            print(f"Error loading parsed file {path}: {e}")

    new_tokenized_chunks = [
        chunk["text"].lower().split()
        for chunk in new_chunks
    ]
    return new_chunks, new_tokenized_chunks


def load_chunks():
    """Legacy helper function to populate globals. Kept for backwards compatibility."""
    global all_chunks
    global tokenized_chunks
    all_chunks, tokenized_chunks = _load_chunks_internal()


# Initial load at module import time
all_chunks, tokenized_chunks = _load_chunks_internal()
bm25 = BM25Okapi(tokenized_chunks) if tokenized_chunks else None


def reload_index():
    """Reload all chunks from parsed JSON files and rebuild BM25 index thread-safely."""
    global all_chunks
    global tokenized_chunks
    global bm25

    # Run slow IO and tokenization outside the lock
    new_chunks, new_tokenized_chunks = _load_chunks_internal()
    new_bm25 = BM25Okapi(new_tokenized_chunks) if new_tokenized_chunks else None

    # Swap references atomically under lock
    with _lock:
        all_chunks = new_chunks
        tokenized_chunks = new_tokenized_chunks
        bm25 = new_bm25

    print(f"BM25 index reloaded thread-safely with {len(all_chunks)} chunks.")


def bm25_search(
    query: str,
    top_k: int = 5
):
    # Retrieve current global references atomically under lock
    with _lock:
        current_bm25 = bm25
        current_chunks = all_chunks

    if not current_bm25:
        return []

    tokenized_query = query.lower().split()

    # Perform scores calculation lock-free on captured references
    scores = current_bm25.get_scores(
        tokenized_query
    )

    scored_results = list(
        zip(current_chunks, scores)
    )

    scored_results.sort(
        key=lambda x: x[1],
        reverse=True
    )

    results = []

    for chunk, score in scored_results[:top_k]:
        # Copy the chunk dictionary to prevent cross-request mutation of global chunks
        chunk_copy = chunk.copy()
        chunk_copy["bm25_score"] = float(score)
        results.append(chunk_copy)

    return results