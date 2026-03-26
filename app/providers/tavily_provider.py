from __future__ import annotations

import httpx

from app.config import get_settings
from app.models.news import NewsItem
from app.models.user import User


class TavilyProvider:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def search_news(self, user: User, request_text: str) -> list[NewsItem]:
        if not self.settings.tavily_api_key:
            return []
        payload = {
            "api_key": self.settings.tavily_api_key,
            "query": self._build_query(user, request_text),
            "topic": "news",
            "max_results": self.settings.recommendation_limit,
            "search_depth": "basic",
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(f"{self.settings.tavily_base_url}/search", json=payload)
                response.raise_for_status()
        except Exception:
            return []

        data = response.json()
        items: list[NewsItem] = []
        for result in data.get("results", []):
            title = result.get("title") or ""
            if not title:
                continue
            items.append(
                NewsItem.from_source(
                    title=title,
                    url=result.get("url") or "",
                    summary=result.get("content") or "",
                    source=result.get("source") or "Tavily",
                    published_at=result.get("published_date") or "",
                )
            )
        return items

    def _build_query(self, user: User, request_text: str) -> str:
        parts = [*user.topics, *user.keywords]
        if request_text:
            parts.append(request_text)
        parts.append("latest news")
        return " ".join(part for part in parts if part)
