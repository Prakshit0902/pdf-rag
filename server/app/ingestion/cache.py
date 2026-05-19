import os
import json
import hashlib
from typing import Optional, Dict, Any

CACHE_DIR = "data/cache"
MANIFEST_PATH = os.path.join(CACHE_DIR, "manifest.json")

os.makedirs(CACHE_DIR, exist_ok=True)


def _load_manifest() -> Dict[str, Any]:
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r") as f:
            return json.load(f)
    return {}


def _save_manifest(manifest: Dict[str, Any]):
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)


def compute_file_hash(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_bytes_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get_cached_entry(file_hash: str) -> Optional[Dict[str, Any]]:
    manifest = _load_manifest()
    return manifest.get(file_hash)


def set_cached_entry(file_hash: str, filename: str, parsed_path: str):
    manifest = _load_manifest()
    manifest[file_hash] = {
        "filename": filename,
        "parsed_path": parsed_path,
        "indexed_at": None,
    }
    _save_manifest(manifest)


def mark_indexed(file_hash: str):
    manifest = _load_manifest()
    entry = manifest.get(file_hash)
    if entry:
        from datetime import datetime
        entry["indexed_at"] = datetime.utcnow().isoformat()
        _save_manifest(manifest)


def is_cached(file_hash: str) -> bool:
    entry = get_cached_entry(file_hash)
    if entry and os.path.exists(entry.get("parsed_path", "")):
        return True
    return False
