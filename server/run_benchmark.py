import os
import shutil
import uuid
import time
import json
from datetime import datetime

import functools

# ------------------------------------------------------------
# Utility: retry any callable with exponential backoff on 429s
# ------------------------------------------------------------
API_SLEEP_TIME = 0
original_perf_counter = time.perf_counter

def custom_perf_counter():
    return original_perf_counter() - API_SLEEP_TIME

time.perf_counter = custom_perf_counter


def with_rate_limit_backoff(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        global API_SLEEP_TIME
        max_retries = 8
        base_delay = 4
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                err_msg = str(e).lower()
                if "429" in err_msg or "exhausted" in err_msg or "quota" in err_msg or "rate limit" in err_msg or "503" in err_msg:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    print(f"\n    [Rate Limit] Waiting {delay}s before retry {attempt+1}/{max_retries}...")
                    time.sleep(delay)
                    API_SLEEP_TIME += delay
                else:
                    raise
    return wrapper


# -----------------------------------------------

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app.parsing.extract_images import extract_images_from_pdf
from app.parsing.render_pages import render_pdf_pages
from app.parsing.parser import parse_pdf
from app.ingestion.process_pdfs import build_chunks
from app.embeddings.embedder import get_embedding
from app.vectorstore.store import create_collection, store_chunks
from app.agent.agentic_qa import ask_agentic_question

BENCHMARK_DIR = os.path.join("app", "benchmark")
INPUT_DIR = "data/cleaned_pdfs"
PARSED_DIR = "data/parsed"
IMAGE_DIR = "data/images"
PAGE_RENDER_DIR = "data/page_renders"
RESULTS_DIR = "benchmark"

for d in [RESULTS_DIR, INPUT_DIR, PARSED_DIR, IMAGE_DIR, PAGE_RENDER_DIR]:
    os.makedirs(d, exist_ok=True)


def benchmark_pipeline(pdf_name):
    """Run full pipeline on one PDF with per-step timing."""
    pdf_path = os.path.join(INPUT_DIR, pdf_name)
    stem = pdf_name.replace(".pdf", "")
    metrics = {"filename": pdf_name, "steps": {}}

    print(f"\n{'='*60}")
    print(f"  Pipeline: {pdf_name}")
    print(f"{'='*60}")

    try:
        # Step 1 — Extract images
        print("[1/5] Extracting images...", end=" ")
        t0 = time.perf_counter()
        pdf_image_dir = os.path.join(IMAGE_DIR, stem)
        image_map = extract_images_from_pdf(pdf_path, pdf_image_dir)
        t1 = time.perf_counter()
        total_images = sum(len(v) for v in image_map.values())
        print(f"{t1-t0:.2f}s ({total_images} images)")
        metrics["steps"]["extract_images"] = {"time_s": round(t1-t0, 3), "total_images": total_images}

        # Step 2 — Render pages
        print("[2/5] Rendering pages...", end=" ")
        pdf_render_dir = os.path.join(PAGE_RENDER_DIR, stem)
        page_render_map = render_pdf_pages(pdf_path, pdf_render_dir)
        t2 = time.perf_counter()
        print(f"{t2-t1:.2f}s ({len(page_render_map)} pages)")
        metrics["steps"]["render_pages"] = {"time_s": round(t2-t1, 3), "total_pages": len(page_render_map)}

        # Step 3 — Parse PDF
        print("[3/5] Parsing PDF...", end=" ")
        documents = parse_pdf(pdf_path)
        t3 = time.perf_counter()
        print(f"{t3-t2:.2f}s ({len(documents)} blocks)")
        metrics["steps"]["parse_pdf"] = {"time_s": round(t3-t2, 3), "document_blocks": len(documents)}

        # Step 4 — Chunk + save JSON
        print("[4/5] Chunking...", end=" ")
        chunks = build_chunks(documents, pdf_name, image_map, page_render_map)
        t4 = time.perf_counter()
        print(f"{t4-t3:.2f}s ({len(chunks)} chunks)")

        output_path = os.path.join(PARSED_DIR, f"{stem}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        metrics["steps"]["chunking"] = {"time_s": round(t4-t3, 3), "total_chunks": len(chunks)}

        if not chunks:
            print("  [SKIP] No chunks to index.")
            metrics["steps"]["embedding"] = {"time_s": 0, "total_chunks": 0, "batches": 0, "per_chunk_ms": 0, "batch_details": []}
            metrics["steps"]["qdrant_upsert"] = {"time_s": 0}
            metrics["total_time_s"] = round(t4 - t0, 3)
            return metrics

        # Step 5 — Embed (local SentenceTransformer, sequential per-chunk) + store in Qdrant
        print(f"[5/5] Embedding {len(chunks)} chunks (local bge-m3)...")
        texts = [c["text"] for c in chunks]
        embeddings = []
        batch_details = []

        embed_start = time.perf_counter()
        for i, text in enumerate(texts):
            bt0 = time.perf_counter()
            emb = get_embedding(text)
            bt1 = time.perf_counter()
            embeddings.append(emb)
            bt = bt1 - bt0
            batch_details.append({"chunk_num": i + 1, "time_s": round(bt, 3)})
            if (i + 1) % 50 == 0 or i == len(texts) - 1:
                avg = sum(b["time_s"] for b in batch_details[-50:]) / min(50, len(batch_details))
                print(f"    {i+1}/{len(texts)} chunks — last {min(50, i+1)} avg {avg*1000:.1f}ms/chunk")

        embed_end = time.perf_counter()
        embed_total = embed_end - embed_start
        per_chunk_ms = embed_total / len(texts) * 1000

        metrics["steps"]["embedding"] = {
            "time_s": round(embed_total, 3),
            "total_chunks": len(texts),
            "batches": len(texts),
            "per_chunk_ms": round(per_chunk_ms, 1),
            "batch_details": batch_details,
        }
        print(f"  => Embedded {len(texts)} chunks in {embed_total:.2f}s ({per_chunk_ms:.1f}ms/chunk)")

        # Upsert to Qdrant
        print("  => Storing vectors in Qdrant...", end=" ")
        if embeddings:
            vector_size = len(embeddings[0])
            create_collection(vector_size)
            store_chunks(chunks, embeddings)
        t5 = time.perf_counter()
        upsert_time = t5 - embed_end
        metrics["steps"]["qdrant_upsert"] = {"time_s": round(upsert_time, 3)}
        print(f"{upsert_time:.2f}s")

        total_time = t5 - t0
        metrics["total_time_s"] = round(total_time, 3)
        print(f"  => Pipeline total: {total_time:.2f}s")

    except Exception as e:
        print(f"\n  [ERROR] {e}")
        metrics["error"] = str(e)

    return metrics


def parse_questions():
    questions = []
    q_file = os.path.join(BENCHMARK_DIR, "questions.md")
    if not os.path.exists(q_file):
        return [
            "What problem does the paper say poor PDF parsing causes in RAG?",
            "How many PDF parsing tools are compared?",
        ]
    with open(q_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("* "):
                questions.append(line[2:].strip())
    return questions


def run_benchmarks():
    print("=" * 60)
    print("  PDF RAG — Full Pipeline Benchmark (self-hosted)")
    print(f"  Started: {datetime.now().isoformat()}")
    print(f"  Embedding: local BAAI/bge-m3 (SentenceTransformer)")
    print("=" * 60)

    pdf_files = sorted([f for f in os.listdir(BENCHMARK_DIR) if f.endswith(".pdf")])
    if not pdf_files:
        print("No benchmark PDFs found.")
        return

    print(f"\nFound {len(pdf_files)} PDF(s): {', '.join(pdf_files)}\n")

    for pdf in pdf_files:
        shutil.copy2(os.path.join(BENCHMARK_DIR, pdf), os.path.join(INPUT_DIR, pdf))

    pipeline_results = {}
    for pdf in pdf_files:
        m = benchmark_pipeline(pdf)
        pipeline_results[pdf] = m
        rp = os.path.join(RESULTS_DIR, f"upload_pipeline_{pdf.replace('.pdf', '')}.json")
        with open(rp, "w", encoding="utf-8") as f:
            json.dump(m, f, indent=2)

    # --- Aggregate ingestion stats ---
    total_ingest = sum(m.get("total_time_s", 0) for m in pipeline_results.values())
    total_embed = sum(m.get("steps", {}).get("embedding", {}).get("time_s", 0) for m in pipeline_results.values())
    total_chunks = sum(m.get("steps", {}).get("embedding", {}).get("total_chunks", 0) for m in pipeline_results.values())

    print(f"\n{'='*60}")
    print("  INGESTION SUMMARY")
    print(f"{'='*60}")
    print(f"  {'PDF':<30} {'Chunks':<8} {'Embed(s)':<10} {'Total(s)':<10}")
    print(f"  {'-'*30} {'-'*8} {'-'*10} {'-'*10}")
    for pdf in pdf_files:
        m = pipeline_results[pdf]
        s = m.get("steps", {})
        e = s.get("embedding", {})
        c = e.get("total_chunks", 0)
        et = e.get("time_s", 0)
        tt = m.get("total_time_s", 0)
        print(f"  {pdf:<30} {c:<8} {et:<10.2f} {tt:<10.2f}")
    print(f"\n  Total chunks: {total_chunks}")
    print(f"  Total embedding time: {total_embed:.2f}s")
    print(f"  Total ingestion time: {total_ingest:.2f}s")

    # --- Run QA (with rate-limit backoff on LLM calls) ---
    print(f"\n{'='*60}")
    print("  BENCHMARK QUESTIONS")
    print(f"{'='*60}")

    agentic_with_backoff = with_rate_limit_backoff(ask_agentic_question)

    questions = parse_questions()
    qa_results = []
    for idx, q in enumerate(questions):
        print(f"\nQ{idx+1}/{len(questions)}: {q}")
        t0 = time.perf_counter()
        try:
            res = agentic_with_backoff(q)
            status = "Success" if res and "answer" in res else "Failed (no answer)"
        except Exception as e:
            status = f"Error: {e}"
        t1 = time.perf_counter()
        dur = round(t1 - t0, 2)
        qa_results.append({"question": q, "time_s": dur, "status": status})
        print(f"  Time: {dur}s | {status[:60]}")

        qp = os.path.join(RESULTS_DIR, f"agentic_qa_{idx+1}.json")
        with open(qp, "w", encoding="utf-8") as f:
            json.dump(qa_results[-1], f, indent=2)

    avg_qa = sum(x["time_s"] for x in qa_results) / len(qa_results) if qa_results else 0
    total_qa = sum(x["time_s"] for x in qa_results)

    summary = {
        "timestamp": datetime.now().isoformat(),
        "embedding_mode": "local_BAAI_bge_m3_SentenceTransformer",
        "total_ingestion_time_s": round(total_ingest, 2),
        "total_embedding_time_s": round(total_embed, 2),
        "total_chunks_embedded": total_chunks,
        "pipeline": pipeline_results,
        "qa": {
            "total_questions": len(qa_results),
            "average_time_s": round(avg_qa, 2),
            "total_time_s": round(total_qa, 2),
            "questions": qa_results,
        },
    }

    summary_path = os.path.join(RESULTS_DIR, "benchmark_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  BENCHMARK COMPLETE")
    print(f"{'='*60}")
    print(f"  Ingestion: {total_ingest:.2f}s total")
    print(f"  QA: {total_qa:.2f}s total ({avg_qa:.2f}s avg)")
    print(f"  Results: {os.path.abspath(RESULTS_DIR)}")


if __name__ == "__main__":
    run_benchmarks()
