from typing import Optional, List
import os
import json
import threading

from rank_bm25 import BM25Okapi


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PARSED_DIR = os.path.join(BASE_DIR, "data", "parsed")

os.makedirs(PARSED_DIR, exist_ok=True)

# Lock to synchronize swaps and captures of user indexes
_lock = threading.Lock()

# Dictionary to hold user-specific indexes: {user_id: (BM25Okapi, all_chunks)}
_user_indexes = {}


def _load_chunks_internal_user(user_id: str):
    """Internal helper to load user-specific chunks from disk."""
    user_parsed_dir = os.path.join(BASE_DIR, "data", "parsed", user_id)
    if not os.path.isdir(user_parsed_dir):
        return [], []

    new_chunks = []
    json_files = [
        f for f in os.listdir(user_parsed_dir)
        if f.endswith(".json")
    ]

    for file in json_files:
        path = os.path.join(user_parsed_dir, file)
        try:
            with open(path, "r", encoding="utf-8") as f:
                chunks = json.load(f)
                new_chunks.extend(chunks)
        except Exception as e:
            print(f"Error loading parsed file {path} for user {user_id}: {e}")

    new_tokenized_chunks = [
        chunk["text"].lower().split()
        for chunk in new_chunks
    ]
    return new_chunks, new_tokenized_chunks


def reload_index(user_id: str = "default_tenant"):
    """Reload all chunks from parsed JSON files and rebuild BM25 index for user thread-safely."""
    new_chunks, new_tokenized_chunks = _load_chunks_internal_user(user_id)
    new_bm25 = BM25Okapi(new_tokenized_chunks) if new_tokenized_chunks else None

    # Swap references atomically under lock
    with _lock:
        _user_indexes[user_id] = (new_bm25, new_chunks)

    print(f"BM25 index reloaded thread-safely for user '{user_id}' with {len(new_chunks)} chunks.")


def bm25_search(
    query: str,
    user_id: str = "default_tenant",
    top_k: int = 5,
    selected_files: Optional[List[str]] = None
):
    # Check if index needs to be lazy-loaded
    needs_reload = False
    with _lock:
        if user_id not in _user_indexes:
            needs_reload = True

    if needs_reload:
        reload_index(user_id)

    # Retrieve current user references atomically under lock
    with _lock:
        current_bm25, current_chunks = _user_indexes.get(user_id, (None, []))

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

    if selected_files:
        selected_files_set = set(selected_files)
        scored_results = [
            (chunk, score) for chunk, score in scored_results
            if chunk.get("source_file") in selected_files_set
        ]

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