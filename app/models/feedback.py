from datetime import datetime

from pydantic import BaseModel


class Feedback(BaseModel):
    user_id: int
    chat_id: int
    news_id: str | None = None
    news_url: str | None = None
    feedback_type: str
    source_command: str
    created_at: datetime
