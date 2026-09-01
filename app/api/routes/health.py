from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel

class HealthResponseDTO(BaseModel):
    status: str = "ok"
    timestamp: str

router = APIRouter(tags=["Health"])

@router.get("", response_model=HealthResponseDTO)
@router.get("/", response_model=HealthResponseDTO)
async def health_check() -> HealthResponseDTO:
    return HealthResponseDTO(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
