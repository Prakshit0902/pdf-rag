import os
import math
import time
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL_NAME = "gemini-embedding-2"

_client_cache = {}

def _get_client():
    try:
        loop = asyncio.get_running_loop()
        if loop not in _client_cache:
            _client_cache[loop] = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        return _client_cache[loop]
    except RuntimeError:
        return genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def normalize_vector(vector: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(x * x for x in vector))
    if magnitude > 0:
        return [x / magnitude for x in vector]
    return vector


def get_embedding(text: str, task_type: str = "RETRIEVAL_QUERY"):
    client = _get_client()
    result = client.models.embed_content(
        model=MODEL_NAME,
        contents=text,
        config=types.EmbedContentConfig(
            task_type=task_type
        )
    )
    return normalize_vector(result.embeddings[0].values)


def get_embeddings_batch(
    texts: list[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
    title: str = None,
    retries: int = 3,
    delay: float = 2.0
) -> list[list[float]]:
    # Wrap each text in a Content object to prevent the SDK from
    # concatenating consecutive strings into a single Content's Parts.
    content_list = [types.Content(parts=[types.Part.from_text(text=t)]) for t in texts]
    client = _get_client()
    for attempt in range(retries):
        try:
            result = client.models.embed_content(
                model=MODEL_NAME,
                contents=content_list,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    title=title
                )
            )
            return [normalize_vector(e.values) for e in result.embeddings]
        except Exception as e:
            if attempt == retries - 1:
                raise e
            print(f"[embedder] Batch embedding attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2


async def get_embedding_async(text: str, task_type: str = "RETRIEVAL_QUERY"):
    client = _get_client()
    result = await client.aio.models.embed_content(
        model=MODEL_NAME,
        contents=text,
        config=types.EmbedContentConfig(
            task_type=task_type
        )
    )
    return normalize_vector(result.embeddings[0].values)


async def get_embeddings_batch_async(
    texts: list[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
    title: str = None,
    retries: int = 3,
    delay: float = 2.0
) -> list[list[float]]:
    content_list = [types.Content(parts=[types.Part.from_text(text=t)]) for t in texts]
    client = _get_client()
    for attempt in range(retries):
        try:
            result = await client.aio.models.embed_content(
                model=MODEL_NAME,
                contents=content_list,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    title=title
                )
            )
            return [normalize_vector(e.values) for e in result.embeddings]
        except Exception as e:
            if attempt == retries - 1:
                raise e
            print(f"[embedder] Async batch embedding attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            await asyncio.sleep(delay)
            delay *= 2

