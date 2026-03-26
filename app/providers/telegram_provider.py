import httpx

from app.config import get_settings


class TelegramProvider:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def send_message(self, chat_id: int, text: str) -> int | None:
        if not self.settings.tg_bot_token:
            return None
        url = f"{self.settings.tg_api_base}/bot{self.settings.tg_bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(url, json=payload)
                data = response.json()
        except Exception:
            return None
        result = data.get("result") if isinstance(data, dict) else None
        message_id = result.get("message_id") if isinstance(result, dict) else None
        return message_id if isinstance(message_id, int) else None
