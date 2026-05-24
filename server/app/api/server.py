import os
from dotenv import load_dotenv
import time
from typing import Optional, List

from fastapi import FastAPI, UploadFile, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.qa.stream_ask import stream_question
from app.api.auth import get_current_user
from app.vectorstore.supabase_client import (
    create_chat_session,
    list_chat_sessions,
    list_chat_messages
)

from app.api.upload import (
    upload_pdf,
    get_job_status,
    get_all_jobs,
    list_uploaded_files,
    delete_uploaded_file
)


load_dotenv()

# Record start time to report uptime on the health endpoint
START_TIME = time.time()

app = FastAPI(title="PDF RAG API", version="1.0.0")

# Configure CORS origins via the ALLOWED_ORIGINS environment variable.
# Example: ALLOWED_ORIGINS="https://your-site.vercel.app,https://www.your-site.com"
node_env = os.getenv("NODE_ENV", "development").lower()
is_prod = node_env == "production"

default_origins = "https://pdf-rag-nu-one.vercel.app" if is_prod else "http://localhost:3000"
raw_origins = os.getenv("ALLOWED_ORIGINS", default_origins)

if raw_origins.strip() == "*":
    origins = ["*"]
else:
    origins = []
    for o in raw_origins.split(","):
        o = o.strip()
        if o:
            # Strip trailing slash if present (except for file schemas or empty strings)
            if o.endswith("/") and not o.startswith("file:"):
                o = o.rstrip("/")
            origins.append(o)

# When using wildcard origins, browsers disallow credentials. Disable credentials
# automatically in that case to avoid CORS errors.
allow_credentials = False if origins == ["*"] else True

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)



class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    selected_files: Optional[List[str]] = None


@app.post("/chat")
async def chat(request: ChatRequest, user_id: str = Depends(get_current_user)):
    async def event_generator():
        async for token in stream_question(
            request.question,
            user_id=user_id,
            session_id=request.session_id,
            selected_files=request.selected_files
        ):
            yield token

    return StreamingResponse(
        event_generator(),
        media_type="text/plain"
    )


@app.get("/chat/sessions")
async def get_sessions(user_id: str = Depends(get_current_user)):
    """List all chat sessions for the authenticated user."""
    return await list_chat_sessions(user_id)


class CreateSessionRequest(BaseModel):
    title: str
    filename: Optional[str] = None


@app.post("/chat/sessions")
async def create_session(request: CreateSessionRequest, user_id: str = Depends(get_current_user)):
    """Create a new chat session for the authenticated user."""
    return await create_chat_session(user_id, request.title, request.filename)


@app.delete("/upload/files/{filename}")
async def delete_file(filename: str, user_id: str = Depends(get_current_user)):
    """Delete an uploaded PDF file and all its dependencies from the workspace."""
    return await delete_uploaded_file(filename, user_id)


@app.get("/chat/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, user_id: str = Depends(get_current_user)):
    """List all chat messages for a specific session."""
    return await list_chat_messages(session_id, user_id)


@app.post("/upload")
async def upload(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):
    """
    Upload a PDF file (max 50MB).

    The file will be saved to data/cleaned_pdfs/{user_id}/ and processed
    through the complete pipeline (parse → chunk → index).
    """
    return await upload_pdf(file, background_tasks, user_id=user_id)


@app.get("/health")
def health():
    """Lightweight health check used by load balancers and deployment platforms."""
    return {
        "status": "ok",
        "uptime_seconds": int(time.time() - START_TIME),
    }


@app.head("/health")
def health_head():
    """Allow HEAD probes to pass without returning a body."""
    return {}


@app.get("/upload/status/{job_id}")
async def job_status(job_id: str, user_id: str = Depends(get_current_user)):
    """Get the status of a processing job."""
    return get_job_status(job_id, user_id=user_id)


@app.get("/upload/jobs")
async def all_jobs(user_id: str = Depends(get_current_user)):
    """Get all processing jobs."""
    return get_all_jobs(user_id=user_id)


@app.get("/upload/files")
async def files(user_id: str = Depends(get_current_user)):
    """List all uploaded PDF files."""
    return await list_uploaded_files(user_id=user_id)