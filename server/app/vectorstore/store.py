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
        try:
            info = client.get_collection(COLLECTION_NAME)
            vectors_config = info.config.params.vectors
            
            current_distance = None
            current_size = None
            
            if hasattr(vectors_config, "distance"):
                current_distance = vectors_config.distance
                current_size = vectors_config.size
            elif isinstance(vectors_config, dict) and "distance" in vectors_config:
                current_distance = vectors_config["distance"]
                current_size = vectors_config["size"]
            
            if current_distance == Distance.DOT and current_size == vector_size:
                return
                
            print(f"Collection '{COLLECTION_NAME}' exists but has config mismatch (distance={current_distance}, size={current_size}). Recreating...")
            client.delete_collection(COLLECTION_NAME)
        except Exception as e:
            print(f"Error checking collection config, forcing recreate: {e}")
            try:
                client.delete_collection(COLLECTION_NAME)
            except Exception:
                pass

    client.create_collection(
        collection_name=COLLECTION_NAME,

        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.DOT
        )
    )

    print(f"Qdrant collection '{COLLECTION_NAME}' created with Distance.DOT")



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