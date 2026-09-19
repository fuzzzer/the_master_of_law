import json
import uuid
from app.config.settings import settings

_API_KEYS_CACHE = None
_LAST_LOADED_FILE = None

def load_api_keys() -> set[str]:
    """Load valid API keys from the JSON file."""
    global _API_KEYS_CACHE, _LAST_LOADED_FILE
    # Bypass cache in test environment to avoid mock-settings pollution
    is_test = settings.app_env == "test" or "Mock" in type(settings.api_keys_file).__name__ or "Mock" in type(settings).__name__
    if not is_test and _API_KEYS_CACHE is not None and _LAST_LOADED_FILE == settings.api_keys_file:
        return _API_KEYS_CACHE
    _LAST_LOADED_FILE = settings.api_keys_file
    if not settings.api_keys_file.exists():
        _API_KEYS_CACHE = set()
        return _API_KEYS_CACHE
    try:
        with open(settings.api_keys_file, "r") as f:
            data = json.load(f)
            _API_KEYS_CACHE = set(data.get("keys", []))
            return _API_KEYS_CACHE
    except (json.JSONDecodeError, OSError):
        _API_KEYS_CACHE = set()
        return _API_KEYS_CACHE

def save_api_keys(keys: set[str]):
    """Save API keys to the JSON file."""
    global _API_KEYS_CACHE
    _API_KEYS_CACHE = set(keys)
    with open(settings.api_keys_file, "w") as f:
        json.dump({"keys": list(keys)}, f, indent=2)

def is_valid_api_key(api_key: str) -> bool:
    """Check if the provided API key is valid."""
    keys = load_api_keys()
    return api_key in keys

def generate_api_key() -> str:
    """Generate and store a new API key."""
    new_key = f"sk_{uuid.uuid4().hex}"
    keys = load_api_keys()
    keys.add(new_key)
    save_api_keys(keys)
    return new_key

