from pathlib import Path
from xml.etree import ElementTree as ET

from app.config import get_settings
from app.models.news import NewsItem


class RSSProvider:
    def __init__(self) -> None:
        self.settings = get_settings()

    def load_all(self) -> list[NewsItem]:
        rss_dir = Path(self.settings.rss_data_dir)
        items: list[NewsItem] = []
        for path in sorted(rss_dir.glob("*.xml")):
            items.extend(self.load_file(path))
        return items

    def load_file(self, path: str | Path) -> list[NewsItem]:
        tree = ET.parse(path)
        root = tree.getroot()
        items: list[NewsItem] = []
        for node in root.findall(".//item"):
            title = _find_text(node, "title")
            link = _find_text(node, "link")
            summary = _find_text(node, "description")
            published_at = _find_text(node, "pubDate")
            source = _find_text(node, "source") or "RSS"
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
