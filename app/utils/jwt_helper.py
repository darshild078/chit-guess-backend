import time
import jwt
from typing import Dict, Any, Optional
from app.config import settings
from app.errors import unauthorized

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_SECONDS = 24 * 60 * 60  # 24 hours

def sign_participant_token(participant_id: str, room_id: str, role: str, session_version: int) -> str:
    """Sign a JWT for participant session."""
    now = int(time.time())
    payload = {
        "participantId": participant_id,
        "roomId": room_id,
        "role": role,
        "sessionVersion": session_version,
        "iat": now,
        "exp": now + JWT_EXPIRATION_SECONDS
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_participant_token(token: str) -> Dict[str, Any]:
    """Verify and decode participant JWT."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise unauthorized("Your session has expired. Please rejoin the room.")
    except jwt.InvalidTokenError:
        raise unauthorized("Please join or create a room to continue.")
