from app.bot.formatter import format_news_results, format_settings
from app.models.news import NewsItem
from app.models.user import User


def test_format_settings() -> None:
    user = User(chat_id=1, user_id=1, topics=["AI"], keywords=["OpenAI"])
    text = format_settings(user)
    assert "AI" in text
    assert "OpenAI" in text


def test_format_news_results() -> None:
    item = NewsItem.from_source(title="OpenAI launches feature", url="https://example.com", source="Example")
    item.reason = "Matches your interests in AI."
    text = format_news_results("Top picks", "A short summary.", [item])
    assert "Why it matters:" in text
    assert "Source:" in text
