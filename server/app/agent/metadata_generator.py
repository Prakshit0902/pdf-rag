"""
Document Metadata Generator — Phase A of Multi-Tier RAG.

Generates structured metadata (summary, tables, key entities) for each
uploaded PDF using gemini-3.5-flash (large context window, free tier).

Metadata is stored on disk at:
    data/metadata/{user_id}/{filename_stem}.json

This module is called asynchronously in a background thread after
chunk indexing completes, so it never blocks upload job completion.
"""

import os
import json
import asyncio
from datetime import datetime

from google.genai import types

# Re-use the same genai client instance from the shared module
from app.llm.gemini import client


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
METADATA_DIR = os.path.join(BASE_DIR, "data", "metadata")

# Use the large-context model for metadata extraction
METADATA_MODEL = "gemini-3.5-flash"
# Cap input to ~300K chars (~75K tokens) — well within 1M token limit
MAX_TEXT_CHARS = 300_000


async def _generate_summary(text: str, filename: str) -> str:
    """Generate a comprehensive multi-paragraph document summary."""
    prompt = (
        f"You are a document analyst. Provide a comprehensive 3-paragraph summary "
        f"of the following document titled '{filename}'.\n\n"
        f"Include:\n"
        f"- Main topic and purpose of the document\n"
        f"- Key findings, data points, or arguments\n"
        f"- Methodology, structure, and conclusions (if applicable)\n\n"
        f"DOCUMENT TEXT:\n{text}"
    )

    try:
        response = await client.aio.models.generate_content(
            model=METADATA_MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=4096,
            ),
        )
        return response.text or ""
    except Exception as e:
        print(f"[metadata] Summary generation failed for {filename}: {e}")
        return ""


async def _extract_tables(text: str) -> list:
    """Extract all tabular data from the document as structured JSON."""
    prompt = (
        "Extract ALL tables from this document. For each table, provide:\n"
        '- "page": the page number where the table appears (or "unknown")\n'
        '- "title": a short description of what the table contains\n'
        '- "headers": list of column header strings\n'
        '- "rows": list of row arrays, each containing cell values as strings\n\n'
        "Return a JSON array of table objects. If there are NO tables, return [].\n"
        "Respond ONLY with valid JSON, no markdown fences.\n\n"
        f"DOCUMENT TEXT:\n{text}"
    )

    try:
        response = await client.aio.models.generate_content(
            model=METADATA_MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=8192,
                response_mime_type="application/json",
            ),
        )

        raw = (response.text or "[]").strip()
        # Strip markdown fences if the model wraps output
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return json.loads(raw)
    except (json.JSONDecodeError, Exception) as e:
        print(f"[metadata] Table extraction failed: {e}")
        return []


async def _extract_entities(text: str) -> list:
    """Extract the most important entities, metrics, and topics."""
    prompt = (
        "List the 15 most important entities, metrics, numerical values, "
        "and key topics mentioned in this document.\n\n"
        "Return a JSON array of strings. Each string should be a concise "
        "entity or topic name (e.g., 'Amazon SDE-1', 'LRU Cache', '$45,000 revenue').\n"
        "Respond ONLY with valid JSON, no markdown fences.\n\n"
        f"DOCUMENT TEXT:\n{text}"
    )

    try:
        response = await client.aio.models.generate_content(
            model=METADATA_MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=2048,
                response_mime_type="application/json",
            ),
        )

        raw = (response.text or "[]").strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return json.loads(raw)
    except (json.JSONDecodeError, Exception) as e:
        print(f"[metadata] Entity extraction failed: {e}")
        return []


async def generate_document_metadata(
    chunks: list,
    filename: str,
    user_id: str,
) -> dict:
    """
    Generate all metadata artifacts for a document concurrently.

    Args:
        chunks: List of parsed chunk dicts (from the parsed JSON file).
        filename: Original PDF filename (e.g. "report.pdf").
        user_id: Clerk tenant ID.

    Returns:
        The metadata dict that was saved to disk.
    """
    # Build the full document text with page markers
    full_text = "\n\n".join(
        f"[Page {c.get('page', '?')}]\n{c['text']}" for c in chunks
    )
    truncated_text = full_text[:MAX_TEXT_CHARS]

    # Run all three extractions concurrently — if one fails, others still proceed
    summary, tables, entities = await asyncio.gather(
        _generate_summary(truncated_text, filename),
        _extract_tables(truncated_text),
        _extract_entities(truncated_text),
        return_exceptions=False,
    )

    # Handle gather exceptions gracefully
    if isinstance(summary, BaseException):
        print(f"[metadata] Summary task exception: {summary}")
        summary = ""
    if isinstance(tables, BaseException):
        print(f"[metadata] Tables task exception: {tables}")
        tables = []
    if isinstance(entities, BaseException):
        print(f"[metadata] Entities task exception: {entities}")
        entities = []

    metadata = {
        "filename": filename,
        "user_id": user_id,
        "page_count": len(set(str(c.get("page", "")) for c in chunks)),
        "chunk_count": len(chunks),
        "summary": summary,
        "tables": tables,
        "has_structured_data": isinstance(tables, list) and len(tables) > 0,
        "key_entities": entities,
        "generated_at": datetime.utcnow().isoformat(),
    }

    return metadata


async def generate_and_save_metadata(
    chunks: list,
    filename: str,
    user_id: str,
) -> None:
    """
    Generate metadata and persist to disk.
    Called from a background thread in upload.py.
    """
    try:
        metadata = await generate_document_metadata(chunks, filename, user_id)

        # Ensure tenant-scoped directory exists
        user_metadata_dir = os.path.join(METADATA_DIR, user_id)
        os.makedirs(user_metadata_dir, exist_ok=True)

        filename_stem = os.path.splitext(filename)[0]
        output_path = os.path.join(user_metadata_dir, f"{filename_stem}.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"[metadata] Saved metadata for '{filename}' → {output_path}")
    except Exception as e:
        print(f"[metadata] Failed to generate/save metadata for '{filename}': {e}")
