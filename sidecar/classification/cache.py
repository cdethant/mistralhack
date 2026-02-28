"""
Phrase cache: avoids redundant TTS API calls for common messages.
Uses an LRU cache keyed on (sender_name, status, activity_summary).
"""
import hashlib
from cachetools import LRUCache
from threading import Lock

_cache: LRUCache = LRUCache(maxsize=20)
_lock = Lock()

# Pre-baked template variations (never expire, always served from cache)
PREGENERATED_KEYS: set[str] = set()


def _cache_key(sender_name: str, status: str, activity_summary: str) -> str:
    raw = f"{sender_name.lower()}|{status}|{activity_summary.lower()[:50]}"
    return hashlib.md5(raw.encode()).hexdigest()


def get_cached(sender_name: str, status: str, activity_summary: str):
    """Returns (audio_b64, duration, message_text) or None if cache miss."""
    key = _cache_key(sender_name, status, activity_summary)
    with _lock:
        return _cache.get(key)


def put_cache(sender_name: str, status: str, activity_summary: str, value: tuple):
    """Cache (audio_b64, duration, message_text) for the given inputs."""
    key = _cache_key(sender_name, status, activity_summary)
    with _lock:
        _cache[key] = value


def cache_stats() -> dict:
    with _lock:
        return {
            "size": len(_cache),
            "maxsize": _cache.maxsize,
            "hit_rate_approx": f"{len(_cache)}/{_cache.maxsize}",
        }
