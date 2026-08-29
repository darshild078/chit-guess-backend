import secrets

# Excludes ambiguous characters (0, O, 1, I)
ALLOWED_ROOM_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
ROOM_CODE_LENGTH = 6

def generate_room_code() -> str:
    """Generate a random 6-character room code."""
    return "".join(secrets.choice(ALLOWED_ROOM_CHARS) for _ in range(ROOM_CODE_LENGTH))

def is_valid_room_code(code: str) -> bool:
    """Validate if the string matches the room code criteria."""
    if not code or len(code) != ROOM_CODE_LENGTH:
        return False
    return all(c in ALLOWED_ROOM_CHARS for c in code.upper())
