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


app = FastAPI(title="PDF RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
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