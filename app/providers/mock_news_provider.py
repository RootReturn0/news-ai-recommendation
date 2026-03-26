from app.models.news import NewsItem
from app.providers.rss_provider import RSSProvider


class MockNewsProvider:
    def __init__(self, rss_provider: RSSProvider) -> None:
        self.rss_provider = rss_provider

    def get_hot_news(self) -> list[NewsItem]:
        return self.rss_provider.load_all()
