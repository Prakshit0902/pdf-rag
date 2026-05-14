from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from pydantic import BaseModel

from app.qa.stream_ask import (
    stream_question
)


app = FastAPI()


class ChatRequest(BaseModel):

    question: str


@app.post("/chat")
async def chat(
    request: ChatRequest
):

    async def event_generator():

        for token in stream_question(
            request.question
        ):

            yield token

    return StreamingResponse(
        event_generator(),
        media_type="text/plain"
    )