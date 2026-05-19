import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

MODEL_NAME = "gemini-embedding-2"

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def get_embedding(text: str):
    result = client.models.embed_content(
        model=MODEL_NAME,
        contents=text,
    )
    return result.embeddings[0].values


def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    result = client.models.embed_content(
        model=MODEL_NAME,
        contents=texts,
    )
    return [e.values for e in result.embeddings]