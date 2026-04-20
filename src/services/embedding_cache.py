"""Embedding cache service to avoid redundant OpenAI API calls."""

import json
import hashlib
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "embeddings"
CACHE_FILE = CACHE_DIR / "embeddings_cache.json"


def ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _hash_text(text: str) -> str:
    """Generate hash of text for cache key."""
    return hashlib.md5(text.encode()).hexdigest()


def get_cached_embedding(text: str) -> list | None:
    """Retrieve embedding from cache if exists."""
    ensure_cache_dir()

    if not CACHE_FILE.exists():
        return None

    try:
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)

        text_hash = _hash_text(text)
        return cache.get(text_hash)
    except Exception:
        return None


def save_embedding_to_cache(text: str, embedding: list) -> None:
    """Save embedding to local cache."""
    ensure_cache_dir()

    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
        else:
            cache = {}

        text_hash = _hash_text(text)
        cache[text_hash] = embedding

        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)
    except Exception as e:
        print(f"Warning: Could not save embedding to cache: {e}")


def get_cache_stats() -> dict:
    """Get cache statistics."""
    ensure_cache_dir()

    if not CACHE_FILE.exists():
        return {"total_cached": 0, "cache_size_mb": 0}

    try:
        cache_size = CACHE_FILE.stat().st_size / (1024 * 1024)
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)

        return {
            "total_cached": len(cache),
            "cache_size_mb": round(cache_size, 2)
        }
    except Exception:
        return {"total_cached": 0, "cache_size_mb": 0}
