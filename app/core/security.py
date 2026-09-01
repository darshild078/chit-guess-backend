import time
from typing import Any, Dict
import jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedException

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_SECONDS = 24 * 60 * 60  # 24 hours

def sign_participant_token(participant_id: str, room_id: str, role: str, session_version: int) -> str:
    now = int(time.time())
    payload = {
        "participantId": participant_id,
        "roomId": room_id,
        "role": role,
        "sessionVersion": session_version,
        "iat": now,
        "exp": now + JWT_EXPIRATION_SECONDS,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_participant_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("Your session has expired. Please rejoin the room.")
    except jwt.InvalidTokenError:
        raise UnauthorizedException("Please join or create a room to continue.")
