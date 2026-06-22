import os
import time
import httpx
from fastapi import HTTPException

def transcribe_audio(file_path: str) -> str:
    """Transcribes an audio file using Groq Whisper API with fallback handling and timestamp aggregation."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured.")

    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    def process_verbose_json(response_json) -> str:
        segments = response_json.get("segments", [])
        final_blocks = []
        last_timestamp_sec = -999.0
        current_block_texts = []
        
        for segment in segments:
            sec = segment.get("start", 0.0)
            text = segment.get("text", "").strip()
            if not text:
                continue
                
            if sec - last_timestamp_sec >= 15.0:
                if current_block_texts:
                    final_blocks.append(" ".join(current_block_texts))
                    current_block_texts = []
                
                m = int(sec // 60)
                s = int(sec % 60)
                ts_formatted = f"[{m:02d}:{s:02d}]"
                current_block_texts.append(ts_formatted)
                last_timestamp_sec = sec
                
            current_block_texts.append(text)
            
        if current_block_texts:
            final_blocks.append(" ".join(current_block_texts))
            
        return "\n\n".join(final_blocks)

    # First attempt with turbo model
    model = "whisper-large-v3-turbo"
    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "audio/mpeg")}
            data = {"model": model, "response_format": "verbose_json"}
            
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url, headers=headers, files=files, data=data)
            
            if response.status_code in [429, 500, 502, 503, 504]:
                print(f"Groq API {response.status_code} on {model}, falling back to whisper-large-v3...")
                time.sleep(2)
                model = "whisper-large-v3"
                with open(file_path, "rb") as f2:
                    files = {"file": (os.path.basename(file_path), f2, "audio/mpeg")}
                    data = {"model": model, "response_format": "verbose_json"}
                    with httpx.Client(timeout=120.0) as client2:
                        response2 = client2.post(url, headers=headers, files=files, data=data)
                        response2.raise_for_status()
                        return process_verbose_json(response2.json())
            else:
                response.raise_for_status()
                return process_verbose_json(response.json())
    except Exception as e:
        raise Exception(f"Failed to transcribe audio chunk: {str(e)}")
