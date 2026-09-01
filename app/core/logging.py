import logging
import sys

def setup_logging(level: str = "INFO") -> logging.Logger:
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
    return logging.getLogger("chitguess")

logger = logging.getLogger("chitguess")

def log_event(
    action: str,
    status: str = "success",
    message: str = "",
    request_id: str | None = None,
    user_id: str | None = None,
    room_id: str | None = None,
    level: int = logging.INFO,
    **extra: object,
) -> None:
    parts = [
        f"action={action}",
        f"status={status}",
    ]
    if request_id:
        parts.insert(0, f"request_id={request_id}")
    if user_id:
        parts.append(f"user_id={user_id}")
    if room_id:
        parts.append(f"room_id={room_id}")
    for k, v in extra.items():
        if v is not None:
            parts.append(f"{k}={v}")
    if message:
        parts.append(f'message="{message}"')
    logger.log(level, " ".join(parts))
