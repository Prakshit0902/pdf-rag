import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL_NAME = "gemini-embedding-2"

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def get_embedding(text: str, task_type: str = "RETRIEVAL_QUERY"):
    result = client.models.embed_content(
        model=MODEL_NAME,
        contents=text,
        config=types.EmbedContentConfig(
            task_type=task_type
        )
    )
    return result.embeddings[0].values


def get_embeddings_batch(
    texts: list[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
    title: str = None
) -> list[list[float]]:
    # Wrap each text in a Content object to prevent the SDK from
    # concatenating consecutive strings into a single Content's Parts.
    content_list = [types.Content(parts=[types.Part.from_text(text=t)]) for t in texts]
    result = client.models.embed_content(
        model=MODEL_NAME,
        contents=content_list,
        config=types.EmbedContentConfig(
            task_type=task_type,
            title=title
        )
    )
    return [e.values for e in result.embeddings]