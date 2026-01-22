"""
Admin command handlers.

All commands in this module require admin permissions in groups.
- /addtime - Add a timezone to the group
- /removetime - Remove a timezone from the group
- /listtimes - List all group timezones
- /timeexport - Export group data as JSON
- /timehealth - Show bot health info
- /timeconfig - Show/edit group configuration
"""

import csv
import io
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatType, ParseMode

# Auto-delete delay for admin commands in groups (seconds)
AUTO_DELETE_DELAY = 30

# Handle imports for both direct execution and module execution
try:
    from .common import is_admin, check_owner_only_mode
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from common import is_admin, check_owner_only_mode

logger = logging.getLogger(__name__)


def register_admin_handlers(app: Client, services):
    """Register admin command handlers."""

    async def schedule_auto_delete(chat_id: int, message_id: int):
        """Schedule a message for auto-deletion in groups."""
        delete_at = datetime.utcnow() + timedelta(seconds=AUTO_DELETE_DELAY)
        await services.store.schedule_delete(chat_id, message_id, delete_at)

    @app.on_message(filters.command("addtime"))
    async def handle_addtime(client: Client, message: Message):
        """
        Handle /addtime command (admin only).

        Adds a timezone to the group.
        Usage: /addtime <city or timezone>
        """
        user_id = message.from_user.id if message.from_user else 0

        # Check owner-only mode
        if await check_owner_only_mode(services, user_id, "addtime", message):
            return

        chat_id = message.chat.id
        is_group = message.chat.type != ChatType.PRIVATE

        # Check admin permission
        if is_group:
            user_is_admin = await is_admin(
                client, message.chat.id, message.from_user.id
            )
            if not user_is_admin:
                sent = await message.reply(
                    "⛔ <b>Permission Denied</b>\n\n"
                    "Only group administrators can add timezones.",
                    parse_mode=ParseMode.HTML
                )
                await schedule_auto_delete(chat_id, sent.id)
                return

        # Parse arguments
        args = message.text.split(maxsplit=1)

        if len(args) < 2:
            sent = await message.reply(
                "📖 <b>Usage:</b> <code>/addtime &lt;city or timezone&gt;</code>\n\n"
                "<b>Examples:</b>\n"
                "• <code>/addtime Tokyo</code>\n"
                "• <code>/addtime New York</code>\n"
                "• <code>/addtime America/Los_Angeles</code>\n"
                "• <code>/addtime PST</code>\n"
                "• <code>/addtime UK</code>",
                parse_mode=ParseMode.HTML
            )
            if is_group:
                await schedule_auto_delete(chat_id, sent.id)
            return

        tz_query = args[1].strip()

        # Resolve the timezone
        resolved = await services.timezone.resolve_timezone(tz_query)

        if not resolved:
            sent = await message.reply(
                f"❌ <b>Unknown Timezone</b>\n\n"
                f"Could not resolve <code>{tz_query}</code>.\n\n"
                f"<b>Try using:</b>\n"
                f"• City names: <code>Tokyo</code>, <code>London</code>, <code>Paris</code>\n"
                f"• Abbreviations: <code>PST</code>, <code>EST</code>, <code>CET</code>\n"
                f"• IANA IDs: <code>America/New_York</code>",
                parse_mode=ParseMode.HTML
            )
            if is_group:
                await schedule_auto_delete(chat_id, sent.id)
            return

        tz_id, display_name = resolved

        # Try to add the timezone
        success = await services.store.add_group_timezone(
            chat_id, tz_id, display_name, user_id
        )

        if not success:
            sent = await message.reply(
                f"⚠️ <b>Already Exists</b>\n\n"
                f"The timezone <b>{display_name}</b> (<code>{tz_id}</code>) is already configured for this group.",
                parse_mode=ParseMode.HTML
            )
            if is_group:
                await schedule_auto_delete(chat_id, sent.id)
            return

        # Show confirmation with current time
        current_time = services.timezone.get_current_time(tz_id)
        time_str = services.timezone.format_time(current_time)

        sent = await message.reply(
            f"✅ <b>Timezone Added!</b>\n\n"
            f"📍 <b>{display_name}</b> (<code>{tz_id}</code>)\n"
            f"🕐 Current time: {time_str}\n\n"
            f"<i>Use /time to see all group timezones.</i>",
            parse_mode=ParseMode.HTML
        )
        if is_group:
            await schedule_auto_delete(chat_id, sent.id)
            # Refresh live message if active
            await services.tasks.refresh_live_message(client, chat_id)

        logger.info(f"Added timezone {tz_id} to chat {chat_id} by user {user_id}")

    @app.on_message(filters.command("removetime"))
    async def handle_removetime(client: Client, message: Message):
        """
        Handle /removetime command (admin only).

        Removes a timezone from the group.
        Usage: /removetime <city or timezone>
        """
        user_id = message.from_user.id if message.from_user else 0

        # Check owner-only mode
        if await check_owner_only_mode(services, user_id, "removetime", message):
            return

        chat_id = message.chat.id
        is_group = message.chat.type != ChatType.PRIVATE

        # Check admin permission
        if is_group:
            user_is_admin = await is_admin(
                client, message.chat.id, message.from_user.id
            )
            if not user_is_admin:
                sent = await message.reply(
                    "⛔ <b>Permission Denied</b>\n\n"
                    "Only group administrators can remove timezones.",
                    parse_mode=ParseMode.HTML
                )
                await schedule_auto_delete(chat_id, sent.id)
                return

        # Parse arguments
        args = message.text.split(maxsplit=1)

        if len(args) < 2:
            # Show list of current timezones
            timezones = await services.store.get_group_timezones(chat_id)

            if not timezones:
                sent = await message.reply(
                    "📭 No timezones configured for this group.\n\n"
                    "Add one with <code>/addtime &lt;city&gt;</code>",
                    parse_mode=ParseMode.HTML
                )
                if is_group:
                    await schedule_auto_delete(chat_id, sent.id)
                return

            tz_list = "\n".join(
                f"• <code>{entry.display_name}</code> ({entry.tz})"
                for entry in timezones.values()
            )

            sent = await message.reply(
                f"📖 <b>Usage:</b> <code>/removetime &lt;city or timezone&gt;</code>\n\n"
                f"<b>Current timezones:</b>\n{tz_list}",
                parse_mode=ParseMode.HTML
            )
            if is_group:
                await schedule_auto_delete(chat_id, sent.id)
            return

        tz_query = args[1].strip()

        # Try to remove the timezone
        removed_name = await services.store.remove_group_timezone(chat_id, tz_query)

        if not removed_name:
            sent = await message.reply(
                f"❌ <b>Not Found</b>\n\n"
                f"No timezone matching <code>{tz_query}</code> found in this group.\n\n"
                f"Use /listtimes to see configured timezones.",
                parse_mode=ParseMode.HTML
            )
            if is_group:
                await schedule_auto_delete(chat_id, sent.id)
            return

        sent = await message.reply(
            f"✅ <b>Timezone Removed</b>\n\n"
            f"Removed <b>{removed_name}</b> from this group.",
            parse_mode=ParseMode.HTML
        )
        if is_group:
            await schedule_auto_delete(chat_id, sent.id)
            # Refresh live message if active
            await services.tasks.refresh_live_message(client, chat_id)

        logger.info(f"Removed timezone {removed_name} from chat {chat_id}")

    @app.on_message(filters.command("listtimes"))
    async def handle_listtimes(client: Client, message: Message):
        """
        Handle /listtimes command.

        Lists all timezones configured for the group.
        """
        chat_id = message.chat.id
        is_group = message.chat.type != ChatType.PRIVATE

        timezones = await services.store.get_group_timezones(chat_id)

        if not timezones:
            sent = await message.reply(
                "📭 <b>No Timezones Configured</b>\n\n"
                "This group has no timezones set up.\n\n"
                "Admins can add timezones with <code>/addtime &lt;city&gt;</code>",
                parse_mode=ParseMode.HTML
            )
            if is_group:
                await schedule_auto_delete(chat_id, sent.id)
            return

        lines = ["📋 <b>Group Timezones</b>\n"]

        for entry in timezones.values():
            current_time = services.timezone.get_current_time(entry.tz)
            time_str = services.timezone.format_time(current_time)
            lines.append(
                f"• <b>{entry.display_name}</b> - {time_str}\n"
                f"  <code>{entry.tz}</code>"
            )

        lines.append(f"\n<i>Total: {len(timezones)} timezone(s)</i>")

        sent = await message.reply("\n".join(lines), parse_mode=ParseMode.HTML)
        if is_group:
            await schedule_auto_delete(chat_id, sent.id)

    @app.on_message(filters.command("timeexport"))
    async def handle_timeexport(client: Client, message: Message):
        """
        Handle /timeexport command (admin only).

        Exports group timezone data as CSV to user's DM.
        """
        user_id = message.from_user.id if message.from_user else 0
        chat_id = message.chat.id

        # Check owner-only mode
        if await check_owner_only_mode(services, user_id, "timeexport", message):
            return

        # Check admin permission in groups
        if message.chat.type != ChatType.PRIVATE:
            user_is_admin = await is_admin(
                client, message.chat.id, message.from_user.id
            )
            if not user_is_admin:
                await message.reply(
                    "⛔ <b>Permission Denied</b>\n\n"
                    "Only group administrators can export data.",
                    parse_mode=ParseMode.HTML
                )
                return

        is_group = message.chat.type != ChatType.PRIVATE

        # Get group timezones
        timezones = await services.store.get_group_timezones(chat_id)

        if not timezones:
            sent = await message.reply(
                "📭 <b>No Data to Export</b>\n\n"
                "This group has no timezones configured.",
                parse_mode=ParseMode.HTML
            )
            if is_group:
                await schedule_auto_delete(chat_id, sent.id)
            return

        # Create CSV content
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)

        # Write header
        writer.writerow(["Timezone ID", "Display Name", "Added By", "Added At"])

        # Write data
        for entry in timezones.values():
            writer.writerow([
                entry.tz,
                entry.display_name,
                entry.added_by,
                entry.added_at
            ])

        # Convert to bytes for sending
        csv_content = csv_buffer.getvalue()
        csv_bytes = io.BytesIO(csv_content.encode("utf-8"))
        csv_bytes.name = f"timebot_export_{chat_id}.csv"

        # Try to send to user's DM
        try:
            await client.send_document(
                chat_id=user_id,
                document=csv_bytes,
                caption=f"📦 <b>Group Data Export</b>\n\n"
                        f"Exported {len(timezones)} timezone(s) from chat <code>{chat_id}</code>",
                parse_mode=ParseMode.HTML
            )

            # Confirm in the original chat
            if is_group:
                sent = await message.reply(
                    "✅ <b>Export Sent</b>\n\n"
                    "The CSV export has been sent to your DM.",
                    parse_mode=ParseMode.HTML
                )
                await schedule_auto_delete(chat_id, sent.id)
        except Exception as e:
            logger.error(f"Failed to send export to DM: {e}")
            sent = await message.reply(
                "❌ <b>Could not send DM</b>\n\n"
                "Please start a private chat with me first, then try again.",
                parse_mode=ParseMode.HTML
            )
            if is_group:
                await schedule_auto_delete(chat_id, sent.id)

    @app.on_message(filters.command("timehealth"))
    async def handle_timehealth(client: Client, message: Message):
        """
        Handle /timehealth command (admin only).

        Shows bot health status: JSON integrity, cache stats, active tasks.
        """
        user_id = message.from_user.id if message.from_user else 0
        chat_id = message.chat.id
        is_group = message.chat.type != ChatType.PRIVATE

        # Check owner-only mode
        if await check_owner_only_mode(services, user_id, "timehealth", message):
            return

        # Check admin permission
        if is_group:
            user_is_admin = await is_admin(
                client, message.chat.id, message.from_user.id
            )
            if not user_is_admin:
                sent = await message.reply(
                    "⛔ <b>Permission Denied</b>\n\n"
                    "Only group administrators can view health status.",
                    parse_mode=ParseMode.HTML
                )
                await schedule_auto_delete(chat_id, sent.id)
                return

        # Gather health info
        json_status = await services.store.check_integrity()
        cache_stats = await services.store.get_cache_stats()
        active_tasks = services.tasks.get_active_task_count()
        active_chats = services.tasks.get_active_chats()

        # Format JSON status
        json_lines = []
        for name, info in json_status.items():
            status = info["status"]
            size = info.get("size", 0)
            icon = "✅" if status == "ok" else "⚠️" if status == "missing" else "❌"
            json_lines.append(f"  {icon} {name}: {status} ({size} bytes)")

        lines = [
            "🏥 <b>Bot Health Status</b>\n",
            "<b>JSON Storage:</b>",
            *json_lines,
            "",
            "<b>Cache:</b>",
            f"  • Alias cache entries: {cache_stats['alias_cache_size']}",
            "",
            "<b>Active Tasks:</b>",
            f"  • Live /time messages: {active_tasks}",
        ]

        if active_chats:
            lines.append(f"  • Active in chats: {', '.join(map(str, active_chats))}")

        # Add current time
        utc_now = datetime.now(ZoneInfo("UTC"))
        lines.append(f"\n<i>Checked at {utc_now.strftime('%Y-%m-%d %H:%M:%S')} UTC</i>")

        sent = await message.reply("\n".join(lines), parse_mode=ParseMode.HTML)
        if is_group:
            await schedule_auto_delete(chat_id, sent.id)

    @app.on_message(filters.command("timeconfig"))
    async def handle_timeconfig(client: Client, message: Message):
        """
        Handle /timeconfig command (admin only).

        Shows and allows editing group configuration.
        Usage:
            /timeconfig - Show current config
            /timeconfig cooldown <seconds> - Set cooldown
        """
        user_id = message.from_user.id if message.from_user else 0
        chat_id = message.chat.id
        is_group = message.chat.type != ChatType.PRIVATE

        # Check owner-only mode
        if await check_owner_only_mode(services, user_id, "timeconfig", message):
            return

        # Check admin permission
        if is_group:
            user_is_admin = await is_admin(
                client, message.chat.id, message.from_user.id
            )
            if not user_is_admin:
                sent = await message.reply(
                    "⛔ <b>Permission Denied</b>\n\n"
                    "Only group administrators can view/edit configuration.",
                    parse_mode=ParseMode.HTML
                )
                await schedule_auto_delete(chat_id, sent.id)
                return

        args = message.text.split()

        # Get current config
        config = await services.store.get_group_config(chat_id)

        if len(args) == 1:
            # Show current config
            timezones = await services.store.get_group_timezones(chat_id)
            offset_status = "On" if config.show_utc_offset else "Off"

            sent = await message.reply(
                f"⚙️ <b>Group Configuration</b>\n\n"
                f"<b>Cooldown:</b> {config.cooldown_seconds} seconds\n"
                f"<b>Show UTC offset:</b> {offset_status}\n"
                f"<b>Timezones:</b> {len(timezones)} configured\n\n"
                f"<b>Edit settings:</b>\n"
                f"• <code>/timeconfig cooldown &lt;seconds&gt;</code>\n"
                f"• <code>/timeconfig offset on/off</code>",
                parse_mode=ParseMode.HTML
            )
            if is_group:
                await schedule_auto_delete(chat_id, sent.id)
            return

        if len(args) >= 3 and args[1].lower() == "cooldown":
            try:
                new_cooldown = int(args[2])
                if new_cooldown < 0 or new_cooldown > 3600:
                    raise ValueError("Out of range")

                config.cooldown_seconds = new_cooldown
                await services.store.set_group_config(chat_id, config)

                sent = await message.reply(
                    f"✅ <b>Configuration Updated</b>\n\n"
                    f"Cooldown set to <b>{new_cooldown}</b> seconds.",
                    parse_mode=ParseMode.HTML
                )
                if is_group:
                    await schedule_auto_delete(chat_id, sent.id)

                logger.info(f"Updated cooldown for chat {chat_id} to {new_cooldown}s")
                return

            except ValueError:
                sent = await message.reply(
                    "❌ <b>Invalid Value</b>\n\n"
                    "Cooldown must be a number between 0 and 3600.",
                    parse_mode=ParseMode.HTML
                )
                if is_group:
                    await schedule_auto_delete(chat_id, sent.id)
                return

        if len(args) >= 3 and args[1].lower() == "offset":
            value = args[2].lower()
            if value in ("on", "true", "1", "yes"):
                config.show_utc_offset = True
                await services.store.set_group_config(chat_id, config)
                sent = await message.reply(
                    "✅ <b>Configuration Updated</b>\n\n"
                    "UTC offset display is now <b>enabled</b>.",
                    parse_mode=ParseMode.HTML
                )
                if is_group:
                    await schedule_auto_delete(chat_id, sent.id)
            elif value in ("off", "false", "0", "no"):
                config.show_utc_offset = False
                await services.store.set_group_config(chat_id, config)
                sent = await message.reply(
                    "✅ <b>Configuration Updated</b>\n\n"
                    "UTC offset display is now <b>disabled</b>.",
                    parse_mode=ParseMode.HTML
                )
                if is_group:
                    await schedule_auto_delete(chat_id, sent.id)
            else:
                sent = await message.reply(
                    "❌ <b>Invalid Value</b>\n\n"
                    "Use <code>/timeconfig offset on</code> or <code>/timeconfig offset off</code>",
                    parse_mode=ParseMode.HTML
                )
                if is_group:
                    await schedule_auto_delete(chat_id, sent.id)
            return

        sent = await message.reply(
            "📖 <b>Usage:</b>\n"
            "• <code>/timeconfig</code> - Show current config\n"
            "• <code>/timeconfig cooldown &lt;seconds&gt;</code> - Set cooldown (0-3600)\n"
            "• <code>/timeconfig offset on/off</code> - Show/hide UTC offset",
            parse_mode=ParseMode.HTML
        )
        if is_group:
            await schedule_auto_delete(chat_id, sent.id)
