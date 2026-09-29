"""Optional Redis cache. Degrades silently when Redis is unavailable (spec 82)."""
import json
from typing import Any

from app.core.config import get_settings

_client = None


def get_redis():
    global _client
    if _client is None:
        try:
            import redis
            _client = redis.Redis.from_url(get_settings().REDIS_URL, decode_responses=True)
            _client.ping()
        except Exception:
            _client = False
    return _client or None


def cache_get(key: str) -> Any | None:
    r = get_redis()
    if not r:
        return None
    try:
        raw = r.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    r = get_redis()
    if not r:
        return
    try:
        r.setex(key, ttl, json.dumps(value))
    except Exception:
        pass
