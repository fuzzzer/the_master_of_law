import json
import uuid
from app.config.settings import settings

def load_api_keys() -> set[str]:
    """Load valid API keys from the JSON file."""
    if not settings.api_keys_file.exists():
        return set()
    try:
        with open(settings.api_keys_file, "r") as f:
            data = json.load(f)
            return set(data.get("keys", []))
    except (json.JSONDecodeError, OSError):
        return set()

def save_api_keys(keys: set[str]):
    """Save API keys to the JSON file."""
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
