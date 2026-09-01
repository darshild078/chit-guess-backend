from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from app.api.main import api_router
from app.api.routes.health import HealthResponseDTO
from app.core.config import settings
from app.core.handlers import register_exception_handlers
from app.core.logging import logger, setup_logging
from app.core.middleware import RequestIdMiddleware
from app.sockets.server import sio

# Initialize structured logging
setup_logging(settings.LOG_LEVEL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ChitGuess API server...")
    yield
    logger.info("Shutting down ChitGuess API server...")

# Create FastAPI application
app = FastAPI(
    title="ChitGuess API",
    description="Multiplayer party game backend in Python FastAPI",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_dev else None,
    redoc_url="/redoc" if settings.is_dev else None,
)

# Add Request ID correlation middleware
app.add_middleware(RequestIdMiddleware)

# Explicit CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if not settings.is_dev else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Register global standardized exception handlers
register_exception_handlers(app)

# Root un-rate-limited health check
@app.get("/health", tags=["Health"], response_model=HealthResponseDTO)
async def root_health_check() -> HealthResponseDTO:
    return HealthResponseDTO(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

# Mount /api/v1 router
app.include_router(api_router)

# Wrap FastAPI with Socket.IO ASGI app
app_asgi = socketio.ASGIApp(sio, other_asgi_app=app)
