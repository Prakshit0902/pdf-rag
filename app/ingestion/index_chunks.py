import os
import json

from app.embeddings.embedder import get_embedding

from app.vectorstore.store import (
    create_collection,
    store_chunks
)


PARSED_DIR = "data/parsed"


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

    print(f"Loaded {len(chunks)} chunks")

    embeddings = []

    for index, chunk in enumerate(chunks):

        print(f"Embedding {index+1}/{len(chunks)}")

        embedding = get_embedding(
            chunk["text"]
        )

        embeddings.append(embedding)

    vector_size = len(embeddings[0])

    create_collection(vector_size)

    store_chunks(chunks, embeddings)

    print("Indexing complete")


if __name__ == "__main__":
    main()