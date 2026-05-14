from sentence_transformers import SentenceTransformer


# VERY strong retrieval model
MODEL_NAME = "BAAI/bge-m3"


model = SentenceTransformer(MODEL_NAME)


def get_embedding(text: str):

    embedding = model.encode(
        text,
        normalize_embeddings=True
    )

    return embedding.tolist()