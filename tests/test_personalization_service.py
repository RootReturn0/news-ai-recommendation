import asyncio

from app.models.news import NewsItem
from app.models.user import User
from app.services.personalization_service import PersonalizationService


def test_personalization_prefers_matching_keywords() -> None:
    service = PersonalizationService()
    user = User(chat_id=1, user_id=1, topics=["AI"], keywords=["OpenAI"])
    items = [
        NewsItem.from_source(title="Sports roundup", summary="Football results"),
        NewsItem.from_source(title="OpenAI ships new model", summary="AI update for developers"),
    ]
    ranked = service._rank_items(user, "today", items)
    assert ranked[0].title == "OpenAI ships new model"


def test_hot_news_returns_items() -> None:
    service = PersonalizationService()
    user = User(chat_id=1, user_id=1)
    items = asyncio.run(service.get_hot_news(user))
    assert items
