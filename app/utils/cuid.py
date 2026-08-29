import uuid
import secrets
import string

def generate_cuid() -> str:
    """Generate a clean random CUID-like alphanumeric ID."""
    prefix = "c"
    random_part = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(24))
    return f"{prefix}{random_part}"

def generate_opaque_id() -> str:
    """Generate an opaque random ID for anonymous card assignments."""
    return f"opq_{uuid.uuid4().hex}"
