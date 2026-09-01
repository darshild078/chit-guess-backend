from fastapi import APIRouter

from app.api.routes.guesses import router as guesses_router
from app.api.routes.health import router as health_router
from app.api.routes.inbox import router as inbox_router
from app.api.routes.rooms import router as rooms_router
from app.api.routes.submissions import router as submissions_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router, prefix="/health")
api_router.include_router(rooms_router)
api_router.include_router(submissions_router)
api_router.include_router(inbox_router)
api_router.include_router(guesses_router)
