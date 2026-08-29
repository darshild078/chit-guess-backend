import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
import socketio

from app.config import settings
from app.errors import AppError
from app.api.v1_router import api_v1_router
from app.sockets.server import sio

# Setup logging
logging.basicConfig(
    level=logging.INFO if not settings.is_dev else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("chitguess")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run automatic schema migration on startup (ensures all tables/columns exist)
    try:
        from migrate_db import migrate
        await migrate()
        logger.info("Database schema verified/migrated on startup.")
    except Exception as e:
        logger.error(f"Startup schema migration warning: {e}")
    yield

# Create FastAPI app
app = FastAPI(
    title="ChitGuess API",
    description="Multiplayer party game backend in Python FastAPI",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_dev else None,
    redoc_url="/redoc" if settings.is_dev else None,
)

# CORS Configuration - permits localhost, 127.0.0.1, LAN IPs, and Vercel domains
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ----------------- Specific & Friendly Exception Handlers -----------------

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "fieldErrors": exc.field_errors,
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    field_errors = {}
    primary_message = "Please check your inputs and try again."

    for err in exc.errors():
        loc = [str(x) for x in err.get("loc", []) if x not in ("body", "query", "path")]
        field_name = loc[-1] if loc else "general"
        msg = err.get("msg", "Invalid input value.")

        # Translate technical validation messages to friendly human text
        if "at least" in msg or "min_length" in msg:
            friendly_msg = f"{field_name.replace('_', ' ').capitalize()} is too short."
        elif "at most" in msg or "max_length" in msg:
            friendly_msg = f"{field_name.replace('_', ' ').capitalize()} is too long."
        elif "missing" in msg:
            friendly_msg = f"{field_name.replace('_', ' ').capitalize()} is required."
        else:
            friendly_msg = msg

        field_errors.setdefault(field_name, []).append(friendly_msg)
        primary_message = friendly_msg

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": primary_message,
                "fieldErrors": field_errors,
            }
        }
    )

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.warning(f"Database Integrity constraint hit: {exc}")
    orig_msg = str(getattr(exc, "orig", exc)).lower()

    if "participant_roomid_displayname_key" in orig_msg or "unique constraint" in orig_msg:
        message = "A player with this name is already in the room. Please choose a different name."
        code = "DUPLICATE_NAME"
    elif "room_code_key" in orig_msg:
        message = "A room with this code already exists. Please try again."
        code = "ROOM_CODE_COLLISION"
    elif "chitmessage_roundid_senderid_key" in orig_msg:
        message = "You have already submitted a secret word for this round."
        code = "ALREADY_SUBMITTED"
    else:
        message = "A conflict occurred with existing room data. Please refresh and try again."
        code = "CONFLICT"

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
            }
        }
    )

@app.exception_handler(OperationalError)
async def operational_error_handler(request: Request, exc: OperationalError):
    logger.error(f"Database connection operational error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "error": {
                "code": "DATABASE_UNAVAILABLE",
                "message": "Database is temporarily reconnecting. Please retry your request in a few seconds.",
            }
        }
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error during request {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "DATABASE_ERROR",
                "message": "Unable to complete database operation. Please try again.",
            }
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred while processing your request. Please try again.",
            }
        }
    )

# ----------------- Routes -----------------

# Top-level un-rate-limited health check for UptimeRobot / Render
@app.get("/health", tags=["Health"])
async def root_health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Mount /api/v1
app.include_router(api_v1_router)

# Wrap FastAPI with Socket.IO ASGI app
app_asgi = socketio.ASGIApp(sio, other_asgi_app=app)
