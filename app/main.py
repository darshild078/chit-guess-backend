import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import socketio

from app.config import settings
from app.errors import AppError
from app.schemas.common import ApiErrorResponse, ErrorDetail
from app.api.v1_router import api_v1_router
from app.sockets.server import sio

# Setup logging
logging.basicConfig(
    level=logging.INFO if not settings.is_dev else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("chitguess")

# Create FastAPI app
app = FastAPI(
    title="ChitGuess API",
    description="Multiplayer party game backend in Python FastAPI",
    version="1.0.0",
    docs_url="/docs" if settings.is_dev else None,
    redoc_url="/redoc" if settings.is_dev else None,
)

# CORS Configuration
origins = [
    settings.FRONTEND_URL.rstrip("/"),
    "http://localhost:5173",
    "http://localhost:3000",
]
if settings.FRONTEND_URL == "*":
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Global Exception Handlers -----------------

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
    for err in exc.errors():
        field_name = ".".join(str(loc) for loc in err["loc"] if loc not in ("body", "query", "path"))
        if not field_name:
            field_name = "general"
        field_errors[field_name] = [err["msg"]]

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters.",
                "fieldErrors": field_errors,
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
                "message": "Something went wrong on our end. Please try again.",
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
