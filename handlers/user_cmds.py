"""
User command handlers.

Handles personal timezone management for users.
"""

import logging

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode

logger = logging.getLogger(__name__)


def register_user_handlers(app: Client, services):
    """Register user command handlers."""

    @app.on_message(filters.command("settimezone"))
    async def handle_settimezone(client: Client, message: Message):
        """
        Handle /settimezone command.

        Sets the user's personal timezone.
        Usage: /settimezone <city or timezone>
        """
        user_id = message.from_user.id if message.from_user else 0

        if not user_id:
            await message.reply("❌ Could not identify user.")
            return

        # Parse arguments
        args = message.text.split(maxsplit=1)

        if len(args) < 2:
            # Show current timezone and usage
            user_data = await services.store.get_user_timezone(user_id)

            if user_data:
                current = (
                    f"<b>Current timezone:</b> {user_data.display_name} "
                    f"(<code>{user_data.timezone}</code>)\n\n"
                )
            else:
                current = "<b>Current timezone:</b> Not set\n\n"

            await message.reply(
                f"📍 <b>Set Your Timezone</b>\n\n"
                f"{current}"
                f"<b>Usage:</b> <code>/settimezone &lt;city or timezone&gt;</code>\n\n"
                f"<b>Examples:</b>\n"
                f"• <code>/settimezone Tokyo</code>\n"
                f"• <code>/settimezone New York</code>\n"
                f"• <code>/settimezone America/Los_Angeles</code>\n"
                f"• <code>/settimezone PST</code>\n"
                f"• <code>/settimezone UK</code>",
                parse_mode=ParseMode.HTML
            )
            return

        tz_query = args[1].strip()

        # Resolve the timezone
        resolved = await services.timezone.resolve_timezone(tz_query)

        if not resolved:
            await message.reply(
                f"❌ <b>Unknown Timezone</b>\n\n"
                f"Could not resolve <code>{tz_query}</code>.\n\n"
                f"<b>Try using:</b>\n"
                f"• City names: <code>Tokyo</code>, <code>London</code>, <code>Paris</code>\n"
                f"• Country names: <code>Japan</code>, <code>Germany</code>, <code>UK</code>\n"
                f"• Abbreviations: <code>PST</code>, <code>EST</code>, <code>CET</code>\n"
                f"• IANA IDs: <code>America/New_York</code>, <code>Europe/London</code>",
                parse_mode=ParseMode.HTML
            )
            return

        tz_id, display_name = resolved

        # Save the timezone
        await services.store.set_user_timezone(user_id, tz_id, display_name)

        # Show confirmation with current time
        time_display = services.timezone.get_user_time_display(tz_id, display_name)

        await message.reply(
            f"✅ <b>Timezone Set!</b>\n\n"
            f"{time_display}\n\n"
            f"<i>Use /timehere to check your time anytime.</i>",
            parse_mode=ParseMode.HTML
        )

        logger.info(f"User {user_id} set timezone to {tz_id}")

    @app.on_message(filters.command("mytimezone"))
    async def handle_mytimezone(client: Client, message: Message):
        """
        Handle /mytimezone command.

        Shows the user's current timezone setting.
        Alias for checking timezone without changing it.
        """
        user_id = message.from_user.id if message.from_user else 0

        if not user_id:
            await message.reply("❌ Could not identify user.")
            return

        user_data = await services.store.get_user_timezone(user_id)

        if not user_data:
            await message.reply(
                "📍 <b>No Timezone Set</b>\n\n"
                "You haven't set your timezone yet.\n\n"
                "Set it with <code>/settimezone &lt;city&gt;</code>",
                parse_mode=ParseMode.HTML
            )
            return

        time_display = services.timezone.get_user_time_display(
            user_data.timezone,
            user_data.display_name
        )

        await message.reply(
            f"{time_display}\n\n"
            f"<i>Change with /settimezone &lt;city&gt;</i>",
            parse_mode=ParseMode.HTML
        )
