from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.rooms import router as rooms_router
from app.api.submissions import router as submissions_router
from app.api.inbox import router as inbox_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health_router, prefix="/health")
api_v1_router.include_router(rooms_router)
api_v1_router.include_router(submissions_router)
api_v1_router.include_router(inbox_router)
