from fastapi import APIRouter

from app.schemas.response import SuccessResponse

router = APIRouter()


@router.get("/health")
async def health_check() -> SuccessResponse[dict[str, bool]]:
    return SuccessResponse(data={"status": True})
