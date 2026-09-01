import re
from app.core.constants import MAX_DISPLAY_NAME_LEN, MIN_DISPLAY_NAME_LEN
from app.core.exceptions import BadRequestException

# Single word: letters only (A-Z, a-z), no spaces, 1 to 30 characters
CHIT_WORD_REGEX = re.compile(r"^[a-zA-Z]{1,30}$")

def sanitize_display_name(name: str) -> str:
    """Sanitize and validate player display name."""
    cleaned = (name or "").strip()
    if len(cleaned) < MIN_DISPLAY_NAME_LEN or len(cleaned) > MAX_DISPLAY_NAME_LEN:
        raise BadRequestException(f"Display name must be between {MIN_DISPLAY_NAME_LEN} and {MAX_DISPLAY_NAME_LEN} characters.")
    return cleaned

def sanitize_single_word(body: str) -> str:
    """Validate that chit body is strictly a single word with letters only."""
    cleaned = (body or "").strip()
    if not cleaned:
        raise BadRequestException("Secret word cannot be empty.")
    if not CHIT_WORD_REGEX.match(cleaned):
        raise BadRequestException("Secret word must be a single word containing only letters (max 30 letters, no spaces).")
    return cleaned
