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

os.makedirs(PARSED_DIR, exist_ok=True)


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

    # Group chunks by source_file to pass the correct document title
    from collections import defaultdict
    grouped_chunks = defaultdict(list)
    for chunk in chunks:
        grouped_chunks[chunk.get("source_file", "unknown_document.pdf")].append(chunk)

    embeddings_dict = {}
    for source_file, file_chunks in grouped_chunks.items():
        print(f"Embedding {len(file_chunks)} chunks for document: {source_file}")
        texts = [c["text"] for c in file_chunks]
        file_embeddings = []
        total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            print(f"  Batch {batch_num}/{total_batches} ({len(batch)} texts)")
            batch_embeddings = get_embeddings_batch(batch, title=source_file)
            file_embeddings.extend(batch_embeddings)
        embeddings_dict[source_file] = file_embeddings

    # Reconstruct ordered lists for collection creation and storage
    ordered_chunks = []
    ordered_embeddings = []
    for source_file, file_chunks in grouped_chunks.items():
        ordered_chunks.extend(file_chunks)
        ordered_embeddings.extend(embeddings_dict[source_file])

    if ordered_embeddings:
        vector_size = len(ordered_embeddings[0])
        create_collection(vector_size)
        store_chunks(ordered_chunks, ordered_embeddings)

    print("Indexing complete")

    # Reload BM25 index to make newly indexed file chunks searchable immediately
    try:
        from app.retrieval.bm25_index import reload_index
        reload_index()
    except Exception as e:
        pass


def index_single_file(json_path: str) -> None:
    """Index a single parsed JSON file to vector store."""
    with open(json_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Indexing {len(chunks)} chunks from {json_path}")

    # Extract title from the source file metadata or fallback to JSON filename
    title = chunks[0].get("source_file") if chunks else os.path.basename(json_path).replace(".json", ".pdf")

    texts = [chunk["text"] for chunk in chunks]
    embeddings = []

    total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"  Embedding batch {batch_num}/{total_batches} ({len(batch)} texts)")
        batch_embeddings = get_embeddings_batch(batch, title=title)
        embeddings.extend(batch_embeddings)

    if embeddings:
        vector_size = len(embeddings[0])
        create_collection(vector_size)
        store_chunks(chunks, embeddings)

    print(f"Indexed {len(chunks)} chunks")

    # Reload BM25 index to make newly indexed file chunks searchable immediately
    try:
        from app.retrieval.bm25_index import reload_index
        reload_index()
    except Exception as e:
        print(f"Failed to reload BM25 index: {e}")


if __name__ == "__main__":
    main()