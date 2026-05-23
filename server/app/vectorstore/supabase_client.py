import os
import httpx
import uuid
import threading
from typing import Dict, List, Optional
from datetime import datetime, timezone

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Global flag to dynamically switch to local database fallback if Supabase fails
_force_local_db = False

# Local in-memory mock database for fallback
_local_db_lock = threading.Lock()
_local_documents: List[dict] = []
_local_sessions: List[dict] = []
_local_messages: List[dict] = []

def is_supabase_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY) and not _force_local_db

async def _get_client_headers() -> dict:
    return {
        "apikey": SUPABASE_KEY or "",
        "Authorization": f"Bearer {SUPABASE_KEY or ''}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

# Local DB Helper Functions
def _insert_document_local(user_id: str, filename: str, parsed_path: str, pdf_hash: str) -> dict:
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

def _list_documents_local(user_id: str) -> List[dict]:
    with _local_db_lock:
        return [doc for doc in _local_documents if doc["user_id"] == user_id]

def _create_chat_session_local(user_id: str, title: str) -> dict:
    with _local_db_lock:
        session = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": title,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        _local_sessions.append(session)
        return session

def _list_chat_sessions_local(user_id: str) -> List[dict]:
    with _local_db_lock:
        filtered = [s for s in _local_sessions if s["user_id"] == user_id]
        return sorted(filtered, key=lambda x: x["created_at"], reverse=True)

def _insert_chat_message_local(session_id: str, user_id: str, role: str, content: str) -> dict:
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

def _list_chat_messages_local(session_id: str, user_id: str) -> List[dict]:
    with _local_db_lock:
        filtered = [
            m for m in _local_messages
            if m["session_id"] == session_id and m["user_id"] == user_id
        ]
        return sorted(filtered, key=lambda x: x["created_at"])


# Public Database Access API
def _handle_supabase_error(e: Exception, operation: str):
    global _force_local_db
    err_str = str(e)
    print(f"Supabase error during {operation}: {e}")
    if "42501" in err_str or "401" in err_str or "403" in err_str or "row-level security" in err_str.lower():
        print("\n" + "="*80)
        print("💡 CONFIGURATION WARNING:")
        print("This is a Row Level Security (RLS) violation or unauthorized error.")
        print("Ensure that your backend server/.env uses the Supabase SECRET key (sb_secret_...)")
        print("for the SUPABASE_KEY environment variable, NOT the public Publishable key.")
        print("="*80 + "\n")
    print("Switching database mode to local fallback...")
    _force_local_db = True

async def insert_document(user_id: str, filename: str, parsed_path: str, pdf_hash: str) -> Optional[dict]:
    if not is_supabase_configured():
        return _insert_document_local(user_id, filename, parsed_path, pdf_hash)
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
        _handle_supabase_error(e, "inserting document")
        return _insert_document_local(user_id, filename, parsed_path, pdf_hash)

def insert_document_sync(user_id: str, filename: str, parsed_path: str, pdf_hash: str) -> Optional[dict]:
    if not is_supabase_configured():
        return _insert_document_local(user_id, filename, parsed_path, pdf_hash)
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
        _handle_supabase_error(e, "inserting document (sync)")
        return _insert_document_local(user_id, filename, parsed_path, pdf_hash)

async def list_documents(user_id: str) -> List[dict]:
    if not is_supabase_configured():
        return _list_documents_local(user_id)
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
        _handle_supabase_error(e, "listing documents")
        return _list_documents_local(user_id)

async def create_chat_session(user_id: str, title: str) -> Optional[dict]:
    if not is_supabase_configured():
        return _create_chat_session_local(user_id, title)
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
        _handle_supabase_error(e, "creating chat session")
        return _create_chat_session_local(user_id, title)

async def list_chat_sessions(user_id: str) -> List[dict]:
    if not is_supabase_configured():
        return _list_chat_sessions_local(user_id)
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
        _handle_supabase_error(e, "listing sessions")
        return _list_chat_sessions_local(user_id)

async def insert_chat_message(session_id: str, user_id: str, role: str, content: str) -> Optional[dict]:
    if not is_supabase_configured():
        return _insert_chat_message_local(session_id, user_id, role, content)
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
        _handle_supabase_error(e, "inserting message")
        return _insert_chat_message_local(session_id, user_id, role, content)

async def list_chat_messages(session_id: str, user_id: str) -> List[dict]:
    if not is_supabase_configured():
        return _list_chat_messages_local(session_id, user_id)
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
        _handle_supabase_error(e, "listing messages")
        return _list_chat_messages_local(session_id, user_id)

