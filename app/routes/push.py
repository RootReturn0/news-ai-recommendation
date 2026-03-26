from fastapi import APIRouter

from app.services.push_service import PushService

router = APIRouter()
push_service = PushService()


@router.post("/check")
async def check_push() -> dict[str, int]:
    return await push_service.push_matching_news()
