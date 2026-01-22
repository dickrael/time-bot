"""
Handler for /when command.

Converts a time from one timezone to all group timezones.
Usage: /when 18:00 Tokyo
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
    from ..langs import get_string
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from langs import get_string

# Auto-delete delay for this command (seconds)
AUTO_DELETE_DELAY = 45

logger = logging.getLogger(__name__)


def register_when_handler(app: Client, services):
    """Register the /when command handler."""

    async def schedule_auto_delete(chat_id: int, message_id: int):
        """Schedule a message for auto-deletion in groups."""
        delete_at = datetime.utcnow() + timedelta(seconds=AUTO_DELETE_DELAY)
        await services.store.schedule_delete(chat_id, message_id, delete_at)

    @app.on_message(filters.command("when"))
    async def handle_when(client: Client, message: Message):
        """
        Handle /when command.

        Converts a given time from a source timezone to:
        - All stored group timezones
        - User's timezone (if set)

        Usage: /when <time> <timezone>
        """
        user_id = message.from_user.id if message.from_user else 0
        chat_id = message.chat.id
        is_private = message.chat.type == ChatType.PRIVATE

        # Parse command arguments
        args = message.text.split(maxsplit=2)

        if len(args) < 3:
            sent = await message.reply(
                "📖 <b>Usage:</b> <code>/when &lt;time&gt; &lt;timezone&gt;</code>\n\n"
                "<b>Examples:</b>\n"
                "• <code>/when 18:00 Tokyo</code>\n"
                "• <code>/when 3pm PST</code>\n"
                "• <code>/when 14:30 London</code>\n"
                "• <code>/when 9am America/New_York</code>\n\n"
                "<b>Supported time formats:</b>\n"
                "• 24-hour: <code>18:00</code>, <code>1430</code>\n"
                "• 12-hour: <code>6pm</code>, <code>3:30am</code>",
                parse_mode=ParseMode.HTML
            )
            if not is_private:
                await schedule_auto_delete(chat_id, sent.id)
            return

        time_str = args[1]
        tz_query = args[2]

        # Resolve the source timezone
        resolved = await services.timezone.resolve_timezone(tz_query)
        if not resolved:
            sent = await message.reply(
                f"❌ <b>Unknown Timezone</b>\n\n"
                f"Could not resolve <code>{tz_query}</code>.\n\n"
                f"Try using:\n"
                f"• City names: <code>Tokyo</code>, <code>London</code>, <code>NYC</code>\n"
                f"• Abbreviations: <code>PST</code>, <code>EST</code>, <code>CET</code>\n"
                f"• IANA IDs: <code>America/New_York</code>",
                parse_mode=ParseMode.HTML
            )
            if not is_private:
                await schedule_auto_delete(chat_id, sent.id)
            return

        source_tz, source_name = resolved

        # Gather target timezones
        target_timezones = []

        # In groups, include all group timezones
        if not is_private:
            group_tzs = await services.store.get_group_timezones(chat_id)
            for entry in group_tzs.values():
                # Don't include source timezone in targets
                if entry.tz != source_tz:
                    target_timezones.append((entry.tz, entry.display_name))

        # Include user's timezone if set and different from source
        user_data = await services.store.get_user_timezone(user_id)
        if user_data and user_data.timezone != source_tz:
            # Check if not already in targets
            if not any(tz == user_data.timezone for tz, _ in target_timezones):
                target_timezones.append((
                    user_data.timezone,
                    f"{user_data.display_name} (you)"
                ))

        if not target_timezones:
            # No targets - just show the source time info
            if is_private:
                hint = "Set your timezone with <code>/settimezone &lt;city&gt;</code> to see conversions."
            else:
                hint = (
                    "Add group timezones with <code>/addtime &lt;city&gt;</code> or\n"
                    "set your personal timezone with <code>/settimezone &lt;city&gt;</code>."
                )
            sent = await message.reply(
                f"ℹ️ <b>No timezones to convert to</b>\n\n{hint}",
                parse_mode=ParseMode.HTML
            )
            if not is_private:
                await schedule_auto_delete(chat_id, sent.id)
            return

        # Perform the conversion
        result = services.timezone.convert_time(
            time_str,
            source_tz,
            target_timezones
        )

        if result is None:
            sent = await message.reply(
                f"❌ <b>Invalid Time Format</b>\n\n"
                f"Could not parse <code>{time_str}</code>.\n\n"
                f"<b>Supported formats:</b>\n"
                f"• 24-hour: <code>18:00</code>, <code>14:30</code>, <code>0900</code>\n"
                f"• 12-hour: <code>6pm</code>, <code>3:30am</code>, <code>12:00pm</code>",
                parse_mode=ParseMode.HTML
            )
            if not is_private:
                await schedule_auto_delete(chat_id, sent.id)
            return

        sent = await message.reply(result, parse_mode=ParseMode.HTML)

        # Auto-delete in groups
        if not is_private:
            await schedule_auto_delete(chat_id, sent.id)

        logger.info(
            f"Time conversion by user {user_id}: "
            f"{time_str} {tz_query} -> {len(target_timezones)} targets"
        )
