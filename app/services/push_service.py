from pathlib import Path

from app.bot.formatter import format_news_item
from app.config import get_settings
from app.models.news import NewsItem
from app.models.user import User
from app.providers.rss_provider import RSSProvider
from app.providers.telegram_provider import TelegramProvider
from app.services.personalization_service import PersonalizationService
from app.services.user_settings_service import user_settings_service


class PushService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.rss_provider = RSSProvider()
        self.telegram_provider = TelegramProvider()
        self.personalization_service = PersonalizationService()

    async def push_matching_news(self) -> dict[str, int]:
        users = user_settings_service.get_all_users()
        if not users:
            return {"users": 0, "sent": 0}

        items = self._load_mock_feed_items()
        sent = 0
        for user in users:
            sent += await self._push_for_user(user, items)
        return {"users": len(users), "sent": sent}

    async def _push_for_user(self, user: User, items: list[NewsItem]) -> int:
        ranked = self.personalization_service._rank_items(user, "rss push", items)
        matching = [item for item in ranked if item.score > 0 and item.id not in set(user.pushed_news_ids)]
        if not matching:
            return 0

        sent = 0
        for item in matching:
            text = format_news_item(sent + 1, item)
            message_id = await self.telegram_provider.send_message(chat_id=user.chat_id, text=text)
            if message_id:
                user_settings_service.record_sent_message(user.chat_id, message_id, text)
            user_settings_service.mark_news_pushed(user.chat_id, user.user_id, item.id)
            sent += 1
        return sent

    def _load_mock_feed_items(self) -> list[NewsItem]:
        rss_dir = Path(self.settings.rss_data_dir)
        items: list[NewsItem] = []
        for path in sorted(rss_dir.glob("*.xml")):
            items.extend(self.rss_provider.load_file(path))
        return items
