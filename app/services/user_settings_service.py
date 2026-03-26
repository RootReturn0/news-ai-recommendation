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
        self._users_dir = Path("data/users")
        self._users_dir.mkdir(parents=True, exist_ok=True)

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

    def record_feedback(self, chat_id: int, user_id: int, news_url: str, feedback_type: str, source_command: str) -> None:
        self._feedback[(chat_id, user_id)].append(
            {
                "news_url": news_url,
                "feedback_type": feedback_type,
                "source_command": source_command,
            }
        )

    def _user_path(self, chat_id: int, user_id: int) -> Path:
        return self._users_dir / f"{chat_id}_{user_id}.json"

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
