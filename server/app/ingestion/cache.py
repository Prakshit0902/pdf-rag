import os
import json
import hashlib
from typing import Optional, Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE_DIR = os.path.join(BASE_DIR, "data", "cache")

os.makedirs(CACHE_DIR, exist_ok=True)


def _get_manifest_path(user_id: str) -> str:
    user_cache_dir = os.path.join(CACHE_DIR, user_id)
    os.makedirs(user_cache_dir, exist_ok=True)
    return os.path.join(user_cache_dir, "manifest.json")


def _load_manifest(user_id: str) -> Dict[str, Any]:
    path = _get_manifest_path(user_id)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}


def _save_manifest(manifest: Dict[str, Any], user_id: str):
    path = _get_manifest_path(user_id)
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)


def compute_file_hash(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_bytes_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get_cached_entry(file_hash: str, user_id: str = "default_tenant") -> Optional[Dict[str, Any]]:
    manifest = _load_manifest(user_id)
    return manifest.get(file_hash)


def set_cached_entry(file_hash: str, filename: str, parsed_path: str, user_id: str = "default_tenant"):
    manifest = _load_manifest(user_id)
    manifest[file_hash] = {
        "filename": filename,
        "parsed_path": parsed_path,
        "indexed_at": None,
    }
    _save_manifest(manifest, user_id)


def mark_indexed(file_hash: str, user_id: str = "default_tenant"):
    manifest = _load_manifest(user_id)
    entry = manifest.get(file_hash)
    if entry:
        from datetime import datetime
        entry["indexed_at"] = datetime.utcnow().isoformat()
        _save_manifest(manifest, user_id)


def is_cached(file_hash: str, user_id: str = "default_tenant") -> bool:
    entry = get_cached_entry(file_hash, user_id)
    if not entry:
        return False
    parsed_path = entry.get("parsed_path", "")
    filename = entry.get("filename", "")
    # Check if both the parsed output path and original PDF file exist on disk
    pdf_path = os.path.join(BASE_DIR, "data", "cleaned_pdfs", user_id, filename) if filename else ""
    
    if os.path.exists(parsed_path) and (not pdf_path or os.path.exists(pdf_path)):
        return True
    return False


def delete_cache_by_filename(filename: str, user_id: str = "default_tenant"):
    manifest = _load_manifest(user_id)
    keys_to_delete = [
        k for k, v in manifest.items()
        if v.get("filename") == filename
    ]
    for k in keys_to_delete:
        del manifest[k]
    if keys_to_delete:
        _save_manifest(manifest, user_id)
