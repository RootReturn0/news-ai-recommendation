from collections import defaultdict
from pathlib import Path

from app.models.user import User


def _parse_csv(value: str) -> list[str]:
    if not value:
        return []
    items: list[str] = []
    seen: set[str] = set()
    for chunk in value.split(","):
        item = chunk.strip()
        key = item.lower()
        if item and key not in seen:
            items.append(item)
            seen.add(key)
    return items


class UserSettingsService:
    def __init__(self) -> None:
        self._users: dict[tuple[int, int], User] = {}
        self._feedback: defaultdict[tuple[int, int], list[dict[str, str]]] = defaultdict(list)
        self._sent_messages: dict[tuple[int, int], str] = {}
        self._users_dir = Path("data/users")
        self._sent_messages_dir = Path("data/sent_messages")
        self._users_dir.mkdir(parents=True, exist_ok=True)
        self._sent_messages_dir.mkdir(parents=True, exist_ok=True)

    def get_or_create_user(self, chat_id: int, user_id: int, username: str | None = None) -> User:
        key = (chat_id, user_id)
        if key in self._users:
            user = self._users[key]
            if username and user.username != username:
                user.username = username
                user.updated_at = _utcnow()
                self._save_user(user)
            return user

        user = self._load_user(chat_id, user_id)
        if user is None:
            user = User(chat_id=chat_id, user_id=user_id, username=username)
            self._save_user(user)
        elif username and user.username != username:
            user.username = username
            user.updated_at = _utcnow()
            self._save_user(user)

        self._users[key] = user
        return user

    def update_topics(self, chat_id: int, user_id: int, raw_value: str, username: str | None = None) -> list[str]:
        user = self.get_or_create_user(chat_id, user_id, username=username)
        user.topics = _parse_csv(raw_value)
        user.updated_at = _utcnow()
        self._save_user(user)
        return user.topics

    def update_keywords(self, chat_id: int, user_id: int, raw_value: str, username: str | None = None) -> list[str]:
        user = self.get_or_create_user(chat_id, user_id, username=username)
        user.keywords = _parse_csv(raw_value)
        user.updated_at = _utcnow()
        self._save_user(user)
        return user.keywords

    def append_keywords(
        self,
        chat_id: int,
        user_id: int,
        keywords: list[str],
        username: str | None = None,
    ) -> list[str]:
        user = self.get_or_create_user(chat_id, user_id, username=username)
        merged = list(user.keywords)
        seen = {keyword.lower() for keyword in merged}
        for keyword in keywords:
            normalized = keyword.strip()
            if not normalized:
                continue
            lowered = normalized.lower()
            if lowered in seen:
                continue
            merged.append(normalized)
            seen.add(lowered)
        user.keywords = merged
        user.updated_at = _utcnow()
        self._save_user(user)
        return user.keywords

    def remove_keywords(
        self,
        chat_id: int,
        user_id: int,
        keywords: list[str],
        username: str | None = None,
    ) -> list[str]:
        user = self.get_or_create_user(chat_id, user_id, username=username)
        to_remove = {keyword.strip().lower() for keyword in keywords if keyword.strip()}
        if not to_remove:
            return user.keywords
        user.keywords = [keyword for keyword in user.keywords if keyword.lower() not in to_remove]
        user.updated_at = _utcnow()
        self._save_user(user)
        return user.keywords

    def get_all_users(self) -> list[User]:
        users = list(self._users.values())
        known_keys = set(self._users.keys())
        for path in sorted(self._users_dir.glob("*.json")):
            stem = path.stem
            try:
                chat_id_str, user_id_str = stem.split("_", 1)
                key = (int(chat_id_str), int(user_id_str))
            except ValueError:
                continue
            if key in known_keys:
                continue
            user = User.model_validate_json(path.read_text(encoding="utf-8"))
            self._users[key] = user
            users.append(user)
        return users

    def mark_news_pushed(self, chat_id: int, user_id: int, news_id: str, username: str | None = None) -> list[str]:
        user = self.get_or_create_user(chat_id, user_id, username=username)
        if news_id not in user.pushed_news_ids:
            user.pushed_news_ids.append(news_id)
            user.updated_at = _utcnow()
            self._save_user(user)
        return user.pushed_news_ids

    def record_feedback(self, chat_id: int, user_id: int, news_url: str, feedback_type: str, source_command: str) -> None:
        self._feedback[(chat_id, user_id)].append(
            {
                "news_url": news_url,
                "feedback_type": feedback_type,
                "source_command": source_command,
            }
        )

    def record_sent_message(self, chat_id: int, message_id: int, text: str) -> None:
        key = (chat_id, message_id)
        self._sent_messages[key] = text
        path = self._sent_message_path(chat_id, message_id)
        path.write_text(text, encoding="utf-8")

    def get_sent_message(self, chat_id: int, message_id: int) -> str:
        key = (chat_id, message_id)
        cached = self._sent_messages.get(key)
        if cached is not None:
            return cached
        path = self._sent_message_path(chat_id, message_id)
        if not path.exists():
            return ""
        text = path.read_text(encoding="utf-8")
        self._sent_messages[key] = text
        return text

    def _user_path(self, chat_id: int, user_id: int) -> Path:
        return self._users_dir / f"{chat_id}_{user_id}.json"

    def _sent_message_path(self, chat_id: int, message_id: int) -> Path:
        return self._sent_messages_dir / f"{chat_id}_{message_id}.txt"

    def _load_user(self, chat_id: int, user_id: int) -> User | None:
        path = self._user_path(chat_id, user_id)
        if not path.exists():
            return None
        return User.model_validate_json(path.read_text(encoding="utf-8"))

    def _save_user(self, user: User) -> None:
        path = self._user_path(user.chat_id, user.user_id)
        path.write_text(user.model_dump_json(indent=2), encoding="utf-8")


def _utcnow():
    from datetime import datetime, UTC

    return datetime.now(UTC)


user_settings_service = UserSettingsService()
