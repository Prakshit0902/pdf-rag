import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()


client = InferenceClient(
    provider="hf-inference",
    api_key=os.environ.get("HF_TOKEN"),
)

MODEL_NAME = "BAAI/bge-m3"


def get_embedding(text: str):

    embedding = client.feature_extraction(
        text,
        model=MODEL_NAME
    )

    # Normalize the embedding
    magnitude = sum(x**2 for x in embedding) ** 0.5

    if magnitude > 0:
        embedding = [x / magnitude for x in embedding]

    return embedding