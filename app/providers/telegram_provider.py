import httpx

from app.config import get_settings


class TelegramProvider:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def send_message(self, chat_id: int, text: str) -> None:
        if not self.settings.tg_bot_token:
            return
        url = f"{self.settings.tg_api_base}/bot{self.settings.tg_bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                await client.post(url, json=payload)
        except Exception:
            return
