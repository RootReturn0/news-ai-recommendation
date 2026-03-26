from typing import Any

from app.bot.formatter import (
    format_help,
    format_list_update,
    format_news_intro,
    format_news_item,
    format_news_results,
    format_settings,
    format_welcome,
)
from app.providers.telegram_provider import TelegramProvider
from app.services.llm_service import LLMService
from app.services.personalization_service import PersonalizationService
from app.services.user_settings_service import user_settings_service

telegram_provider = TelegramProvider()
personalization_service = PersonalizationService()
llm_service = LLMService()
SUPPORTED_COMMANDS = {
    "/start",
    "/help",
    "/news",
    "/hotnews",
    "/topics",
    "/keywords",
    "/settings",
}


async def handle_update(payload: dict[str, Any], send_reply: bool = True) -> str:
    raw_message = payload.get("message") if isinstance(payload, dict) else None
    message = raw_message if isinstance(raw_message, dict) else {}
    reply = await handle_message(message)
    chat_id = _extract_chat_id(message)
    if send_reply and chat_id:
        for part in _normalize_replies(reply):
            await telegram_provider.send_message(chat_id=chat_id, text=part)
    return _join_reply_preview(reply)


async def handle_message(message: dict[str, Any]) -> str | list[str]:
    text = _extract_text(message)
    command, argument = _parse_command_parts(text)
    chat_id = _extract_chat_id(message)
    user_id = _extract_user_id(message) or chat_id
    username = _extract_username(message)
    user = user_settings_service.get_or_create_user(chat_id, user_id, username=username)

    liked_reply = await _extract_liked_reply_keywords(message, user.keywords)
    if liked_reply:
        keywords = user_settings_service.append_keywords(chat_id, user_id, liked_reply, username=username)
        reply_text = _extract_reply_text(message)
        reply_url = _extract_reply_url(reply_text)
        if reply_url:
            user_settings_service.record_feedback(
                chat_id=chat_id,
                user_id=user_id,
                news_url=reply_url,
                feedback_type="liked",
                source_command="reply_like",
            )
        extracted = ", ".join(liked_reply)
        return f"Saved from your like: {extracted}\n\nCurrent keywords:\n" + "\n".join(f"- {item}" for item in keywords)

    if command == "/start":
        return format_welcome()
    if command == "/help":
        return format_help()
    if command == "/topics":
        values = user_settings_service.update_topics(chat_id, user_id, argument, username=username)
        return format_list_update("Topics", values)
    if command == "/keywords":
        values = user_settings_service.update_keywords(chat_id, user_id, argument, username=username)
        return format_list_update("Keywords", values)
    if command == "/settings":
        return format_settings(user)
    # if command in {"/news", "message"}:
    if command in {"/news"}:
        request_text = argument or text or ""
        items = await personalization_service.get_personalized_news(user=user, request_text=request_text)
        summary = await llm_service.summarize_news(user=user, request_text=request_text, items=items)
        if not items:
            return format_news_results("Top picks for you today", summary, items)
        replies = [format_news_intro("Top picks for you today", summary)]
        replies.extend(format_news_item(index, item) for index, item in enumerate(items, start=1))
        return replies
    if command == "/hotnews":
        items = await personalization_service.get_hot_news(user=user)
        summary = await llm_service.summarize_hot_news(user=user, items=items)
        if not items:
            return format_news_results("Hot news today", summary, items)
        replies = [format_news_intro("Hot news today", summary)]
        replies.extend(format_news_item(index, item) for index, item in enumerate(items, start=1))
        return replies
    return "Unknown command. Use /help to see available commands."


def _normalize_replies(reply: str | list[str]) -> list[str]:
    if isinstance(reply, list):
        return reply
    return [reply]


def _join_reply_preview(reply: str | list[str]) -> str:
    return "\n\n".join(_normalize_replies(reply))


def _extract_text(message: dict[str, Any]) -> str:
    text = message.get("text")
    return text if isinstance(text, str) else ""


def _extract_chat_id(message: dict[str, Any]) -> int:
    chat = message.get("chat")
    if isinstance(chat, dict):
        chat_id = chat.get("id")
        if isinstance(chat_id, int):
            return chat_id
    return 0


def _extract_user_id(message: dict[str, Any]) -> int:
    from_user = message.get("from")
    if isinstance(from_user, dict):
        user_id = from_user.get("id")
        if isinstance(user_id, int):
            return user_id
    return 0


def _extract_username(message: dict[str, Any]) -> str | None:
    from_user = message.get("from")
    if isinstance(from_user, dict):
        username = from_user.get("username")
        if isinstance(username, str) and username:
            return username
    return None


def _parse_command_parts(text: str) -> tuple[str, str]:
    stripped = text.strip()
    if not stripped:
        return "message", ""
    if not stripped.startswith("/"):
        return "message", stripped

    head, _, tail = stripped.partition(" ")
    command = head.split("@", 1)[0]
    if command not in SUPPORTED_COMMANDS:
        return "unknown", stripped
    return command, tail.strip()


async def _extract_liked_reply_keywords(message: dict[str, Any], existing_keywords: list[str]) -> list[str]:
    text = _extract_text(message).strip().lower()
    if text not in {"👍", "/like", "like", "liked", "love this"}:
        return []
    reply_text = _extract_reply_text(message)
    if not reply_text:
        return []
    return await llm_service.extract_keywords_from_liked_news(reply_text, existing_keywords)


def _extract_reply_text(message: dict[str, Any]) -> str:
    reply = message.get("reply_to_message")
    if not isinstance(reply, dict):
        return ""
    text = reply.get("text")
    if isinstance(text, str) and text:
        return text
    caption = reply.get("caption")
    return caption if isinstance(caption, str) else ""


def _extract_reply_url(reply_text: str) -> str:
    for line in reply_text.splitlines():
        if line.startswith("Link: "):
            return line.replace("Link: ", "", 1).strip()
    return ""
