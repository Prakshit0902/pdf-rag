import os
import uuid
import asyncio
import json
import re
import glob
import tempfile
import yt_dlp
import imageio_ffmpeg
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
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx", ".pptx"}


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
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, TXT, DOCX, and PPTX files are allowed"
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
            raise FileNotFoundError(f"File not found at {pdf_path}")

        # Check if PDF or TXT or DOCX or PPTX
        ext = os.path.splitext(filename)[1].lower()
        is_pdf = ext == ".pdf"
        is_txt = ext == ".txt"
        is_docx = ext == ".docx"
        is_pptx = ext == ".pptx"
        
        name_without_ext = os.path.splitext(filename)[0]

        if is_pdf:
            # -------------------------
            # Step 1: Extract Images
            # -------------------------
            from app.parsing.extract_images import extract_images_from_pdf

            pdf_image_dir = os.path.join(
                user_image_dir,
                name_without_ext
            )

            image_map = extract_images_from_pdf(pdf_path, pdf_image_dir)
            print(f"[{job_id}] Extracted {sum(len(v) for v in image_map.values())} images")

            # -------------------------
            # Step 2: Render Pages
            # -------------------------
            from app.parsing.render_pages import render_pdf_pages

            pdf_render_dir = os.path.join(
                user_page_render_dir,
                name_without_ext
            )

            page_render_map = render_pdf_pages(pdf_path, pdf_render_dir)
            print(f"[{job_id}] Rendered {len(page_render_map)} pages")

            # -------------------------
            # Step 3: Parse PDF
            # -------------------------
            from app.parsing.parser import parse_pdf

            documents = parse_pdf(pdf_path)
            print(f"[{job_id}] Parsed {len(documents)} document blocks")
        else:
            # It's a text-based or office file
            image_map = {}
            page_render_map = {}

            from llama_index.core import Document
            
            text_content = ""
            if is_txt:
                with open(pdf_path, "r", encoding="utf-8", errors="ignore") as f:
                    text_content = f.read()
            elif is_docx:
                from app.parsing.parse_office import extract_text_from_docx, extract_images_from_docx
                text_content = extract_text_from_docx(pdf_path)
                pdf_image_dir = os.path.join(user_image_dir, name_without_ext)
                image_map = extract_images_from_docx(pdf_path, pdf_image_dir)
                print(f"[{job_id}] Extracted {sum(len(v) for v in image_map.values())} images from DOCX")
            elif is_pptx:
                from app.parsing.parse_office import extract_text_from_pptx, extract_images_from_pptx
                text_content = extract_text_from_pptx(pdf_path)
                pdf_image_dir = os.path.join(user_image_dir, name_without_ext)
                image_map = extract_images_from_pptx(pdf_path, pdf_image_dir)
                print(f"[{job_id}] Extracted {sum(len(v) for v in image_map.values())} images from PPTX")

            documents = [Document(
                text=text_content,
                metadata={
                    "file_path": pdf_path,
                    "source": ext[1:],
                }
            )]
            print(f"[{job_id}] Loaded {ext} file directly")

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
            f"{name_without_ext}.json"
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
    """List uploaded files from database or local directory fallback."""
    from app.vectorstore.supabase_client import is_supabase_configured, list_documents
    if is_supabase_configured() and user_id != "default_tenant":
        docs = await list_documents(user_id)
        files = [d["filename"] for d in docs]
        return JSONResponse(content={"files": files})

    user_input_dir = os.path.join(BASE_DIR, "data", "cleaned_pdfs", user_id)
    os.makedirs(user_input_dir, exist_ok=True)
    files = [
        f for f in os.listdir(user_input_dir)
        if f.endswith(".pdf") or f.endswith(".txt") or f.endswith(".docx") or f.endswith(".pptx")
    ]
    return JSONResponse(content={"files": files})


async def delete_uploaded_file(filename: str, user_id: str) -> JSONResponse:
    """Delete an uploaded file and all its artifacts/DB connections cleanly."""
    import shutil
    from app.vectorstore.supabase_client import delete_document, delete_chat_sessions_by_file
    from app.vectorstore.qdrant_client import client as qdrant_client
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    from app.retrieval.bm25_index import reload_index
    from app.ingestion.cache import delete_cache_by_filename

    name_without_ext = os.path.splitext(filename)[0]
    # 1. Disk cleanup
    user_input_path = os.path.join(BASE_DIR, "data", "cleaned_pdfs", user_id, filename)
    user_parsed_path = os.path.join(BASE_DIR, "data", "parsed", user_id, f"{name_without_ext}.json")
    user_image_path = os.path.join(BASE_DIR, "data", "images", user_id, name_without_ext)
    user_page_render_path = os.path.join(BASE_DIR, "data", "page_renders", user_id, name_without_ext)
    user_metadata_path = os.path.join(BASE_DIR, "data", "metadata", user_id, f"{name_without_ext}.json")

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


def extract_youtube_info(url: str) -> Optional[Dict[str, str]]:
    """Extract YouTube video or playlist ID."""
    video_id = None
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&\s]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([^?\s]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([^?\s]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/v/([^?\s]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([^?\s]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            break
            
    playlist_id = None
    playlist_match = re.search(r'[?&]list=([^&\s]+)', url)
    if playlist_match:
        playlist_id = playlist_match.group(1)
        
    if video_id:
        # If there's a video ID, we treat it as a video (ignore playlist)
        return {"type": "video", "id": video_id}
    elif playlist_id:
        return {"type": "playlist", "id": playlist_id}
        
    return None


def parse_vtt(vtt_path: str) -> str:
    """Parses a WebVTT file and returns text with aggregated [MM:SS] timestamps."""
    if not os.path.exists(vtt_path):
        return ""

    with open(vtt_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Normalize line endings
    content = content.replace("\r\n", "\n")
    
    # Split into blocks (separated by empty lines)
    blocks = content.split("\n\n")
    
    raw_cues = []
    for block in blocks:
        lines = block.strip().split("\n")
        # Find the line containing the timestamp
        timestamp_idx = -1
        for i, line in enumerate(lines):
            if "-->" in line:
                timestamp_idx = i
                break
        
        if timestamp_idx != -1:
            start_ts_str = lines[timestamp_idx].split("-->")[0].strip()
            parts = start_ts_str.split(":")
            sec = 0.0
            try:
                if len(parts) == 3:
                    sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
                elif len(parts) == 2:
                    sec = int(parts[0]) * 60 + float(parts[1])
            except ValueError:
                pass

            # The text lines start after the timestamp
            text_lines = lines[timestamp_idx + 1:]
            clean_cue_lines = []
            for line in text_lines:
                cleaned = re.sub(r'<[^>]+>', '', line).strip()
                if cleaned:
                    clean_cue_lines.append(cleaned)
            
            if clean_cue_lines:
                raw_cues.append({
                    "sec": sec,
                    "text": " ".join(clean_cue_lines)
                })

    # YouTube auto-captions have overlapping text.
    # If a cue text is a prefix of the next cue text, we skip it.
    deduped_cues = []
    for i, cue in enumerate(raw_cues):
        if i < len(raw_cues) - 1:
            next_cue = raw_cues[i + 1]
            if next_cue["text"].strip().startswith(cue["text"].strip()):
                continue
        deduped_cues.append(cue)
        
    # Aggregate text with 15-second windows
    final_blocks = []
    last_timestamp_sec = -999.0
    current_block_texts = []
    
    for cue in deduped_cues:
        sec = cue["sec"]
        if sec - last_timestamp_sec >= 15.0:
            if current_block_texts:
                final_blocks.append(" ".join(current_block_texts))
                current_block_texts = []
            
            m = int(sec // 60)
            s = int(sec % 60)
            ts_formatted = f"[{m:02d}:{s:02d}]"
            current_block_texts.append(ts_formatted)
            last_timestamp_sec = sec
            
        current_block_texts.append(cue["text"])
        
    if current_block_texts:
        final_blocks.append(" ".join(current_block_texts))

    return "\n\n".join(final_blocks)

def process_youtube_pipeline(url: str, item_id: str, job_id: str, user_id: str, is_playlist: bool = False, needs_transcription: bool = False, transcribe_duration: Optional[int] = None) -> None:
    """Background task to download YouTube subtitles, save to disk, and index."""
    job = job_store.get(job_id)
    if not job:
        return

    try:
        job.status = JobStatus.PROCESSING

        user_input_dir = os.path.join(BASE_DIR, "data", "cleaned_pdfs", user_id)
        os.makedirs(user_input_dir, exist_ok=True)

        # Download subtitles using yt-dlp into a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            if not needs_transcription:
                ydl_opts = {
                    'skip_download': True,
                    'writeautomaticsub': True,
                    'writesubtitles': True,
                    'subtitleslangs': ['en', 'en-US'],
                    'outtmpl': os.path.join(temp_dir, '%(id)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'noplaylist': not is_playlist,
                    'nocheckcertificate': True,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android', 'web']
                        }
                    },
                }
                if is_playlist:
                    ydl_opts['playlistend'] = 5  # limit to first 5 videos

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if 'entries' in info:
                        video_title = info.get('title', f"Playlist_{item_id}")
                    else:
                        video_title = info.get('title', item_id)
                    # Clean up video title for safe filename
                    safe_title = "".join(c for c in video_title if c.isalnum() or c in " -_").strip()
                    ydl.download([url])

                # Locate downloaded subtitle file(s)
                vtt_files = glob.glob(os.path.join(temp_dir, "*.vtt"))
                if not vtt_files:
                    raise Exception("No subtitles or captions found for this video/playlist.")

                all_clean_text = []
                for vtt_path in vtt_files:
                    text = parse_vtt(vtt_path)
                    if text.strip():
                        all_clean_text.append(text)
                        
                clean_text = "\n\n".join(all_clean_text)

                if not clean_text.strip():
                    raise Exception("Subtitles download completed but text content was empty.")
            else:
                # Transcription Logic using Groq Whisper API
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'ffmpeg_location': ffmpeg_exe,
                    'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'noplaylist': True,
                    'nocheckcertificate': True,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android', 'web']
                        }
                    },
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    video_title = info.get('title', item_id)
                    safe_title = "".join(c for c in video_title if c.isalnum() or c in " -_").strip()
                    ydl.download([url])

                audio_files = glob.glob(os.path.join(temp_dir, "*.mp3"))
                if not audio_files:
                    raise Exception("Failed to download audio for transcription.")
                audio_path = audio_files[0]

                # Limit audio to specified duration if needed
                if transcribe_duration:
                    short_audio_path = os.path.join(temp_dir, "short_audio.mp3")
                    import subprocess
                    subprocess.run([
                        ffmpeg_exe, "-y", "-i", audio_path, "-t", str(transcribe_duration),
                        "-c", "copy", short_audio_path
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    audio_path = short_audio_path

                # Split audio into ~10 minute chunks to stay within API limit (~25MB)
                import subprocess
                subprocess.run([
                    ffmpeg_exe, "-y", "-i", audio_path, "-f", "segment", "-segment_time", "600",
                    "-c", "copy", os.path.join(temp_dir, "chunk_%03d.mp3")
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                chunk_files = sorted(glob.glob(os.path.join(temp_dir, "chunk_*.mp3")))
                if not chunk_files:
                    raise Exception("Failed to split audio into chunks.")

                from app.api.groq_whisper import transcribe_audio
                all_clean_text = []
                for chunk_file in chunk_files:
                    text = transcribe_audio(chunk_file)
                    all_clean_text.append(text)

                clean_text = " ".join(all_clean_text)
                if not clean_text.strip():
                    raise Exception("Transcription completed but text content was empty.")

            # Limit length of total text to 150,000 characters just in case
            max_chars = 150000
            if len(clean_text) > max_chars:
                clean_text = clean_text[:max_chars] + "\n\n[TEXT TRUNCATED DUE TO LENGTH LIMIT]"

            # Create clean txt header metadata
            source_type = "Playlist" if is_playlist else "Video"
            header = (
                f"YouTube {source_type}: {video_title}\n"
                f"URL: {url}\n"
                f"ID: {item_id}\n"
                f"Indexed At: {datetime.utcnow().isoformat()}\n\n"
            )
            full_content = header + clean_text

            # Save the clean text document to disk
            filename = f"YouTube - {safe_title} ({item_id}).txt"
            filepath = os.path.join(user_input_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(full_content)

        # Update job with the actual filename
        job.filename = filename

        # Compute file hash for caching
        file_bytes = full_content.encode("utf-8")
        file_hash = compute_bytes_hash(file_bytes)

        # Delegate indexing to standard pipeline
        process_pdf_pipeline(filename, job_id, user_id, pdf_hash=file_hash)

    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)
        job.completed_at = datetime.utcnow()
        print(f"[{job_id}] YouTube pipeline failed: {e}")


async def upload_youtube_url(
    url: str,
    background_tasks: BackgroundTasks,
    user_id: str = "default_tenant"
) -> JSONResponse:
    """Validate YouTube URL, register a background job, and queue processing."""
    info = extract_youtube_info(url)
    if not info:
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL format"
        )

    is_playlist = info["type"] == "playlist"
    item_id = info["id"]
    job_id = str(uuid.uuid4())
    needs_transcription = False
    warning_msg = None
    transcribe_duration = None

    # Synchronous check for subtitles
    ydl_opts = {
        'quiet': True,
        'noplaylist': not is_playlist,
        'playlistend': 1,
        'nocheckcertificate': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        },
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=False)
            if is_playlist and 'entries' in info_dict and info_dict['entries']:
                # check the first video for a playlist
                first_video = info_dict['entries'][0]
                subs = first_video.get('subtitles', {})
                auto_subs = first_video.get('automatic_captions', {})
            else:
                subs = info_dict.get('subtitles', {})
                auto_subs = info_dict.get('automatic_captions', {})
            
            has_en_subs = any(lang.startswith('en') for lang in list(subs.keys()) + list(auto_subs.keys()))
            
            if not has_en_subs:
                if is_playlist:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "message": "This playlist does not have English subtitles. We currently cannot process playlists without subtitles.",
                            "status": "failed",
                            "is_playlist": True
                        }
                    )
                else:
                    needs_transcription = True
                    duration = info_dict.get('duration', 0)
                    if duration > 1800: # 30 minutes
                        warning_msg = "No subtitles found. Video is longer than 30 minutes, so only the first 30 minutes will be transcribed."
                        transcribe_duration = 1800
                    else:
                        warning_msg = "No subtitles found. We are downloading and transcribing the audio, which may take some time."
        except Exception as e:
            needs_transcription = True
            warning_msg = "Could not check subtitles. Will attempt to transcribe audio if needed."

    # Temporary filename placeholder
    job = Job(job_id=job_id, filename=f"youtube_{item_id}", user_id=user_id)
    job_store[job_id] = job

    background_tasks.add_task(
        process_youtube_pipeline,
        url,
        item_id,
        job_id,
        user_id,
        is_playlist,
        needs_transcription,
        transcribe_duration
    )

    if is_playlist and not needs_transcription:
        warning_msg = "You are uploading a playlist. It may take longer, and we will only index the first 5 videos to ensure efficiency."

    return JSONResponse(
        status_code=202,
        content={
            "message": warning_msg if warning_msg else "YouTube processing started",
            "job_id": job_id,
            "filename": f"youtube_{item_id}",
            "status": job.status.value,
            "is_playlist": is_playlist,
            "needs_transcription": needs_transcription
        }
    )