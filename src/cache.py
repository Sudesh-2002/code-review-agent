import hashlib
import json
import os
from src.logger import get_logger

logger = get_logger("cache")

os.makedirs("cache", exist_ok=True)
CACHE_FILE = "cache/reviews.json"

def _load_cache() -> dict:
    if not os.path.exists(CACHE_FILE):
        return {}
    with open(CACHE_FILE, "r") as f:
        return json.load(f)

def _save_cache(data: dict):
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_cache_key(filename: str, patch: str) -> str:
    """Generate unique key based on filename + patch content"""
    content = f"{filename}:{patch}"
    return hashlib.sha256(content.encode()).hexdigest()

def get_cached_review(filename: str, patch: str):
    """Return cached review if patch hasn't changed"""
    key = get_cache_key(filename, patch)
    cache = _load_cache()

    if key in cache:
        logger.info(f"Cache HIT for {filename} — skipping AI call")
        return cache[key]["review"]

    logger.debug(f"Cache MISS for {filename}")
    return None

def save_review_to_cache(filename: str, patch: str, review: str):
    """Save a review result to cache"""
    key = get_cache_key(filename, patch)
    cache = _load_cache()
    cache[key] = {"filename": filename, "review": review}
    _save_cache(cache)
    logger.debug(f"Cached review for {filename}")

def clear_cache():
    """Wipe all cached reviews"""
    _save_cache({})
    logger.info("Cache cleared")