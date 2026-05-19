import os
from dotenv import load_dotenv
import time

from fastapi import FastAPI, UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.qa.stream_ask import stream_question

from app.api.upload import (
    upload_pdf,
    get_job_status,
    get_all_jobs,
    list_uploaded_files
)


load_dotenv()

# Record start time to report uptime on the health endpoint
START_TIME = time.time()

app = FastAPI(title="PDF RAG API", version="1.0.0")

# Configure CORS origins via the ALLOWED_ORIGINS environment variable.
# Example: ALLOWED_ORIGINS="https://your-site.vercel.app,https://www.your-site.com"
raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
if raw_origins.strip() == "*":
    origins = ["*"]
else:
    origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

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


@app.post("/chat")
async def chat(request: ChatRequest):
    async def event_generator():
        for token in stream_question(request.question):
            yield token

    return StreamingResponse(
        event_generator(),
        media_type="text/plain"
    )


@app.post("/upload")
async def upload(
    file: UploadFile,
    background_tasks: BackgroundTasks
):
    """
    Upload a PDF file (max 50MB).

    The file will be saved to data/cleaned_pdfs/ and processed
    through the complete pipeline (parse → chunk → index).
    """
    return await upload_pdf(file, background_tasks)


@app.head("/health")
def health():
    """Lightweight health check used by load balancers and deployment platforms."""
    return {
        "status": "ok",
        "uptime_seconds": int(time.time() - START_TIME),
    }


@app.get("/upload/status/{job_id}")
async def job_status(job_id: str):
    """Get the status of a processing job."""
    return get_job_status(job_id)


@app.get("/upload/jobs")
async def all_jobs():
    """Get all processing jobs."""
    return get_all_jobs()


@app.get("/upload/files")
async def files():
    """List all uploaded PDF files."""
    return list_uploaded_files()