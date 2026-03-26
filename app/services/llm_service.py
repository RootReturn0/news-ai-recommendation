import json
from pathlib import Path

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

    async def extract_keywords_from_liked_news(self, reply_text: str, existing_keywords: list[str]) -> list[str]:
        if not reply_text.strip():
            return []
        if not self.client:
            return self._fallback_extract_keywords(reply_text, existing_keywords)

        prompt = self._build_keyword_extraction_prompt(reply_text, existing_keywords)
        try:
            response = self.client.responses.create(model=self.model, input=prompt)
            text = getattr(response, "output_text", "").strip()
            keywords = self._parse_keywords_response(text)
            return keywords or self._fallback_extract_keywords(reply_text, existing_keywords)
        except Exception:
            return self._fallback_extract_keywords(reply_text, existing_keywords)

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

    def _build_keyword_extraction_prompt(self, reply_text: str, existing_keywords: list[str]) -> str:
        template = self._load_prompt("extract_keywords.txt")
        return template.format(
            existing_keywords=", ".join(existing_keywords) or "none",
            reply_text=reply_text,
        )

    def _load_prompt(self, filename: str) -> str:
        path = Path("app/prompts") / filename
        return path.read_text(encoding="utf-8")

    def _parse_keywords_response(self, text: str) -> list[str]:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        keywords: list[str] = []
        seen: set[str] = set()
        for item in data:
            if not isinstance(item, str):
                continue
            keyword = item.strip()
            if not keyword:
                continue
            lowered = keyword.lower()
            if lowered in seen:
                continue
            keywords.append(keyword)
            seen.add(lowered)
        return keywords[:5]

    def _fallback_extract_keywords(self, reply_text: str, existing_keywords: list[str]) -> list[str]:
        import re

        title = ""
        for line in reply_text.splitlines():
            stripped = line.strip()
            if stripped and stripped[0].isdigit() and ". " in stripped:
                title = stripped.split(". ", 1)[1]
                break
        if not title:
            title = reply_text

        stopwords = {
            "the",
            "and",
            "for",
            "with",
            "from",
            "this",
            "that",
            "why",
            "source",
            "link",
            "today",
            "launches",
            "launch",
            "new",
            "feature",
            "features",
            "startup",
            "startups",
            "major",
            "developer",
            "developers",
            "model",
            "release",
            "tool",
            "tools",
        }
        seen = {item.lower() for item in existing_keywords}
        keywords: list[str] = []
        for match in re.findall(r"[A-Za-z][A-Za-z0-9\-\+\.]{2,}", title):
            lowered = match.lower()
            if lowered in stopwords or lowered in seen:
                continue
            if match.islower():
                continue
            keywords.append(match)
            seen.add(lowered)
        return keywords[:5]

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
