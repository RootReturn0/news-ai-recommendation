from typing import Any

from fastapi import APIRouter

from app.bot.handlers import handle_update

router = APIRouter()


@router.post("/webhook")
async def telegram_webhook(update: dict[str, Any]) -> dict[str, object]:
    message = await handle_update(update)
    return {"ok": True, "message": message}


@router.post("/debug")
async def telegram_debug(update: dict[str, Any]) -> dict[str, object]:
    message = await handle_update(update, send_reply=False)
    return {"ok": True, "message": message}
