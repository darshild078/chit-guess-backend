import re
from app.errors import bad_request

# Single word: letters only (A-Z, a-z), no spaces, 1 to 30 characters
CHIT_WORD_REGEX = re.compile(r"^[a-zA-Z]{1,30}$")

def sanitize_display_name(name: str) -> str:
    """Sanitize and validate player display name."""
    cleaned = (name or "").strip()
    if len(cleaned) < 2 or len(cleaned) > 20:
        raise bad_request("Display name must be between 2 and 20 characters.")
    return cleaned

def sanitize_single_word(body: str) -> str:
    """Validate that chit body is strictly a single word with letters only."""
    cleaned = (body or "").strip()
    if not cleaned:
        raise bad_request("Secret word cannot be empty.")
    if not CHIT_WORD_REGEX.match(cleaned):
        raise bad_request("Secret word must be a single word containing only letters (max 30 letters, no spaces).")
    return cleaned
