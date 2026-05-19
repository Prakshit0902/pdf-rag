import os
import uuid
import asyncio
import json
from datetime import datetime
from typing import Dict, Optional
from enum import Enum

from fastapi import UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.ingestion.cache import (
    compute_bytes_hash,
    is_cached,
    set_cached_entry,
    mark_indexed,
)

INPUT_DIR = "data/cleaned_pdfs"
PARSED_DIR = "data/parsed"
IMAGE_DIR = "data/images"
PAGE_RENDER_DIR = "data/page_renders"

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".pdf"}

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(PARSED_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(PAGE_RENDER_DIR, exist_ok=True)


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
        status: JobStatus = JobStatus.PENDING,
        error: Optional[str] = None,
        created_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ):
        self.job_id = job_id
        self.filename = filename
        self.status = status
        self.error = error
        self.created_at = created_at or datetime.utcnow()
        self.completed_at = completed_at

    def to_dict(self):
        return {
            "job_id": self.job_id,
            "filename": self.filename,
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


async def save_file(file: UploadFile, contents: bytes) -> str:
    """Save uploaded file to disk."""
    safe_filename = os.path.basename(file.filename)
    filepath = os.path.join(INPUT_DIR, safe_filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    return safe_filename


def process_pdf_pipeline(filename: str, job_id: str, pdf_hash: Optional[str] = None) -> None:
    """Background task to process PDF through the pipeline."""
    job = job_store.get(job_id)
    if not job:
        return

    try:
        job.status = JobStatus.PROCESSING

        pdf_path = os.path.join(INPUT_DIR, filename)

        # -------------------------
        # Step 1: Extract Images
        # -------------------------
        from app.parsing.extract_images import extract_images_from_pdf

        pdf_image_dir = os.path.join(
            IMAGE_DIR,
            filename.replace(".pdf", "")
        )

        image_map = extract_images_from_pdf(pdf_path, pdf_image_dir)
        print(f"[{job_id}] Extracted {sum(len(v) for v in image_map.values())} images")

        # -------------------------
        # Step 2: Render Pages
        # -------------------------
        from app.parsing.render_pages import render_pdf_pages

        pdf_render_dir = os.path.join(
            PAGE_RENDER_DIR,
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
            PARSED_DIR,
            filename.replace(".pdf", ".json")
        )

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

        print(f"[{job_id}] Saved chunks to {output_path}")

        # Cache the parsed result
        if pdf_hash:
            set_cached_entry(pdf_hash, filename, output_path)

        # -------------------------
        # Step 6: Index Chunks
        # -------------------------
        from app.ingestion.index_chunks import index_single_file

        index_single_file(output_path)
        print(f"[{job_id}] Indexed chunks to vector store")

        if pdf_hash:
            mark_indexed(pdf_hash)

        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()

    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)
        job.completed_at = datetime.utcnow()
        print(f"[{job_id}] Failed: {e}")


async def upload_pdf(
    file: UploadFile,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    validate_file(file)

    contents = await validate_file_size(file)

    pdf_hash = compute_bytes_hash(contents)

    if is_cached(pdf_hash):
        entry = _get_cached_entry_safe(pdf_hash)
        return JSONResponse(
            status_code=200,
            content={
                "message": "File already processed (cached)",
                "filename": file.filename,
                "parsed_path": entry["parsed_path"],
                "status": "cached",
            }
        )

    filename = await save_file(file, contents)

    job_id = str(uuid.uuid4())
    job = Job(job_id=job_id, filename=filename)
    job_store[job_id] = job

    background_tasks.add_task(process_pdf_pipeline, filename, job_id, pdf_hash)

    return JSONResponse(
        status_code=202,
        content={
            "message": "File uploaded successfully, processing started",
            "job_id": job_id,
            "filename": filename,
            "status": job.status.value
        }
    )


def _get_cached_entry_safe(file_hash: str) -> Optional[Dict]:
    from app.ingestion.cache import get_cached_entry
    return get_cached_entry(file_hash) or {}


def get_job_status(job_id: str) -> JSONResponse:
    """Get the status of a processing job."""
    job = job_store.get(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    return JSONResponse(content=job.to_dict())


def get_all_jobs() -> JSONResponse:
    """Get all jobs."""
    jobs = [job.to_dict() for job in job_store.values()]
    return JSONResponse(content=jobs)


def list_uploaded_files() -> JSONResponse:
    """List all uploaded PDF files."""
    files = [
        f for f in os.listdir(INPUT_DIR)
        if f.endswith(".pdf")
    ]
    return JSONResponse(content={"files": files})