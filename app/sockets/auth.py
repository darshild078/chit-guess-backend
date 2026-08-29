from typing import Optional, Dict, Any
from urllib.parse import parse_qs
from app.utils.jwt_helper import verify_participant_token

def authenticate_socket(environ: dict, auth: Optional[dict] = None) -> Optional[Dict[str, Any]]:
    """
    Extract token from socket auth payload, query params, or cookie,
    and verify participant session.
    """
    token = None
    if auth and isinstance(auth, dict) and "token" in auth:
        token = auth["token"]

    if not token:
        # Check query string
        query_string = environ.get("QUERY_STRING", "")
        if query_string:
            params = parse_qs(query_string)
            if "token" in params and params["token"]:
                token = params["token"][0]

    if not token:
        # Check HTTP headers / cookies
        http_cookie = environ.get("HTTP_COOKIE", "")
        if "token=" in http_cookie:
            for part in http_cookie.split(";"):
                part = part.strip()
                if part.startswith("token="):
                    token = part[6:]
                    break

    if not token:
        return None

    try:
        payload = verify_participant_token(token)
        return payload
    except Exception:
        return None
