import os
import shutil
import uuid
import time
import json
import re
from datetime import datetime

# --- EXCLUDE API SLEEP TIMES FROM BENCHMARKS ---
API_SLEEP_TIME = 0
original_perf_counter = time.perf_counter

def custom_perf_counter():
    return original_perf_counter() - API_SLEEP_TIME

time.perf_counter = custom_perf_counter

import functools

def add_exponential_backoff_to_gemini():
    try:
        import app.llm.gemini as llm_gemini
        import app.embeddings.embedder as embedder
        
        def with_backoff(func):
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
                            print(f"\n    [Rate Limit Hit!] Waiting {delay}s before retry {attempt+1}/{max_retries} for {func.__name__}...")
                            # Use original sleep, record time
                            time.sleep(delay)
                            API_SLEEP_TIME += delay
                        else:
                            raise
            return wrapper

        if hasattr(llm_gemini, "generate_answer"):
            llm_gemini.generate_answer = with_backoff(llm_gemini.generate_answer)
        if hasattr(embedder, "get_embedding"):
            embedder.get_embedding = with_backoff(embedder.get_embedding)
    except Exception as e:
        print(f"Failed to patch Gemini functions with backoff: {e}")

# -----------------------------------------------

os.chdir(os.path.dirname(os.path.abspath(__file__)))

add_exponential_backoff_to_gemini()

from app.api.upload import process_pdf_pipeline, job_store, Job, INPUT_DIR
from app.agent.agentic_qa import ask_agentic_question

BENCHMARK_DIR = os.path.join("app", "benchmark")
RESULTS_DIR = "benchmark-cloud"
os.makedirs(RESULTS_DIR, exist_ok=True)

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
    print("=== STARTING BENCHMARK ===")
    
    # 1. Ingest PDFs
    pdf_files = [f for f in os.listdir(BENCHMARK_DIR) if f.endswith(".pdf")]
    
    upload_times = {}
    
    for pdf in pdf_files:
        src_path = os.path.join(BENCHMARK_DIR, pdf)
        dst_path = os.path.join(INPUT_DIR, pdf)
        
        # Copy to input dir so process_pdf_pipeline can find it
        shutil.copy2(src_path, dst_path)
        
        job_id = str(uuid.uuid4())
        job_store[job_id] = Job(job_id=job_id, filename=pdf)
        
        print(f"\nProcessing PDF: {pdf}")
        start_t = time.perf_counter()
        try:
            process_pdf_pipeline(pdf, job_id)
        except Exception as e:
            print(f"Error processing {pdf}: {e}")
        end_t = time.perf_counter()
        
        upload_times[pdf] = end_t - start_t
        print(f"Finished {pdf} in {upload_times[pdf]:.2f}s")
        
    print("\n--- INGESTION COMPLETE ---")
    
    # 2. Run QA
    questions = parse_questions()
    qa_times = []
    
    print(f"\nRunning {len(questions)} questions...")
    for idx, q in enumerate(questions):
        print(f"\nQ{idx+1}/{len(questions)}: {q}")
        start_t = time.perf_counter()
        try:
            res = ask_agentic_question(q)
            # just check it didn't fail
            answer = "Success" if res and "answer" in res else "Failed"
        except Exception as e:
            answer = f"Error: {e}"
            print(answer)
        end_t = time.perf_counter()
        
        duration = end_t - start_t
        qa_times.append({
            "question": q,
            "time_seconds": duration,
            "status": answer[:50]
        })
        print(f"Time: {duration:.2f}s")
        
    # 3. Save Summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "upload_times_seconds": upload_times,
        "qa_times": qa_times,
        "average_qa_time": sum(x["time_seconds"] for x in qa_times) / len(qa_times) if qa_times else 0,
        "total_pdf_processing_time": sum(upload_times.values())
    }
    
    summary_path = os.path.join(RESULTS_DIR, "benchmark_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    print(f"\n=== BENCHMARK FINISHED ===")
    print(f"Results saved to {summary_path}")
    print(f"Detailed step metrics are in the '{RESULTS_DIR}' folder.")

if __name__ == "__main__":
    run_benchmarks()
