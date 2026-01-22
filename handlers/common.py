"""
Common handler utilities.

Shared helper functions for all handlers.
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

from pyrogram import Client
from pyrogram.types import Message
from pyrogram.enums import ChatType, ChatMemberStatus, ParseMode
from pyrogram.errors import FloodWait, MessageDeleteForbidden

# Handle imports
try:
    from ..config import OWNER_ID
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import OWNER_ID

logger = logging.getLogger(__name__)

# Basic commands that work even in owner-only mode
BASIC_COMMANDS = {"time", "timehere", "when", "settimezone", "mytimezone", "help", "start"}


async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    """Check if a user is admin in a chat."""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False


async def is_private_chat(message: Message) -> bool:
    """Check if message is from a private chat."""
    return message.chat.type == ChatType.PRIVATE


async def safe_delete_message(client: Client, chat_id: int, message_id: int) -> bool:
    """Safely delete a message, handling errors."""
    try:
        await client.delete_messages(chat_id, message_id)
        return True
    except MessageDeleteForbidden:
        logger.debug(f"Cannot delete message {message_id} in chat {chat_id}")
        return False
    except FloodWait as e:
        logger.warning(f"FloodWait on delete: {e.value}s")
        return False
    except Exception as e:
        logger.debug(f"Error deleting message: {e}")
        return False


async def check_cooldown(
    services,
    chat_id: int,
    user_id: int
) -> Tuple[bool, int, Optional[int]]:
    """
    Check if user is on cooldown.

    Returns (is_on_cooldown, remaining_seconds, old_message_id)
    """
    expiry, old_msg_id = await services.store.get_user_cooldown(chat_id, user_id)

    if expiry:
        now = datetime.utcnow()
        if now < expiry:
            remaining = int((expiry - now).total_seconds())
            return (True, remaining, old_msg_id)

    return (False, 0, old_msg_id)


async def set_cooldown(
    services,
    chat_id: int,
    user_id: int,
    message_id: Optional[int] = None
) -> None:
    """Set cooldown for a user."""
    config = await services.store.get_group_config(chat_id)
    expires_at = datetime.utcnow() + timedelta(seconds=config.cooldown_seconds)
    await services.store.set_user_cooldown(chat_id, user_id, expires_at, message_id)


def is_owner(user_id: int) -> bool:
    """Check if user is the bot owner."""
    return user_id == OWNER_ID


def is_basic_command(command: str) -> bool:
    """Check if command is a basic command (allowed in owner-only mode)."""
    return command.lower() in BASIC_COMMANDS


async def check_owner_only_mode(services, user_id: int, command: str, message: Message) -> bool:
    """
    Check if command should be blocked due to owner-only mode.

    Returns True if command should be BLOCKED (user should not proceed).
    Returns False if command is allowed.
    """
    # Owner can always use any command
    if is_owner(user_id):
        return False

    # Basic commands are always allowed
    if is_basic_command(command):
        return False

    # Check if owner-only mode is enabled
    owner_only = await services.store.get_owner_only_mode()
    if owner_only:
        await message.reply(
            "🔒 <b>Owner-Only Mode Active</b>\n\n"
            "This command is currently restricted.\n"
            "Only basic commands are available:\n"
            "<code>/time</code>, <code>/timehere</code>, <code>/when</code>,\n"
            "<code>/settimezone</code>, <code>/mytimezone</code>, <code>/help</code>",
            parse_mode=ParseMode.HTML
        )
        return True

    return False
