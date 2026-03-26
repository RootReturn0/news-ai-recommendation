from app.models.news import NewsItem
from app.models.user import User


def format_settings(user: User) -> str:
    topics = "\n".join(f"- {topic}" for topic in user.topics) or "- (empty)"
    keywords = "\n".join(f"- {keyword}" for keyword in user.keywords) or "- (empty)"
    return f"Your current settings\n\nTopics:\n{topics}\n\nKeywords:\n{keywords}"


def format_list_update(label: str, values: list[str]) -> str:
    current = "\n".join(f"- {value}" for value in values) or "- (empty)"
    return f"{label} updated.\nCurrent {label.lower()}:\n{current}"


def format_news_results(header: str, summary: str, items: list[NewsItem]) -> str:
    if not items:
        return "No strong matches found right now.\nTry broadening your topics or keywords, or use /hotnews to see the current hot feed."

    lines = [header, "", summary]
    for index, item in enumerate(items, start=1):
        lines.extend(
            [
                "",
                f"{index}. {item.title}",
                f"Why it matters: {item.reason or 'This looks relevant to your current interests.'}",
                f"Source: {item.source or 'Unknown'}",
                f"Link: {item.url or 'N/A'}",
            ]
        )
    return "\n".join(lines)


def format_news_intro(header: str, summary: str) -> str:
    return f"{header}\n\n{summary}"


def format_news_item(index: int, item: NewsItem) -> str:
    return "\n".join(
        [
            f"{index}. {item.title}",
            f"Why it matters: {item.reason or 'This looks relevant to your current interests.'}",
            f"Source: {item.source or 'Unknown'}",
            f"Link: {item.url or 'N/A'}",
        ]
    )


def format_help() -> str:
    return (
        "Commands:\n"
        "/topics AI, startups\n"
        "/keywords OpenAI, YC\n"
        "/settings\n"
        "/news today\n"
        "/hotnews\n"
        "Reply /dislike to a sent news item to remove related keywords"
    )


def format_welcome() -> str:
    return (
        "This bot helps you find personalized news.\n"
        "Set your interests with /topics and /keywords, then use /news or /hotnews."
    )
