"""
Handler for /start and /help commands.

/start - Welcome message (brief in groups, detailed in private)
/help - Full command reference
"""

import logging
import sys
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

    @app.on_message(filters.command("start"))
    async def handle_start(client: Client, message: Message):
        """
        Handle /start command.

        In private: Show full welcome with features
        In groups: Show brief text with button that opens DM
        """
        user_id = message.from_user.id if message.from_user else 0

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
                await message.reply(text, parse_mode=ParseMode.HTML)
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
            await message.reply(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

    @app.on_message(filters.command("help"))
    async def handle_help(client: Client, message: Message):
        """Handle /help command - show full command reference."""
        user_id = message.from_user.id if message.from_user else 0

        # Check owner-only mode for restricted help
        owner_only = await services.store.get_owner_only_mode()
        if owner_only and user_id != OWNER_ID:
            text = get_string("help_text_restricted")
        else:
            text = get_string("help_text")

        await message.reply(text, parse_mode=ParseMode.HTML)
