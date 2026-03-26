from openai import OpenAI

from app.config import get_settings
from app.models.news import NewsItem
from app.models.user import User


class LLMService:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.openai_model
        self.client = None
        if settings.resolved_openai_api_key:
            self.client = OpenAI(
                api_key=settings.resolved_openai_api_key,
                base_url=settings.resolved_openai_base_url,
            )

    async def summarize_news(self, user: User, request_text: str, items: list[NewsItem]) -> str:
        if not items:
            return "I could not find strong matches yet."
        if not self.client:
            return self._fallback_summary(user, request_text, items)
        prompt = self._build_prompt(user, request_text, items)
        try:
            response = self.client.responses.create(model=self.model, input=prompt)
            text = getattr(response, "output_text", "").strip()
            return text or self._fallback_summary(user, request_text, items)
        except Exception:
            return self._fallback_summary(user, request_text, items)

    async def summarize_hot_news(self, user: User, items: list[NewsItem]) -> str:
        if not items:
            return "There are no hot items available right now."
        return await self.summarize_news(user=user, request_text="hot news", items=items)

    def _build_prompt(self, user: User, request_text: str, items: list[NewsItem]) -> str:
        lines = [
            "Summarize why these news items matter for the user in 1-2 sentences.",
            f"Topics: {', '.join(user.topics) or 'none'}",
            f"Keywords: {', '.join(user.keywords) or 'none'}",
            f"Request: {request_text or 'none'}",
            "Items:",
        ]
        for item in items[:5]:
            lines.append(f"- {item.title}: {item.summary}")
        return "\n".join(lines)

    def _fallback_summary(self, user: User, request_text: str, items: list[NewsItem]) -> str:
        pieces: list[str] = []
        if user.topics:
            pieces.append(f"These picks lean toward your topics: {', '.join(user.topics[:3])}.")
        if user.keywords:
            pieces.append(f"They also reflect your keyword focus: {', '.join(user.keywords[:3])}.")
        if request_text:
            pieces.append(f"They are filtered around your request: {request_text}.")
        if not pieces:
            pieces.append("These are the strongest items from the current feed.")
        return " ".join(pieces)
