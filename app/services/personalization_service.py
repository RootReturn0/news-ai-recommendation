from app.config import get_settings
from app.models.news import NewsItem
from app.models.user import User
from app.providers.mock_news_provider import MockNewsProvider
from app.providers.rss_provider import RSSProvider
from app.providers.tavily_provider import TavilyProvider


class PersonalizationService:
    def __init__(self) -> None:
        settings = get_settings()
        self.limit = settings.recommendation_limit
        self.tavily_provider = TavilyProvider()
        self.rss_provider = RSSProvider()
        self.mock_provider = MockNewsProvider(self.rss_provider)

    async def get_personalized_news(self, user: User, request_text: str) -> list[NewsItem]:
        items = await self.tavily_provider.search_news(user=user, request_text=request_text)
        return self._rank_items(user, request_text, items)[: self.limit]

    async def get_hot_news(self, user: User) -> list[NewsItem]:
        items = self.mock_provider.get_hot_news()
        return self._rank_items(user, "hot news", items)[: self.limit]

    def _rank_items(self, user: User, request_text: str, items: list[NewsItem]) -> list[NewsItem]:
        request_terms = [term.lower() for term in request_text.split() if term]
        topic_terms = [topic.lower() for topic in user.topics]
        keyword_terms = [keyword.lower() for keyword in user.keywords]
        ranked: list[tuple[int, NewsItem]] = []
        for item in items:
            haystack = " ".join(filter(None, [item.title, item.summary, item.source])).lower()
            score = 0
            score += sum(3 for topic in topic_terms if topic in haystack)
            score += sum(4 for keyword in keyword_terms if keyword in haystack)
            score += sum(1 for term in request_terms if term in haystack)
            if score == 0 and not (topic_terms or keyword_terms or request_terms):
                score = 1
            enriched = item.model_copy()
            enriched.score = score
            enriched.reason = self._build_reason(enriched, user, request_text)
            ranked.append((score, enriched))
        ranked.sort(key=lambda pair: (pair[0], pair[1].published_at or ""), reverse=True)
        return [item for _, item in ranked]

    def _build_reason(self, item: NewsItem, user: User, request_text: str) -> str:
        matches: list[str] = []
        haystack = " ".join(filter(None, [item.title, item.summary, item.source])).lower()
        for topic in user.topics:
            if topic.lower() in haystack:
                matches.append(topic)
        for keyword in user.keywords:
            if keyword.lower() in haystack:
                matches.append(keyword)
        if matches:
            unique = ", ".join(dict.fromkeys(matches))
            return f"Matches your interests in {unique}."
        if request_text:
            return f"Relevant to your current request: {request_text}."
        return "One of the strongest items in the current feed."
