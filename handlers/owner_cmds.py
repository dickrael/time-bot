"""
Owner-only command handlers.

Commands only available to the bot owner (OWNER_ID).
"""

import logging
import sys
from pathlib import Path

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode

# Handle imports
try:
    from ..config import OWNER_ID
    from .common import is_owner
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    sys.path.insert(0, str(Path(__file__).parent))
    from config import OWNER_ID
    from common import is_owner

logger = logging.getLogger(__name__)


def register_owner_handlers(app: Client, services):
    """Register owner-only command handlers."""

    @app.on_message(filters.command("ownermode"))
    async def handle_ownermode(client: Client, message: Message):
        """
        Handle /ownermode command (owner only).

        Toggle owner-only mode on/off.
        When enabled, only basic commands work for non-owners.
        """
        user_id = message.from_user.id if message.from_user else 0

        if not is_owner(user_id):
            await message.reply(
                "⛔ <b>Permission Denied</b>\n\n"
                "This command is only available to the bot owner.",
                parse_mode=ParseMode.HTML
            )
            return

        # Parse arguments
        args = message.text.split()

        if len(args) < 2:
            # Show current status
            current_mode = await services.store.get_owner_only_mode()
            status = "🔒 <b>Enabled</b>" if current_mode else "🔓 <b>Disabled</b>"

            await message.reply(
                f"⚙️ <b>Owner-Only Mode</b>\n\n"
                f"Current status: {status}\n\n"
                f"<b>Usage:</b>\n"
                f"• <code>/ownermode on</code> - Enable owner-only mode\n"
                f"• <code>/ownermode off</code> - Disable owner-only mode\n\n"
                f"<i>When enabled, only basic commands are available to other users.</i>",
                parse_mode=ParseMode.HTML
            )
            return

        action = args[1].lower()

        if action in ("on", "enable", "1", "true"):
            await services.store.set_owner_only_mode(True)
            await message.reply(
                "🔒 <b>Owner-Only Mode Enabled</b>\n\n"
                "Only basic commands are now available to other users:\n"
                "<code>/time</code>, <code>/timehere</code>, <code>/when</code>,\n"
                "<code>/settimezone</code>, <code>/mytimezone</code>, <code>/help</code>",
                parse_mode=ParseMode.HTML
            )
            logger.info(f"Owner-only mode ENABLED by user {user_id}")

        elif action in ("off", "disable", "0", "false"):
            await services.store.set_owner_only_mode(False)
            await message.reply(
                "🔓 <b>Owner-Only Mode Disabled</b>\n\n"
                "All commands are now available to admins.",
                parse_mode=ParseMode.HTML
            )
            logger.info(f"Owner-only mode DISABLED by user {user_id}")

        else:
            await message.reply(
                "❌ <b>Invalid Option</b>\n\n"
                "Use <code>/ownermode on</code> or <code>/ownermode off</code>",
                parse_mode=ParseMode.HTML
            )

    @app.on_message(filters.command("broadcast"))
    async def handle_broadcast(client: Client, message: Message):
        """
        Handle /broadcast command (owner only).

        Broadcast a message to all groups where the bot is active.
        Usage: /broadcast <message>
        """
        user_id = message.from_user.id if message.from_user else 0

        if not is_owner(user_id):
            return  # Silently ignore for non-owners

        # Parse arguments
        args = message.text.split(maxsplit=1)

        if len(args) < 2:
            await message.reply(
                "📢 <b>Broadcast</b>\n\n"
                "<b>Usage:</b> <code>/broadcast &lt;message&gt;</code>\n\n"
                "<i>Sends message to all groups with configured timezones.</i>",
                parse_mode=ParseMode.HTML
            )
            return

        broadcast_text = args[1]

        # This is a placeholder - actual broadcast would need group tracking
        await message.reply(
            "✅ <b>Broadcast feature</b>\n\n"
            "This feature requires group tracking to be implemented.",
            parse_mode=ParseMode.HTML
        )
