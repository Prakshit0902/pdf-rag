"""
Tier-Specific Handlers — Phase C of Multi-Tier RAG.

Three async generators that handle non-chunk queries:
  - handle_document_summary:  Loads pre-computed summaries from metadata,
                              falls back to on-demand generation from parsed JSON.
  - handle_aggregation:       Tries structured tables from metadata first,
                              then map-reduces over all parsed chunks.
  - handle_comparison:        Loads summaries to identify themes, then retrieves
                              targeted chunks per theme from existing retrieval.

Each handler is an async generator yielding string tokens, matching the
stream_answer_async interface so stream_ask.py can yield directly from them.
"""

import os
import json
import asyncio
from typing import AsyncIterator, Optional

from app.llm.gemini import generate_answer_async, stream_answer_async
from app.qa.ask import build_context


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
METADATA_DIR = os.path.join(BASE_DIR, "data", "metadata")
PARSED_DIR = os.path.join(BASE_DIR, "data", "parsed")


# ── Helpers ──────────────────────────────────────────────────────────

def load_metadata(filename: str, user_id: str) -> Optional[dict]:
    """Load pre-generated metadata JSON from disk."""
    stem = filename.replace(".pdf", "")
    path = os.path.join(METADATA_DIR, user_id, f"{stem}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[handlers] Error loading metadata for {filename}: {e}")
        return None


def load_all_parsed_chunks(filename: str, user_id: str) -> list:
    """Load all parsed chunks from disk JSON (bypasses Qdrant entirely)."""
    stem = filename.replace(".pdf", "")
    path = os.path.join(PARSED_DIR, user_id, f"{stem}.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[handlers] Error loading parsed chunks for {filename}: {e}")
        return []


def _resolve_active_files(
    selected_files: list,
    user_id: str,
) -> list:
    """
    If selected_files is empty, discover all parsed JSON files for the user
    and return their original filenames. This ensures all uploaded documents
    are included even when no explicit selection was made.
    """
    if selected_files:
        return selected_files

    user_parsed_dir = os.path.join(PARSED_DIR, user_id)
    if not os.path.isdir(user_parsed_dir):
        return []

    return [
        f.replace(".json", ".pdf")
        for f in os.listdir(user_parsed_dir)
        if f.endswith(".json")
    ]


# ── Tier 1: Document Summary ────────────────────────────────────────

async def handle_document_summary(
    question: str,
    active_files: list,
    user_id: str,
) -> AsyncIterator[str]:
    """
    Load pre-computed summaries from metadata.
    Falls back to on-demand single-pass summarization from parsed JSON.
    """
    files = _resolve_active_files(active_files, user_id)
    if not files:
        yield "No documents are available to summarize."
        return

    contexts = []
    needs_fallback = []

    # Try loading pre-computed summaries
    for filename in files:
        meta = load_metadata(filename, user_id)
        if meta and meta.get("summary"):
            contexts.append(f"--- Document: {filename} ---\n{meta['summary']}")
        else:
            needs_fallback.append(filename)

    # On-demand fallback for docs without metadata yet
    if needs_fallback:
        fallback_tasks = []
        for filename in needs_fallback:
            chunks = load_all_parsed_chunks(filename, user_id)
            if not chunks:
                continue
            full_text = "\n\n".join(
                f"[Page {c.get('page', '?')}]\n{c['text']}" for c in chunks
            )[:100_000]
            fallback_tasks.append(
                (filename, generate_answer_async(
                    f"Provide a comprehensive 3-paragraph summary of this document "
                    f"titled '{filename}':\n\n{full_text}"
                ))
            )

        if fallback_tasks:
            results = await asyncio.gather(
                *[t for _, t in fallback_tasks],
                return_exceptions=True,
            )
            for (filename, _), result in zip(fallback_tasks, results):
                if isinstance(result, str) and result.strip():
                    contexts.append(
                        f"--- Document: {filename} (generated on-demand) ---\n{result}"
                    )

    if not contexts:
        yield "Could not generate summaries for the active documents."
        return

    # Synthesize from all collected summaries
    if len(files) > 1:
        intro = "Based on the following document summaries, provide a synthesized answer."
    else:
        intro = "Based on this document summary, answer the user's question."

    prompt = f"""{intro}

{chr(10).join(contexts)}

User question: {question}

Answer in clean markdown format. At the end, list sources as:
**Sources:** [filename, Summary]"""

    async for token in stream_answer_async(prompt):
        yield token


# ── Tier 3: Aggregation / Computation ────────────────────────────────

async def handle_aggregation(
    question: str,
    active_files: list,
    user_id: str,
) -> AsyncIterator[str]:
    """
    For queries requiring mathematical calculation, counting, or totaling.

    Strategy 1: Use pre-extracted structured tables from metadata (fastest).
    Strategy 2: Map-reduce over all parsed chunks (always correct).
    """
    files = _resolve_active_files(active_files, user_id)
    if not files:
        yield "No documents are available to analyze."
        return

    yield (
        "*Note: This answer required reading the full document text, "
        "not just relevant sections.*\n\n"
    )

    # ── Strategy 1: Try structured tables from metadata ──────────────
    for filename in files:
        meta = load_metadata(filename, user_id)
        if meta and meta.get("has_structured_data") and meta.get("tables"):
            table_prompt = (
                f"You have access to structured tables extracted from '{filename}':\n\n"
                f"{json.dumps(meta['tables'], indent=2)}\n\n"
                f"User question: {question}\n\n"
                f"If the answer can be fully computed from these tables, "
                f"provide a step-by-step calculation with the final result.\n"
                f"If the tables are insufficient, respond with exactly: NEEDS_FULL_SCAN"
            )
            try:
                table_resp = await generate_answer_async(table_prompt)
                if "NEEDS_FULL_SCAN" not in table_resp:
                    # Stream the successful table-based answer
                    async for token in stream_answer_async(table_prompt):
                        yield token
                    return
            except Exception:
                pass  # Fall through to map-reduce

    # ── Strategy 2: Map-reduce over all chunks from disk ─────────────
    all_chunks = []
    for filename in files:
        all_chunks.extend(load_all_parsed_chunks(filename, user_id))

    if not all_chunks:
        yield "Could not load document content for analysis."
        return

    # MAP: Extract relevant data from batches of 10 chunks
    BATCH_SIZE = 10
    map_tasks = []
    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[i:i + BATCH_SIZE]
        batch_text = "\n\n".join(
            f"[{c.get('source_file', '?')}, page {c.get('page', '?')}]\n{c['text']}"
            for c in batch
        )
        map_tasks.append(generate_answer_async(
            f"Extract all numerical values, dates, categories, and items "
            f"relevant to this question: '{question}'\n\n"
            f"From these document chunks:\n{batch_text}\n\n"
            f"Return a structured list. If nothing relevant, say 'No relevant data.'"
        ))

    map_results = await asyncio.gather(*map_tasks, return_exceptions=True)
    relevant_parts = [
        r for r in map_results
        if isinstance(r, str) and "No relevant data" not in r and r.strip()
    ]

    if not relevant_parts:
        yield "Could not find the data needed to answer this question in the active documents."
        return

    # REDUCE: Final synthesis
    reduce_prompt = (
        f"Based on the following extracted data from the documents, "
        f"answer this question: '{question}'\n\n"
        f"Extracted data:\n"
        + "\n".join(f"- {p}" for p in relevant_parts)
        + "\n\nProvide the final answer with step-by-step reasoning. "
        f"Cite document names and page numbers where possible.\n"
        f"Format as clean markdown."
    )

    async for token in stream_answer_async(reduce_prompt):
        yield token


# ── Tier 4: Comparison ───────────────────────────────────────────────

async def handle_comparison(
    question: str,
    active_files: list,
    user_id: str,
    selected_files: list,
) -> AsyncIterator[str]:
    """
    Compare multiple documents by:
    1. Loading their summaries to identify comparison themes.
    2. Retrieving targeted chunks per theme from each document.
    3. Synthesizing a structured comparison.
    """
    files = _resolve_active_files(active_files, user_id)
    if len(files) < 2:
        yield "At least 2 documents are needed for comparison. Please select multiple files."
        return

    # Load summaries for theme identification
    summaries = []
    for filename in files:
        meta = load_metadata(filename, user_id)
        summary_text = ""
        if meta and meta.get("summary"):
            summary_text = meta["summary"][:500]
        else:
            # Fallback: use first few chunks as context
            chunks = load_all_parsed_chunks(filename, user_id)
            if chunks:
                summary_text = " ".join(c["text"][:200] for c in chunks[:3])
        summaries.append(f"Document '{filename}': {summary_text}")

    # Identify comparison themes
    theme_prompt = (
        f"Based on these document summaries:\n"
        + "\n".join(summaries)
        + f"\n\nQuestion: {question}\n\n"
        f"Identify 3 comparison dimensions/themes relevant to this question.\n"
        f"Return as a JSON array of strings. Respond ONLY with valid JSON."
    )

    try:
        themes_raw = await generate_answer_async(theme_prompt)
        raw = themes_raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        themes = json.loads(raw)
        if not isinstance(themes, list):
            themes = [question]
    except Exception:
        themes = [question]

    # Retrieve targeted chunks per theme using existing pipeline
    from app.retrieval.retrieve import retrieve_chunks_async

    all_evidence = []
    retrieval_tasks = [
        retrieve_chunks_async(
            theme,
            user_id=user_id,
            selected_files=selected_files or files,
            rerank_top_k=4,
        )
        for theme in themes[:3]
    ]

    theme_results = await asyncio.gather(*retrieval_tasks, return_exceptions=True)
    for result in theme_results:
        if isinstance(result, list):
            all_evidence.extend(result)

    # Deduplicate by chunk ID
    seen = set()
    unique_evidence = []
    for c in all_evidence:
        cid = c.get("id")
        if cid and cid not in seen:
            seen.add(cid)
            unique_evidence.append(c)

    context = build_context(unique_evidence) if unique_evidence else "No evidence retrieved."

    comparison_prompt = f"""You are a document comparison assistant.
Compare the documents on these dimensions: {', '.join(themes[:3])}.

Evidence from documents:
{context}

User question: {question}

Structure your answer as a clear comparison with sections per dimension.
Use markdown formatting. Cite sources as: [filename, page X]"""

    async for token in stream_answer_async(comparison_prompt):
        yield token
