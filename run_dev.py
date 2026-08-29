import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app_asgi",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.is_dev,
        log_level=settings.LOG_LEVEL.lower(),
    )
