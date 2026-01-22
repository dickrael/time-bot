"""
English translations for Time Bot.
All user-facing strings are defined here.
"""

STRINGS = {
    # ==================== START & HELP ====================
    "start_private": (
        "<b>Welcome to Time Bot!</b>\n\n"
        "I help you track times across different timezones in your groups.\n\n"
        "<b>Quick Start:</b>\n"
        "1. Add me to a group\n"
        "2. Make me admin (to delete messages)\n"
        "3. Use /addtime to add timezones\n"
        "4. Use /time to see current times\n\n"
        "Use /help for detailed commands."
    ),

    "start_group": (
        "<b>Time Bot</b> - Track times across timezones\n"
        "Tap the button below for usage guide."
    ),

    "start_button": "How to use",

    "help_text": (
        "<b>Time Bot Commands</b>\n\n"
        "<b>Everyone:</b>\n"
        "/time - Show current times (one-time)\n"
        "/timehere - Show your personal time\n"
        "/when <code>&lt;time&gt; &lt;zone&gt;</code> - Convert time\n"
        "/settimezone <code>&lt;city&gt;</code> - Set your timezone\n"
        "/mytimezone - Check your timezone\n"
        "/help - Show this help\n\n"
        "<b>Admins only:</b>\n"
        "/time_live - Live updating time display\n"
        "/addtime <code>&lt;city&gt;</code> - Add timezone to group\n"
        "/removetime <code>&lt;city&gt;</code> - Remove timezone\n"
        "/listtimes - List group timezones\n"
        "/timeconfig - Group settings\n"
        "/timeexport - Export data as CSV\n"
        "/timehealth - Bot health status\n\n"
        "<b>Examples:</b>\n"
        "<code>/addtime Tokyo</code>\n"
        "<code>/addtime New York</code>\n"
        "<code>/when 18:00 Tokyo</code>\n"
        "<code>/settimezone London</code>"
    ),

    "help_text_restricted": (
        "<b>Time Bot Commands</b>\n\n"
        "🔒 <i>Owner-only mode is active. Some commands are restricted.</i>\n\n"
        "<b>Available commands:</b>\n"
        "/time - Show current times (one-time)\n"
        "/timehere - Show your personal time\n"
        "/when <code>&lt;time&gt; &lt;zone&gt;</code> - Convert time\n"
        "/settimezone <code>&lt;city&gt;</code> - Set your timezone\n"
        "/mytimezone - Check your timezone\n"
        "/help - Show this help\n\n"
        "<b>Examples:</b>\n"
        "<code>/when 18:00 Tokyo</code>\n"
        "<code>/settimezone London</code>"
    ),

    # ==================== TIME DISPLAY ====================
    "time_header": "<b>Current Times</b>",

    "time_no_zones": (
        "No timezones configured for this group.\n\n"
        "Admins can add timezones with /addtime <code>&lt;city&gt;</code>"
    ),

    "time_entry": "{emoji} <b>{city}, {country}</b>: {time} ({offset})",

    "time_footer": "<i>Updated: {time} UTC</i>",

    "time_live_footer": "<i>Live updates every 25s</i>",

    "time_live_admin_only": (
        "<b>Permission Denied</b>\n\n"
        "Live time updates (/time_live) are only available to admins.\n"
        "Use /time for a one-time display."
    ),

    # ==================== COOLDOWN ====================
    "cooldown_active": (
        "<b>Cooldown Active</b>\n\n"
        "Please wait {seconds} seconds before using this command again."
    ),

    # ==================== TIMEZONE MANAGEMENT ====================
    "tz_added": (
        "<b>Timezone Added!</b>\n\n"
        "{emoji} <b>{city}, {country}</b>\n"
        "Current time: {time} ({offset})\n\n"
        "<i>Use /time to see all group timezones.</i>"
    ),

    "tz_already_exists": (
        "<b>Already Exists</b>\n\n"
        "This timezone is already configured for this group."
    ),

    "tz_removed": (
        "<b>Timezone Removed</b>\n\n"
        "Removed <b>{name}</b> from this group."
    ),

    "tz_not_found": (
        "<b>Not Found</b>\n\n"
        "No timezone matching <code>{query}</code> found.\n\n"
        "Use /listtimes to see configured timezones."
    ),

    "tz_unknown": (
        "<b>Unknown Timezone</b>\n\n"
        "Could not resolve <code>{query}</code>.\n\n"
        "<b>Try using:</b>\n"
        "• City names: <code>Tokyo</code>, <code>London</code>\n"
        "• Abbreviations: <code>PST</code>, <code>EST</code>\n"
        "• IANA IDs: <code>America/New_York</code>"
    ),

    "tz_list_header": "<b>Group Timezones</b>",

    "tz_list_empty": (
        "<b>No Timezones Configured</b>\n\n"
        "Admins can add timezones with /addtime <code>&lt;city&gt;</code>"
    ),

    "tz_list_footer": "<i>Total: {count} timezone(s)</i>",

    # ==================== USER TIMEZONE ====================
    "user_tz_header": "<b>Your Current Time</b>",

    "user_tz_not_set": (
        "<b>No Timezone Set</b>\n\n"
        "Set your timezone with:\n"
        "<code>/settimezone &lt;city&gt;</code>\n\n"
        "<b>Examples:</b>\n"
        "• <code>/settimezone Tokyo</code>\n"
        "• <code>/settimezone New York</code>\n"
        "• <code>/settimezone PST</code>"
    ),

    "user_tz_set": (
        "<b>Timezone Set!</b>\n\n"
        "{time_display}\n\n"
        "<i>Use /timehere to check your time anytime.</i>"
    ),

    "user_tz_current": (
        "<b>Current timezone:</b> {name}\n"
        "<code>{tz_id}</code>"
    ),

    # ==================== TIME CONVERSION ====================
    "when_header": "<b>Time Conversion</b>",

    "when_source": "{time} in <b>{zone}</b>",

    "when_no_targets": (
        "<b>No timezones to convert to</b>\n\n"
        "{hint}"
    ),

    "when_hint_private": "Set your timezone with <code>/settimezone &lt;city&gt;</code>",

    "when_hint_group": (
        "Add group timezones with <code>/addtime &lt;city&gt;</code> or\n"
        "set your personal timezone with <code>/settimezone &lt;city&gt;</code>"
    ),

    "when_invalid_time": (
        "<b>Invalid Time Format</b>\n\n"
        "Could not parse <code>{time}</code>.\n\n"
        "<b>Supported formats:</b>\n"
        "• 24-hour: <code>18:00</code>, <code>14:30</code>\n"
        "• 12-hour: <code>6pm</code>, <code>3:30am</code>"
    ),

    # ==================== PERMISSIONS ====================
    "permission_denied": (
        "<b>Permission Denied</b>\n\n"
        "This command is only available to group administrators."
    ),

    # ==================== CONFIG ====================
    "config_header": "<b>Group Configuration</b>",

    "config_cooldown_updated": (
        "<b>Configuration Updated</b>\n\n"
        "Cooldown set to <b>{seconds}</b> seconds."
    ),

    "config_invalid_value": (
        "<b>Invalid Value</b>\n\n"
        "Cooldown must be a number between 0 and 3600."
    ),

    # ==================== HEALTH ====================
    "health_header": "<b>Bot Health Status</b>",

    # ==================== USAGE ====================
    "usage_addtime": (
        "<b>Usage:</b> <code>/addtime &lt;city or timezone&gt;</code>\n\n"
        "<b>Examples:</b>\n"
        "• <code>/addtime Tokyo</code>\n"
        "• <code>/addtime New York</code>\n"
        "• <code>/addtime America/Los_Angeles</code>"
    ),

    "usage_removetime": (
        "<b>Usage:</b> <code>/removetime &lt;city or timezone&gt;</code>"
    ),

    "usage_when": (
        "<b>Usage:</b> <code>/when &lt;time&gt; &lt;timezone&gt;</code>\n\n"
        "<b>Examples:</b>\n"
        "• <code>/when 18:00 Tokyo</code>\n"
        "• <code>/when 3pm PST</code>\n"
        "• <code>/when 14:30 London</code>"
    ),

    "usage_settimezone": (
        "<b>Set Your Timezone</b>\n\n"
        "{current}"
        "<b>Usage:</b> <code>/settimezone &lt;city&gt;</code>\n\n"
        "<b>Examples:</b>\n"
        "• <code>/settimezone Tokyo</code>\n"
        "• <code>/settimezone New York</code>\n"
        "• <code>/settimezone PST</code>"
    ),

    "usage_timeconfig": (
        "<b>Usage:</b>\n"
        "• <code>/timeconfig</code> - Show current config\n"
        "• <code>/timeconfig cooldown &lt;seconds&gt;</code> - Set cooldown"
    ),

    # ==================== ERRORS ====================
    "error_generic": "An error occurred. Please try again.",

    "error_user_not_found": "Could not identify user.",
}
