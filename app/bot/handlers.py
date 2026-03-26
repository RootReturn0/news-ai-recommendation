from typing import Any

from app.bot.formatter import (
    format_help,
    format_list_update,
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
        await telegram_provider.send_message(chat_id=chat_id, text=reply)
    return reply


async def handle_message(message: dict[str, Any]) -> str:
    text = _extract_text(message)
    command, argument = _parse_command_parts(text)
    chat_id = _extract_chat_id(message)
    user_id = _extract_user_id(message) or chat_id
    username = _extract_username(message)

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
        user = user_settings_service.get_or_create_user(chat_id, user_id, username=username)
        return format_settings(user)
    if command in {"/news", "message"}:
        user = user_settings_service.get_or_create_user(chat_id, user_id, username=username)
        request_text = argument or text or ""
        items = await personalization_service.get_personalized_news(user=user, request_text=request_text)
        summary = await llm_service.summarize_news(user=user, request_text=request_text, items=items)
        return format_news_results("Top picks for you today", summary, items)
    if command == "/hotnews":
        user = user_settings_service.get_or_create_user(chat_id, user_id, username=username)
        items = await personalization_service.get_hot_news(user=user)
        summary = await llm_service.summarize_hot_news(user=user, items=items)
        return format_news_results("Hot news today", summary, items)
    return "Unknown command. Use /help to see available commands."


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
