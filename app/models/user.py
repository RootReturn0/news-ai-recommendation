from datetime import UTC, datetime

from pydantic import BaseModel, Field


class User(BaseModel):
    chat_id: int
    user_id: int
    username: str | None = None
    topics: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
