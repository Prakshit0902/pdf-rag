import os
import uuid
import asyncio
import json
from datetime import datetime
from typing import Dict, Optional, Any
from enum import Enum

from fastapi import UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.ingestion.cache import (
    compute_bytes_hash,
    is_cached,
    get_cached_entry,
    set_cached_entry,
    mark_indexed,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".pdf"}


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job:
    def __init__(
        self,
        job_id: str,
        filename: str,
        user_id: str,
        status: JobStatus = JobStatus.PENDING,
        error: Optional[str] = None,
        created_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ):
        self.job_id = job_id
        self.filename = filename
        self.user_id = user_id
        self.status = status
        self.error = error
        self.created_at = created_at or datetime.utcnow()
        self.completed_at = completed_at

    def to_dict(self):
        return {
            "job_id": self.job_id,
            "filename": self.filename,
            "user_id": self.user_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }


job_store: Dict[str, Job] = {}


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file."""
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )


async def validate_file_size(file: UploadFile) -> bytes:
    """Read and validate file size."""
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds maximum limit of 50MB"
        )
    return contents


async def save_file(file: UploadFile, contents: bytes, user_id: str) -> str:
    """Save uploaded file to disk."""
    safe_filename = os.path.basename(file.filename)
    user_input_dir = os.path.join(BASE_DIR, "data", "cleaned_pdfs", user_id)
    os.makedirs(user_input_dir, exist_ok=True)
    filepath = os.path.join(user_input_dir, safe_filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    return safe_filename


def process_pdf_pipeline(filename: str, job_id: str, user_id: str, pdf_hash: Optional[str] = None) -> None:
    """Background task to process PDF through the pipeline."""
    job = job_store.get(job_id)
    if not job:
        return

    # Scope all paths dynamically by user_id
    user_input_dir = os.path.join(BASE_DIR, "data", "cleaned_pdfs", user_id)
    user_parsed_dir = os.path.join(BASE_DIR, "data", "parsed", user_id)
    user_image_dir = os.path.join(BASE_DIR, "data", "images", user_id)
    user_page_render_dir = os.path.join(BASE_DIR, "data", "page_renders", user_id)

    os.makedirs(user_input_dir, exist_ok=True)
    os.makedirs(user_parsed_dir, exist_ok=True)
    os.makedirs(user_image_dir, exist_ok=True)
    os.makedirs(user_page_render_dir, exist_ok=True)

    try:
        job.status = JobStatus.PROCESSING

        pdf_path = os.path.join(user_input_dir, filename)

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at {pdf_path}")

        # -------------------------
        # Step 1: Extract Images
        # -------------------------
        from app.parsing.extract_images import extract_images_from_pdf

        pdf_image_dir = os.path.join(
            user_image_dir,
            filename.replace(".pdf", "")
        )

        image_map = extract_images_from_pdf(pdf_path, pdf_image_dir)
        print(f"[{job_id}] Extracted {sum(len(v) for v in image_map.values())} images")

        # -------------------------
        # Step 2: Render Pages
        # -------------------------
        from app.parsing.render_pages import render_pdf_pages

        pdf_render_dir = os.path.join(
            user_page_render_dir,
            filename.replace(".pdf", "")
        )

        page_render_map = render_pdf_pages(pdf_path, pdf_render_dir)
        print(f"[{job_id}] Rendered {len(page_render_map)} pages")

        # -------------------------
        # Step 3: Parse PDF
        # -------------------------
        from app.parsing.parser import parse_pdf

        documents = parse_pdf(pdf_path)
        print(f"[{job_id}] Parsed {len(documents)} document blocks")

        # -------------------------
        # Step 4: Build Chunks
        # -------------------------
        from app.ingestion.process_pdfs import build_chunks

        chunks = build_chunks(
            documents,
            filename,
            image_map,
            page_render_map
        )

        # -------------------------
        # Step 5: Save Chunks
        # -------------------------
        output_path = os.path.join(
            user_parsed_dir,
            filename.replace(".pdf", ".json")
        )

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

        print(f"[{job_id}] Saved chunks to {output_path}")

        # Cache the parsed result
        if pdf_hash:
            set_cached_entry(pdf_hash, filename, output_path, user_id=user_id)

        # -------------------------
        # Step 6: Index Chunks
        # -------------------------
        from app.ingestion.index_chunks import index_single_file

        index_single_file(output_path, user_id=user_id)
        print(f"[{job_id}] Indexed chunks to vector store")

        # ── Launch metadata generation in background (non-blocking) ──
        import threading
        from app.agent.metadata_generator import generate_and_save_metadata

        def _run_metadata_bg(bg_chunks, bg_filename, bg_user_id, bg_job_id):
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    generate_and_save_metadata(bg_chunks, bg_filename, bg_user_id)
                )
                print(f"[{bg_job_id}] Metadata generation completed")
            except Exception as meta_err:
                print(f"[{bg_job_id}] Metadata generation failed: {meta_err}")
            finally:
                loop.close()

        meta_thread = threading.Thread(
            target=_run_metadata_bg,
            args=(chunks, filename, user_id, job_id),
            daemon=True,
        )
        meta_thread.start()

        # Sync metadata to Supabase
        try:
            from app.vectorstore.supabase_client import insert_document_sync
            insert_document_sync(user_id, filename, output_path, pdf_hash or "")
        except Exception as db_err:
            print(f"Failed to sync uploaded file to Supabase: {db_err}")

        if pdf_hash:
            mark_indexed(pdf_hash, user_id=user_id)

        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()

    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)
        job.completed_at = datetime.utcnow()
        print(f"[{job_id}] Failed: {e}")


async def upload_pdf(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    user_id: str = "default_tenant"
) -> JSONResponse:
    validate_file(file)

    contents = await validate_file_size(file)

    pdf_hash = compute_bytes_hash(contents)

    if is_cached(pdf_hash, user_id=user_id):
        entry = get_cached_entry(pdf_hash, user_id=user_id) or {}
        
        # If cache exists, make sure it is also synced to Supabase
        try:
            from app.vectorstore.supabase_client import insert_document_sync
            insert_document_sync(user_id, file.filename, entry.get("parsed_path", ""), pdf_hash)
        except Exception as db_err:
            print(f"Failed to sync cached file to Supabase: {db_err}")

        return JSONResponse(
            status_code=200,
            content={
                "message": "File already processed (cached)",
                "filename": file.filename,
                "parsed_path": entry.get("parsed_path"),
                "status": "cached",
            }
        )

    filename = await save_file(file, contents, user_id=user_id)

    job_id = str(uuid.uuid4())
    job = Job(job_id=job_id, filename=filename, user_id=user_id)
    job_store[job_id] = job

    background_tasks.add_task(process_pdf_pipeline, filename, job_id, user_id, pdf_hash)

    return JSONResponse(
        status_code=202,
        content={
            "message": "File uploaded successfully, processing started",
            "job_id": job_id,
            "filename": filename,
            "status": job.status.value
        }
    )


def get_job_status(job_id: str, user_id: str = "default_tenant") -> JSONResponse:
    """Get the status of a processing job."""
    job = job_store.get(job_id)

    # Allow access only if job matches user_id (or fallback default_tenant)
    if not job or (job.user_id != user_id and user_id != "default_tenant" and job.user_id != "default_tenant"):
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    return JSONResponse(content=job.to_dict())


def get_all_jobs(user_id: str = "default_tenant") -> JSONResponse:
    """Get all jobs."""
    jobs = [
        job.to_dict() for job in job_store.values()
        if job.user_id == user_id or user_id == "default_tenant"
    ]
    return JSONResponse(content=jobs)


async def list_uploaded_files(user_id: str = "default_tenant") -> JSONResponse:
    """List uploaded PDF files from database or local directory fallback."""
    from app.vectorstore.supabase_client import is_supabase_configured, list_documents
    if is_supabase_configured() and user_id != "default_tenant":
        docs = await list_documents(user_id)
        files = [d["filename"] for d in docs]
        return JSONResponse(content={"files": files})

    user_input_dir = os.path.join(BASE_DIR, "data", "cleaned_pdfs", user_id)
    os.makedirs(user_input_dir, exist_ok=True)
    files = [
        f for f in os.listdir(user_input_dir)
        if f.endswith(".pdf")
    ]
    return JSONResponse(content={"files": files})


async def delete_uploaded_file(filename: str, user_id: str) -> JSONResponse:
    """Delete an uploaded PDF and all its artifacts/DB connections cleanly."""
    import shutil
    from app.vectorstore.supabase_client import delete_document, delete_chat_sessions_by_file
    from app.vectorstore.qdrant_client import client as qdrant_client
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    from app.retrieval.bm25_index import reload_index
    from app.ingestion.cache import delete_cache_by_filename

    # 1. Disk cleanup
    user_input_path = os.path.join(BASE_DIR, "data", "cleaned_pdfs", user_id, filename)
    user_parsed_path = os.path.join(BASE_DIR, "data", "parsed", user_id, filename.replace(".pdf", ".json"))
    user_image_path = os.path.join(BASE_DIR, "data", "images", user_id, filename.replace(".pdf", ""))
    user_page_render_path = os.path.join(BASE_DIR, "data", "page_renders", user_id, filename.replace(".pdf", ""))
    user_metadata_path = os.path.join(BASE_DIR, "data", "metadata", user_id, filename.replace(".pdf", ".json"))

    try:
        if os.path.exists(user_input_path):
            os.remove(user_input_path)
        if os.path.exists(user_parsed_path):
            os.remove(user_parsed_path)
        if os.path.exists(user_image_path):
            shutil.rmtree(user_image_path, ignore_errors=True)
        if os.path.exists(user_page_render_path):
            shutil.rmtree(user_page_render_path, ignore_errors=True)
        if os.path.exists(user_metadata_path):
            os.remove(user_metadata_path)
    except Exception as disk_err:
        print(f"Disk cleanup error during file deletion: {disk_err}")

    # 2. Qdrant cleanup
    try:
        qdrant_client.delete(
            collection_name="pdf_rag",
            points_selector=Filter(
                must=[
                    FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                    FieldCondition(key="source_file", match=MatchValue(value=filename))
                ]
            )
        )
    except Exception as qdrant_err:
        print(f"Qdrant cleanup error during file deletion: {qdrant_err}")

    # 3. Reload BM25 index
    try:
        reload_index(user_id)
    except Exception as bm25_err:
        print(f"BM25 reload error during file deletion: {bm25_err}")

    # 4. Cache eviction
    try:
        delete_cache_by_filename(filename, user_id=user_id)
    except Exception as cache_err:
        print(f"Cache eviction error during file deletion: {cache_err}")

    # 5. Database cleanup
    try:
        await delete_document(user_id, filename)
        await delete_chat_sessions_by_file(user_id, filename)
    except Exception as db_err:
        print(f"Database cleanup error during file deletion: {db_err}")

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": f"Successfully deleted document '{filename}' and all related resources."
        }
    )