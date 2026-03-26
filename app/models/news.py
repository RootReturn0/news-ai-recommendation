from __future__ import annotations

from hashlib import sha1

from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    id: str
    title: str
    url: str = ""
    summary: str = ""
    source: str = ""
    published_at: str = ""
    score: int = 0
    reason: str = ""

    @classmethod
    def from_source(
        cls,
        title: str,
        url: str = "",
        summary: str = "",
        source: str = "",
        published_at: str = "",
    ) -> "NewsItem":
        digest = sha1(f"{title}|{url}".encode("utf-8")).hexdigest()[:12]
        return cls(
            id=digest,
            title=title,
            url=url,
            summary=summary,
            source=source,
            published_at=published_at,
        )
