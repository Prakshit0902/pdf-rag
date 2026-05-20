import os
import json

from app.embeddings.embedder import get_embeddings_batch

from app.vectorstore.store import (
    create_collection,
    store_chunks
)

BATCH_SIZE = 100
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PARSED_DIR = os.path.join(BASE_DIR, "data", "parsed")


def load_all_chunks():

    all_chunks = []

    json_files = [
        f for f in os.listdir(PARSED_DIR)
        if f.endswith(".json")
    ]

    for file in json_files:

        path = os.path.join(PARSED_DIR, file)

        with open(path, "r", encoding="utf-8") as f:

            chunks = json.load(f)

            all_chunks.extend(chunks)

    return all_chunks


def main():

    chunks = load_all_chunks()
    
    for chunk in chunks:

        token_count = len(
            chunk["text"].split()
        )

        print(
            f"Chunk size: {token_count} words"
        )

    print(f"Loaded {len(chunks)} chunks")

    texts = [chunk["text"] for chunk in chunks]
    embeddings = []

    total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"Embedding batch {batch_num}/{total_batches} ({len(batch)} texts)")
        batch_embeddings = get_embeddings_batch(batch)
        embeddings.extend(batch_embeddings)

    vector_size = len(embeddings[0])

    create_collection(vector_size)

    store_chunks(chunks, embeddings)

    print("Indexing complete")


def index_single_file(json_path: str) -> None:
    """Index a single parsed JSON file to vector store."""
    with open(json_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Indexing {len(chunks)} chunks from {json_path}")

    texts = [chunk["text"] for chunk in chunks]
    embeddings = []

    total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"  Embedding batch {batch_num}/{total_batches} ({len(batch)} texts)")
        batch_embeddings = get_embeddings_batch(batch)
        embeddings.extend(batch_embeddings)

    if embeddings:
        vector_size = len(embeddings[0])
        create_collection(vector_size)
        store_chunks(chunks, embeddings)

    print(f"Indexed {len(chunks)} chunks")


if __name__ == "__main__":
    main()