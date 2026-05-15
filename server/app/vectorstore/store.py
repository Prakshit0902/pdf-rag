from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

from app.vectorstore.qdrant_client import client


COLLECTION_NAME = "pdf_rag"


def create_collection(vector_size: int):

    collections = client.get_collections().collections

    exists = any(
        c.name == COLLECTION_NAME
        for c in collections
    )

    if exists:
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,

        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE
        )
    )

    print("Qdrant collection created")


def store_chunks(chunks, embeddings):

    points = []

    for chunk, embedding in zip(chunks, embeddings):

        point = PointStruct(
            id=chunk["id"],

            vector=embedding,

            payload=chunk
        )

        points.append(point)

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    print(f"Stored {len(points)} chunks")