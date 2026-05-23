import os
import asyncio
from typing import List, Dict, Optional
from app.vectorstore.supabase_client import is_supabase_configured, insert_chat_message, list_chat_messages

# Local fallback in-memory history: {(user_id, session_id): [{"role": role, "content": content}]}
_local_history: Dict[tuple, List[dict]] = {}

MAX_HISTORY = 5

async def add_message_async(role: str, content: str, user_id: str = "default_tenant", session_id: Optional[str] = None):
    """Adds a message to history, asynchronously writing to database if configured."""
    key = (user_id, session_id or "default_session")
    if key not in _local_history:
        _local_history[key] = []
    
    _local_history[key].append({"role": role, "content": content})
    if len(_local_history[key]) > MAX_HISTORY:
        _local_history[key].pop(0)

    if session_id and session_id != "default_session":
        try:
            await insert_chat_message(session_id, user_id, role, content)
        except Exception as e:
            print(f"Failed to persist chat message: {e}")

def add_message(role: str, content: str, user_id: str = "default_tenant", session_id: Optional[str] = None):
    """Sync wrapper for adding a message."""
    key = (user_id, session_id or "default_session")
    if key not in _local_history:
        _local_history[key] = []
    
    _local_history[key].append({"role": role, "content": content})
    if len(_local_history[key]) > MAX_HISTORY:
        _local_history[key].pop(0)

    if session_id and session_id != "default_session":
        try:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                loop.create_task(insert_chat_message(session_id, user_id, role, content))
            else:
                asyncio.run(insert_chat_message(session_id, user_id, role, content))
        except Exception as e:
            print(f"Failed to persist chat message (sync): {e}")

async def get_history_async(user_id: str = "default_tenant", session_id: Optional[str] = None) -> List[dict]:
    """Retrieves conversation history asynchronously from database or local memory."""
    if session_id and session_id != "default_session":
        try:
            messages = await list_chat_messages(session_id, user_id)
            return [{"role": m["role"], "content": m["content"]} for m in messages][-MAX_HISTORY:]
        except Exception as e:
            print(f"Failed to fetch history: {e}")
    
    key = (user_id, session_id or "default_session")
    return _local_history.get(key, [])

def get_history(user_id: str = "default_tenant", session_id: Optional[str] = None) -> List[dict]:
    """Sync wrapper for retrieving conversation history."""
    if session_id and session_id != "default_session":
        try:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # Avoid blocking the event loop synchronously; fallback to local history
                pass
            else:
                messages = asyncio.run(list_chat_messages(session_id, user_id))
                return [{"role": m["role"], "content": m["content"]} for m in messages][-MAX_HISTORY:]
        except Exception as e:
            print(f"Failed to fetch history (sync): {e}")
            
    key = (user_id, session_id or "default_session")
    return _local_history.get(key, [])