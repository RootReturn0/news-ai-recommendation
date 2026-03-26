from pathlib import Path
from xml.etree import ElementTree as ET

import httpx

from app.config import get_settings
from app.models.news import NewsItem


class RSSProvider:
    def __init__(self) -> None:
        self.settings = get_settings()

    def load_all(self) -> list[NewsItem]:
        try:
            response = httpx.get(self.settings.rss_feed_url, timeout=20.0)
            response.raise_for_status()
            return self.load_xml(response.text, source_name="Hacker News")
        except Exception:
            return []

    def load_file(self, path: str | Path) -> list[NewsItem]:
        return self.load_xml(Path(path).read_text(encoding="utf-8"), source_name="RSS")

    def load_xml(self, xml_text: str, source_name: str = "RSS") -> list[NewsItem]:
        root = ET.fromstring(xml_text)
        items: list[NewsItem] = []
        for node in root.findall(".//item"):
            title = _find_text(node, "title")
            link = _find_text(node, "link")
            summary = _find_text(node, "description")
            published_at = _find_text(node, "pubDate")
            source = _find_text(node, "source") or source_name
            if not title:
                continue
            items.append(
                NewsItem.from_source(
                    title=title,
                    url=link,
                    summary=summary,
                    source=source,
                    published_at=published_at,
                )
            )
        return items


def _find_text(node: ET.Element, name: str) -> str:
    child = node.find(name)
    return child.text.strip() if child is not None and child.text else ""
