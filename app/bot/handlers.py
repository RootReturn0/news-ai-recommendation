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
    "/dislike",
    "/topics",
    "/keywords",
    "/settings",
}


async def handle_update(payload: dict[str, Any], send_reply: bool = True) -> str:
    if not isinstance(payload, dict):
        return ""
    reaction = payload.get("message_reaction")
    if isinstance(reaction, dict):
        reply = await handle_message_reaction(reaction)
        chat_id = _extract_reaction_chat_id(reaction)
        if send_reply and chat_id:
            for part in _normalize_replies(reply):
                sent_message_id = await telegram_provider.send_message(chat_id=chat_id, text=part)
                if sent_message_id:
                    user_settings_service.record_sent_message(chat_id, sent_message_id, part)
        return _join_reply_preview(reply)

    raw_message = payload.get("message")
    message = raw_message if isinstance(raw_message, dict) else {}
    reply = await handle_message(message)
    chat_id = _extract_chat_id(message)
    if send_reply and chat_id:
        for part in _normalize_replies(reply):
            sent_message_id = await telegram_provider.send_message(chat_id=chat_id, text=part)
            if sent_message_id:
                user_settings_service.record_sent_message(chat_id, sent_message_id, part)
    return _join_reply_preview(reply)


async def handle_message(message: dict[str, Any]) -> str | list[str]:
    text = _extract_text(message)
    command, argument = _parse_command_parts(text)
    chat_id = _extract_chat_id(message)
    user_id = _extract_user_id(message) or chat_id
    username = _extract_username(message)
    user = user_settings_service.get_or_create_user(chat_id, user_id, username=username)

    liked_reply = await _extract_liked_reply_keywords(message, user.keywords)
    if _is_like_message(message):
        if not liked_reply:
            return _keyword_extraction_failed_message()
        previous_keywords = list(user.keywords)
        keywords = user_settings_service.append_keywords(chat_id, user_id, liked_reply, username=username)
        if keywords == previous_keywords:
            return _keyword_extraction_failed_message()
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

    disliked_reply = await _extract_disliked_reply_keywords(message, user.keywords)
    if _is_dislike_message(message):
        if not disliked_reply:
            return _keyword_extraction_failed_message()
        previous_keywords = list(user.keywords)
        keywords = user_settings_service.remove_keywords(chat_id, user_id, disliked_reply, username=username)
        if keywords == previous_keywords:
            return _keyword_extraction_failed_message()
        reply_text = _extract_reply_text(message)
        reply_url = _extract_reply_url(reply_text)
        if reply_url:
            user_settings_service.record_feedback(
                chat_id=chat_id,
                user_id=user_id,
                news_url=reply_url,
                feedback_type="disliked",
                source_command="reply_dislike",
            )
        removed = ", ".join(disliked_reply)
        current = "\n".join(f"- {item}" for item in keywords) or "- (empty)"
        return f"Removed from your keywords: {removed}\n\nCurrent keywords:\n{current}"

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


async def handle_message_reaction(reaction: dict[str, Any]) -> str | list[str]:
    chat_id = _extract_reaction_chat_id(reaction)
    message_id = _extract_reaction_message_id(reaction)
    if not chat_id or not message_id:
        return ""
    user_id = _extract_reaction_user_id(reaction) or chat_id
    username = _extract_reaction_username(reaction)
    user = user_settings_service.get_or_create_user(chat_id, user_id, username=username)
    original_text = user_settings_service.get_sent_message(chat_id, message_id)
    if not original_text:
        return ""
    reaction_emoji = _extract_reaction_emoji(reaction)
    if reaction_emoji == "👍":
        extracted = await llm_service.extract_keywords_from_liked_news(original_text, user.keywords)
        if not extracted:
            return _keyword_extraction_failed_message()
        previous_keywords = list(user.keywords)
        keywords = user_settings_service.append_keywords(chat_id, user_id, extracted, username=username)
        if keywords == previous_keywords:
            return _keyword_extraction_failed_message()
        reply_url = _extract_reply_url(original_text)
        if reply_url:
            user_settings_service.record_feedback(
                chat_id=chat_id,
                user_id=user_id,
                news_url=reply_url,
                feedback_type="liked",
                source_command="reaction_like",
            )
        extracted_text = ", ".join(extracted)
        current = "\n".join(f"- {item}" for item in keywords)
        return f"Saved from your reaction: {extracted_text}\n\nCurrent keywords:\n{current}"
    if reaction_emoji == "👎":
        extracted = await llm_service.extract_keywords_from_liked_news(original_text, user.keywords)
        if not extracted:
            return _keyword_extraction_failed_message()
        previous_keywords = list(user.keywords)
        keywords = user_settings_service.remove_keywords(chat_id, user_id, extracted, username=username)
        if keywords == previous_keywords:
            return _keyword_extraction_failed_message()
        reply_url = _extract_reply_url(original_text)
        if reply_url:
            user_settings_service.record_feedback(
                chat_id=chat_id,
                user_id=user_id,
                news_url=reply_url,
                feedback_type="disliked",
                source_command="reaction_dislike",
            )
        removed_text = ", ".join(extracted)
        current = "\n".join(f"- {item}" for item in keywords) or "- (empty)"
        return f"Removed from your keywords: {removed_text}\n\nCurrent keywords:\n{current}"
    return ""


def _normalize_replies(reply: str | list[str]) -> list[str]:
    if isinstance(reply, list):
        return [item for item in reply if item]
    return [reply] if reply else []


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
    if not _is_like_message(message):
        return []
    reply_text = _extract_reply_text(message)
    if not reply_text:
        return []
    return await llm_service.extract_keywords_from_liked_news(reply_text, existing_keywords)


async def _extract_disliked_reply_keywords(message: dict[str, Any], existing_keywords: list[str]) -> list[str]:
    if not _is_dislike_message(message):
        return []
    reply_text = _extract_reply_text(message)
    if not reply_text:
        return []
    return await llm_service.extract_keywords_from_liked_news(reply_text, existing_keywords)


def _is_like_message(message: dict[str, Any]) -> bool:
    text = _extract_text(message).strip().lower()
    return text in {"👍", "/like", "like", "liked", "love this"}


def _is_dislike_message(message: dict[str, Any]) -> bool:
    text = _extract_text(message).strip().lower()
    return text in {"/dislike", "dislike", "not interested", "don't like this", "👎"}


def _keyword_extraction_failed_message() -> str:
    return (
        "No topic keywords could be updated."
    )


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


def _extract_reaction_chat_id(reaction: dict[str, Any]) -> int:
    chat = reaction.get("chat")
    if isinstance(chat, dict):
        chat_id = chat.get("id")
        if isinstance(chat_id, int):
            return chat_id
    return 0


def _extract_reaction_message_id(reaction: dict[str, Any]) -> int:
    message_id = reaction.get("message_id")
    if isinstance(message_id, int):
        return message_id
    return 0


def _extract_reaction_emoji(reaction: dict[str, Any]) -> str:
    new_reaction = reaction.get("new_reaction")
    if not isinstance(new_reaction, list):
        return ""
    for item in new_reaction:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "emoji":
            continue
        emoji = item.get("emoji")
        if isinstance(emoji, str):
            return emoji
    return ""


def _extract_reaction_user_id(reaction: dict[str, Any]) -> int:
    for field in ("user", "from"):
        value = reaction.get(field)
        if isinstance(value, dict):
            user_id = value.get("id")
            if isinstance(user_id, int):
                return user_id
    actor_chat = reaction.get("actor_chat")
    if isinstance(actor_chat, dict):
        actor_id = actor_chat.get("id")
        if isinstance(actor_id, int):
            return actor_id
    return 0


def _extract_reaction_username(reaction: dict[str, Any]) -> str | None:
    for field in ("user", "from"):
        value = reaction.get(field)
        if isinstance(value, dict):
            username = value.get("username")
            if isinstance(username, str) and username:
                return username
    return None
