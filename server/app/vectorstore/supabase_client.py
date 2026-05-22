import os
import httpx
import uuid
import threading
from typing import Dict, List, Optional
from datetime import datetime, timezone

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Local in-memory mock database for fallback
_local_db_lock = threading.Lock()
_local_documents: List[dict] = []
_local_sessions: List[dict] = []
_local_messages: List[dict] = []

def is_supabase_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)

async def _get_client_headers() -> dict:
    return {
        "apikey": SUPABASE_KEY or "",
        "Authorization": f"Bearer {SUPABASE_KEY or ''}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

async def insert_document(user_id: str, filename: str, parsed_path: str, pdf_hash: str) -> Optional[dict]:
    if not is_supabase_configured():
        with _local_db_lock:
            doc = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "filename": filename,
                "parsed_path": parsed_path,
                "pdf_hash": pdf_hash,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            _local_documents.append(doc)
            return doc
    try:
        headers = await _get_client_headers()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/user_documents",
                headers=headers,
                json={
                    "user_id": user_id,
                    "filename": filename,
                    "parsed_path": parsed_path,
                    "pdf_hash": pdf_hash
                }
            )
            resp.raise_for_status()
            data = resp.json()
            return data[0] if isinstance(data, list) and data else data
    except Exception as e:
        print(f"Supabase error inserting document: {e}")
        return None

def insert_document_sync(user_id: str, filename: str, parsed_path: str, pdf_hash: str) -> Optional[dict]:
    if not is_supabase_configured():
        with _local_db_lock:
            doc = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "filename": filename,
                "parsed_path": parsed_path,
                "pdf_hash": pdf_hash,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            _local_documents.append(doc)
            return doc
    try:
        headers = {
            "apikey": SUPABASE_KEY or "",
            "Authorization": f"Bearer {SUPABASE_KEY or ''}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        with httpx.Client() as client:
            resp = client.post(
                f"{SUPABASE_URL}/rest/v1/user_documents",
                headers=headers,
                json={
                    "user_id": user_id,
                    "filename": filename,
                    "parsed_path": parsed_path,
                    "pdf_hash": pdf_hash
                }
            )
            resp.raise_for_status()
            data = resp.json()
            return data[0] if isinstance(data, list) and data else data
    except Exception as e:
        print(f"Supabase error inserting document (sync): {e}")
        return None

async def list_documents(user_id: str) -> List[dict]:
    if not is_supabase_configured():
        with _local_db_lock:
            return [doc for doc in _local_documents if doc["user_id"] == user_id]
    try:
        headers = {
            "apikey": SUPABASE_KEY or "",
            "Authorization": f"Bearer {SUPABASE_KEY or ''}"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SUPABASE_URL}/rest/v1/user_documents?user_id=eq.{user_id}&select=*",
                headers=headers
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        print(f"Supabase error listing documents: {e}")
        return []

async def create_chat_session(user_id: str, title: str) -> Optional[dict]:
    if not is_supabase_configured():
        with _local_db_lock:
            session = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "title": title,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            _local_sessions.append(session)
            return session
    try:
        headers = await _get_client_headers()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/chat_sessions",
                headers=headers,
                json={
                    "user_id": user_id,
                    "title": title
                }
            )
            resp.raise_for_status()
            data = resp.json()
            return data[0] if isinstance(data, list) and data else data
    except Exception as e:
        print(f"Supabase error creating chat session: {e}")
        return None

async def list_chat_sessions(user_id: str) -> List[dict]:
    if not is_supabase_configured():
        with _local_db_lock:
            filtered = [s for s in _local_sessions if s["user_id"] == user_id]
            return sorted(filtered, key=lambda x: x["created_at"], reverse=True)
    try:
        headers = {
            "apikey": SUPABASE_KEY or "",
            "Authorization": f"Bearer {SUPABASE_KEY or ''}"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SUPABASE_URL}/rest/v1/chat_sessions?user_id=eq.{user_id}&select=*&order=created_at.desc",
                headers=headers
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        print(f"Supabase error listing sessions: {e}")
        return []

async def insert_chat_message(session_id: str, user_id: str, role: str, content: str) -> Optional[dict]:
    if not is_supabase_configured():
        with _local_db_lock:
            msg = {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "user_id": user_id,
                "role": role,
                "content": content,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            _local_messages.append(msg)
            return msg
    try:
        headers = await _get_client_headers()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/chat_messages",
                headers=headers,
                json={
                    "session_id": session_id,
                    "user_id": user_id,
                    "role": role,
                    "content": content
                }
            )
            resp.raise_for_status()
            data = resp.json()
            return data[0] if isinstance(data, list) and data else data
    except Exception as e:
        print(f"Supabase error inserting message: {e}")
        return None

async def list_chat_messages(session_id: str, user_id: str) -> List[dict]:
    if not is_supabase_configured():
        with _local_db_lock:
            filtered = [
                m for m in _local_messages
                if m["session_id"] == session_id and m["user_id"] == user_id
            ]
            return sorted(filtered, key=lambda x: x["created_at"])
    try:
        headers = {
            "apikey": SUPABASE_KEY or "",
            "Authorization": f"Bearer {SUPABASE_KEY or ''}"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SUPABASE_URL}/rest/v1/chat_messages?session_id=eq.{session_id}&user_id=eq.{user_id}&select=*&order=created_at.asc",
                headers=headers
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        print(f"Supabase error listing messages: {e}")
        return []
