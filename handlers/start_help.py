"""
Handler for /start and /help commands.

/start - Welcome message (brief in groups, detailed in private)
/help - Full command reference
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType, ParseMode

# Handle imports
try:
    from ..langs import get_string
    from ..config import OWNER_ID
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from langs import get_string
    from config import OWNER_ID

# Auto-delete delay for start/help in groups (seconds)
AUTO_DELETE_DELAY = 45

logger = logging.getLogger(__name__)

# Cache for bot username
_bot_username = None


async def get_bot_username(client: Client) -> str:
    """Get and cache the bot's username."""
    global _bot_username
    if _bot_username is None:
        me = await client.get_me()
        _bot_username = me.username
    return _bot_username


def register_start_help_handlers(app: Client, services):
    """Register /start and /help handlers."""

    async def schedule_auto_delete(chat_id: int, message_id: int):
        """Schedule a message for auto-deletion in groups."""
        delete_at = datetime.utcnow() + timedelta(seconds=AUTO_DELETE_DELAY)
        await services.store.schedule_delete(chat_id, message_id, delete_at)

    @app.on_message(filters.command("start"))
    async def handle_start(client: Client, message: Message):
        """
        Handle /start command.

        In private: Show full welcome with features
        In groups: Show brief text with button that opens DM
        """
        user_id = message.from_user.id if message.from_user else 0
        chat_id = message.chat.id
        is_group = message.chat.type != ChatType.PRIVATE

        # Check for deep link parameter
        args = message.text.split(maxsplit=1)
        if len(args) > 1:
            param = args[1].strip()
            # Handle /start help - show help in DM
            if param == "help":
                # Check owner-only mode for restricted help
                owner_only = await services.store.get_owner_only_mode()
                if owner_only and user_id != OWNER_ID:
                    text = get_string("help_text_restricted")
                else:
                    text = get_string("help_text")
                sent = await message.reply(text, parse_mode=ParseMode.HTML)
                if is_group:
                    await schedule_auto_delete(chat_id, sent.id)
                return

        if message.chat.type == ChatType.PRIVATE:
            # Private chat - detailed welcome
            text = get_string("start_private")
            await message.reply(text, parse_mode=ParseMode.HTML)
        else:
            # Group chat - brief with button that opens DM
            text = get_string("start_group")

            # Get bot username for deep link
            bot_username = await get_bot_username(client)
            deep_link = f"https://t.me/{bot_username}?start=help"

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    get_string("start_button"),
                    url=deep_link
                )]
            ])
            sent = await message.reply(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            await schedule_auto_delete(chat_id, sent.id)

    @app.on_message(filters.command("help"))
    async def handle_help(client: Client, message: Message):
        """Handle /help command - show full command reference."""
        user_id = message.from_user.id if message.from_user else 0
        chat_id = message.chat.id
        is_group = message.chat.type != ChatType.PRIVATE

        # Check owner-only mode for restricted help
        owner_only = await services.store.get_owner_only_mode()
        if owner_only and user_id != OWNER_ID:
            text = get_string("help_text_restricted")
        else:
            text = get_string("help_text")

        sent = await message.reply(text, parse_mode=ParseMode.HTML)
        if is_group:
            await schedule_auto_delete(chat_id, sent.id)
