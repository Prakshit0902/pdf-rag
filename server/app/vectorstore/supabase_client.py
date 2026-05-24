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

def _create_chat_session_local(user_id: str, title: str, filename: Optional[str] = None) -> dict:
    with _local_db_lock:
        session = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": title,
            "filename": filename,
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

async def create_chat_session(user_id: str, title: str, filename: Optional[str] = None) -> Optional[dict]:
    if not is_supabase_configured():
        return _create_chat_session_local(user_id, title, filename)
    try:
        headers = await _get_client_headers()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/chat_sessions",
                headers=headers,
                json={
                    "user_id": user_id,
                    "title": title,
                    "filename": filename
                }
            )
            resp.raise_for_status()
            data = resp.json()
            return data[0] if isinstance(data, list) and data else data
    except Exception as e:
        _handle_supabase_error(e, "creating chat session")
        return _create_chat_session_local(user_id, title, filename)

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


def _delete_document_local(user_id: str, filename: str) -> None:
    global _local_documents
    with _local_db_lock:
        _local_documents = [
            d for d in _local_documents
            if not (d["user_id"] == user_id and d["filename"] == filename)
        ]


def _delete_chat_sessions_by_file_local(user_id: str, filename: str) -> None:
    global _local_sessions, _local_messages
    with _local_db_lock:
        session_ids = [
            s["id"] for s in _local_sessions
            if s["user_id"] == user_id and s.get("filename") == filename
        ]
        if session_ids:
            _local_sessions = [
                s for s in _local_sessions
                if s["id"] not in session_ids
            ]
            _local_messages = [
                m for m in _local_messages
                if m["session_id"] not in session_ids
            ]


async def delete_document(user_id: str, filename: str) -> bool:
    if not is_supabase_configured():
        _delete_document_local(user_id, filename)
        return True
    try:
        headers = {
            "apikey": SUPABASE_KEY or "",
            "Authorization": f"Bearer {SUPABASE_KEY or ''}"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{SUPABASE_URL}/rest/v1/user_documents?user_id=eq.{user_id}&filename=eq.{filename}",
                headers=headers
            )
            resp.raise_for_status()
            return True
    except Exception as e:
        _handle_supabase_error(e, "deleting document")
        _delete_document_local(user_id, filename)
        return True


async def delete_chat_sessions_by_file(user_id: str, filename: str) -> bool:
    if not is_supabase_configured():
        _delete_chat_sessions_by_file_local(user_id, filename)
        return True
    try:
        headers = {
            "apikey": SUPABASE_KEY or "",
            "Authorization": f"Bearer {SUPABASE_KEY or ''}"
        }
        async with httpx.AsyncClient() as client:
            # 1. Retrieve IDs of sessions to delete
            resp = await client.get(
                f"{SUPABASE_URL}/rest/v1/chat_sessions?user_id=eq.{user_id}&filename=eq.{filename}&select=id",
                headers=headers
            )
            resp.raise_for_status()
            sessions = resp.json()
            session_ids = [s["id"] for s in sessions]
            
            if session_ids:
                # 2. Delete messages first
                ids_str = ",".join(session_ids)
                await client.delete(
                    f"{SUPABASE_URL}/rest/v1/chat_messages?session_id=in.({ids_str})",
                    headers=headers
                )
                # 3. Delete sessions
                await client.delete(
                    f"{SUPABASE_URL}/rest/v1/chat_sessions?user_id=eq.{user_id}&filename=eq.{filename}",
                    headers=headers
                )
            return True
    except Exception as e:
        _handle_supabase_error(e, "deleting chat sessions by file")
        _delete_chat_sessions_by_file_local(user_id, filename)
        return True

