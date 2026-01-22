"""
Handler for /timehere command.

Shows the current time for the user based on their personal timezone.
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatType, ParseMode

# Auto-delete delay for this command (seconds)
AUTO_DELETE_DELAY = 30

logger = logging.getLogger(__name__)


def register_timehere_handler(app: Client, services):
    """Register the /timehere command handler."""

    @app.on_message(filters.command("timehere"))
    async def handle_timehere(client: Client, message: Message):
        """Show user's current time based on their timezone setting."""
        user_id = message.from_user.id if message.from_user else 0
        is_group = message.chat.type != ChatType.PRIVATE

        if not user_id:
            await message.reply("Could not identify user.")
            return

        # Get user's timezone
        user_data = await services.store.get_user_timezone(user_id)

        if not user_data:
            sent = await message.reply(
                "<b>No Timezone Set</b>\n\n"
                "Set your timezone with:\n"
                "<code>/settimezone &lt;city&gt;</code>\n\n"
                "<b>Examples:</b>\n"
                "• <code>/settimezone Tokyo</code>\n"
                "• <code>/settimezone New York</code>\n"
                "• <code>/settimezone Tashkent</code>",
                parse_mode=ParseMode.HTML
            )
            # Auto-delete in groups
            if is_group:
                delete_at = datetime.utcnow() + timedelta(seconds=AUTO_DELETE_DELAY)
                await services.store.schedule_delete(message.chat.id, sent.id, delete_at)
            return

        # Show user's current time
        text = services.timezone.get_user_time_display(
            user_data.timezone,
            user_data.display_name
        )
        text += "\n\n<i>Update with /settimezone &lt;city&gt;</i>"

        sent = await message.reply(text, parse_mode=ParseMode.HTML)

        # Auto-delete in groups
        if is_group:
            delete_at = datetime.utcnow() + timedelta(seconds=AUTO_DELETE_DELAY)
            await services.store.schedule_delete(message.chat.id, sent.id, delete_at)

        logger.info(f"/timehere by user {user_id} ({user_data.timezone})")
