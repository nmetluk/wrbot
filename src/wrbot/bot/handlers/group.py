"""
Group-specific handlers: /getgrid and bot @mentions in groups/channels (TASK-0047).

Purpose: allow any group member to easily obtain the numeric chat.id (for use in
category notify_chat_ids from TASK-0043) by calling /getgrid or @mentioning the bot
inside the target group/supergroup.

- Scoped to group/supergroup chats via F.chat.type filters.
- /getgrid works with /getgrid@bot (Command filter handles it).
- @mention handler responds ONLY on explicit mention (does not reply to every group message).
- Private chat /getgrid gives a helpful hint (no crash).
- Uses bot.me() to resolve current username for mention matching (can be called in handler;
  rare operation).
- No privacy mode changes; no logging of group message texts.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiogram import F, Router
from aiogram.filters import Command

from wrbot.bot.texts import Texts

if TYPE_CHECKING:
    from aiogram import Bot
    from aiogram.types import Message

logger = logging.getLogger(__name__)

router = Router(name="group")


@router.message(Command("getgrid"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_getgrid_in_group(message: Message, bot: Bot) -> None:
    """Handle /getgrid (and /getgrid@bot) inside groups/supergroups.

    Any participant can call it (no admin check, per owner decision).
    Replies with the chat.id in copyable <code> form + hint about category settings.
    """
    chat_id = message.chat.id
    text = Texts.getgrid_group_id.format(chat_id=chat_id)
    await message.answer(text)


@router.message(Command("getgrid"), F.chat.type == "private")
async def cmd_getgrid_in_private(message: Message) -> None:
    """Handle /getgrid in private chat: give a hint instead of error or the private chat id."""
    await message.answer(Texts.getgrid_private_hint)


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def on_mention_in_group(message: Message, bot: Bot) -> None:
    """Respond with chat ID only if the bot was explicitly @mentioned in a group message.

    Ignores all other messages in the group (anti-spam / privacy).
    Supports both "mention" entities (by @username) and "text_mention" (by user id).
    Username is resolved via bot.me() (cached by aiogram internally in practice).
    """
    if not message.text:
        return

    try:
        me = await bot.me()
    except Exception:
        logger.warning("Failed to get bot.me() for mention check")
        return

    bot_username = (me.username or "").lower()
    bot_id = me.id

    mentioned = False
    entities = getattr(message, "entities", None) or []
    for ent in entities:
        if ent.type == "mention" and bot_username:
            mention_text = message.text[ent.offset : ent.offset + ent.length].lower()
            if mention_text == f"@{bot_username}":
                mentioned = True
                break
        elif ent.type == "text_mention":
            user = getattr(ent, "user", None)
            if user and getattr(user, "id", None) == bot_id:
                mentioned = True
                break

    if not mentioned:
        # Not a mention of us — stay silent (do not answer every group message).
        return

    chat_id = message.chat.id
    text = Texts.getgrid_group_id.format(chat_id=chat_id)
    await message.answer(text)
