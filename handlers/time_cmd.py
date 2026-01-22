"""
Handler for /time and /time_live commands.

/time - One-time display of current times (everyone)
/time_live - Live updating display (admins only, updates forever)
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatType, ParseMode

# Handle imports
try:
    from .common import is_admin, is_private_chat, safe_delete_message, check_cooldown, set_cooldown, check_owner_only_mode
    from ..config import TIME_UPDATE_INTERVAL
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from common import is_admin, is_private_chat, safe_delete_message, check_cooldown, set_cooldown, check_owner_only_mode
    from config import TIME_UPDATE_INTERVAL

logger = logging.getLogger(__name__)


def register_time_handler(app: Client, services):
    """Register the /time command handler."""

    @app.on_message(filters.command("time"))
    async def handle_time(client: Client, message: Message):
        """
        Handle /time command - one-time display.

        Shows current times for all saved group timezones.
        Per-user cooldown applies.
        """
        chat_id = message.chat.id
        user_id = message.from_user.id if message.from_user else 0

        if not user_id:
            return

        # Private chat - show user's timezone
        if await is_private_chat(message):
            user_data = await services.store.get_user_timezone(user_id)
            if user_data:
                text = services.timezone.get_user_time_display(
                    user_data.timezone,
                    user_data.display_name
                )
            else:
                text = (
                    "<b>No timezone set</b>\n\n"
                    "Set your timezone with:\n"
                    "<code>/settimezone &lt;city&gt;</code>\n\n"
                    "Examples:\n"
                    "• <code>/settimezone Tokyo</code>\n"
                    "• <code>/settimezone New York</code>"
                )
            await message.reply(text, parse_mode=ParseMode.HTML)
            return

        # Group chat - check per-user cooldown
        on_cooldown, remaining, old_msg_id = await check_cooldown(services, chat_id, user_id)

        if on_cooldown:
            # Delete old cooldown message if exists
            if old_msg_id:
                await safe_delete_message(client, chat_id, old_msg_id)

            # Send cooldown notice
            cooldown_msg = await message.reply(
                f"<b>Cooldown Active</b>\n\n"
                f"Please wait {remaining} seconds before using /time again.",
                parse_mode=ParseMode.HTML
            )

            # Update stored message ID for cleanup
            await set_cooldown(services, chat_id, user_id, cooldown_msg.id)
            return

        # Get group config and timezones
        config = await services.store.get_group_config(chat_id)
        timezones = await services.store.get_group_timezones(chat_id)

        # Format message (not live)
        text = services.timezone.format_all_times(
            timezones,
            is_live=False,
            show_utc_offset=config.show_utc_offset
        )

        # Send the message
        sent_message = await message.reply(text, parse_mode=ParseMode.HTML)

        # Set cooldown with message ID
        await set_cooldown(services, chat_id, user_id, sent_message.id)

        # Schedule auto-delete after 25 seconds
        delete_at = datetime.utcnow() + timedelta(seconds=TIME_UPDATE_INTERVAL)
        await services.store.schedule_delete(chat_id, sent_message.id, delete_at)

        logger.info(f"/time by user {user_id} in chat {chat_id}")

    @app.on_message(filters.command("time_live"))
    async def handle_time_live(client: Client, message: Message):
        """
        Handle /time_live command - live updating display (admin only).

        Updates every 25 seconds forever until a new /time_live is called.
        """
        chat_id = message.chat.id
        user_id = message.from_user.id if message.from_user else 0

        if not user_id:
            return

        # Check owner-only mode
        if await check_owner_only_mode(services, user_id, "time_live", message):
            return

        # Private chat - not supported
        if await is_private_chat(message):
            await message.reply(
                "<b>Not Available</b>\n\n"
                "Live time updates are only available in groups.\n"
                "Use /time to see your current time.",
                parse_mode=ParseMode.HTML
            )
            return

        # Check admin permission
        if not await is_admin(client, chat_id, user_id):
            await message.reply(
                "<b>Permission Denied</b>\n\n"
                "Live time updates (/time_live) are only available to admins.\n"
                "Use /time for a one-time display.",
                parse_mode=ParseMode.HTML
            )
            return

        # Check if there's already an active live message
        if services.tasks.is_chat_active(chat_id):
            # Stop the existing task (will be replaced)
            await services.tasks.stop_time_task(chat_id)

        # Get group config and timezones
        config = await services.store.get_group_config(chat_id)
        timezones = await services.store.get_group_timezones(chat_id)

        # Format initial message (live)
        text = services.timezone.format_all_times(
            timezones,
            is_live=True,
            show_utc_offset=config.show_utc_offset
        )

        # Send the message
        sent_message = await message.reply(text, parse_mode=ParseMode.HTML)

        # Start the live update task (runs forever)
        if timezones:
            await services.tasks.start_time_task(
                client,
                chat_id,
                sent_message.id
            )

        logger.info(f"/time_live started by admin {user_id} in chat {chat_id}")
