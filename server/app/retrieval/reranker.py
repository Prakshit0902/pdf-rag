import os
import requests
import httpx
from dotenv import load_dotenv

load_dotenv()

JINA_API_KEY = os.getenv("JINA_API_KEY")
MODEL_NAME = "jina-reranker-v2-base-multilingual"


def rerank_chunks(
    query: str,
    chunks: list,
    top_k: int = 5
):
    documents = [chunk["text"] for chunk in chunks]

    response = requests.post(
        "https://api.jina.ai/v1/rerank",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {JINA_API_KEY}",
        },
        json={
            "model": MODEL_NAME,
            "query": query,
            "documents": documents,
            "return_documents": False,
        },
    )
    response.raise_for_status()
    results = response.json()["results"]

    scored_chunks = []
    for result in results:
        idx = result["index"]
        chunk = dict(chunks[idx])
        chunk["rerank_score"] = result["relevance_score"]
        scored_chunks.append(chunk)

    scored_chunks.sort(
        key=lambda x: x["rerank_score"],
        reverse=True
    )

    return scored_chunks[:top_k]


async def rerank_chunks_async(
    query: str,
    chunks: list,
    top_k: int = 5
):
    if not chunks:
        return []

    documents = [chunk["text"] for chunk in chunks]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.jina.ai/v1/rerank",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {JINA_API_KEY}",
            },
            json={
                "model": MODEL_NAME,
                "query": query,
                "documents": documents,
                "return_documents": False,
            },
            timeout=30.0,
        )
    response.raise_for_status()
    results = response.json()["results"]

    scored_chunks = []
    for result in results:
        idx = result["index"]
        chunk = dict(chunks[idx])
        chunk["rerank_score"] = result["relevance_score"]
        scored_chunks.append(chunk)

    scored_chunks.sort(
        key=lambda x: x["rerank_score"],
        reverse=True
    )

    return scored_chunks[:top_k]

