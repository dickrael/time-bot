"""
Timezone Service for Time Bot.

Handles:
- Timezone alias resolution
- Time formatting with country names
- Time conversion between timezones
- IANA timezone validation
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from zoneinfo import ZoneInfo, available_timezones
import re

# Handle imports for both direct execution and module execution
try:
    from ..config import TIMEZONE_ALIASES, TIMEZONE_COUNTRIES, CLOCK_EMOJIS, COUNTRY_FLAGS
    from ..storage import JsonStore
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import TIMEZONE_ALIASES, TIMEZONE_COUNTRIES, CLOCK_EMOJIS, COUNTRY_FLAGS
    from storage import JsonStore

# Try to import pycountry for better country/flag detection
try:
    import pycountry
    HAS_PYCOUNTRY = True
except ImportError:
    HAS_PYCOUNTRY = False

logger = logging.getLogger(__name__)

# Pre-compute available timezones for validation
VALID_TIMEZONES = available_timezones()

# IANA timezone to ISO country code mapping (for common timezones)
# This supplements pycountry for cases where city → country isn't obvious
TZ_TO_COUNTRY_CODE = {
    # Special cases and cities that need explicit mapping
    "Europe/Istanbul": "TR",
    "Europe/London": "GB",
    "Europe/Belfast": "GB",
    "America/New_York": "US",
    "America/Los_Angeles": "US",
    "America/Chicago": "US",
    "America/Denver": "US",
    "America/Phoenix": "US",
    "America/Anchorage": "US",
    "Asia/Kolkata": "IN",
    "Asia/Calcutta": "IN",
    "Asia/Hong_Kong": "HK",
    "Asia/Tokyo": "JP",
    "Asia/Seoul": "KR",
    "Asia/Shanghai": "CN",
    "Asia/Singapore": "SG",
    "Asia/Dubai": "AE",
    "Asia/Tashkent": "UZ",
    "Asia/Samarkand": "UZ",
    "Europe/Moscow": "RU",
    "Europe/Paris": "FR",
    "Europe/Berlin": "DE",
    "Europe/Rome": "IT",
    "Europe/Madrid": "ES",
    "Europe/Amsterdam": "NL",
    "Europe/Brussels": "BE",
    "Europe/Vienna": "AT",
    "Europe/Zurich": "CH",
    "Europe/Stockholm": "SE",
    "Europe/Oslo": "NO",
    "Europe/Copenhagen": "DK",
    "Europe/Helsinki": "FI",
    "Europe/Warsaw": "PL",
    "Europe/Prague": "CZ",
    "Europe/Budapest": "HU",
    "Europe/Athens": "GR",
    "Europe/Lisbon": "PT",
    "Europe/Dublin": "IE",
    "Europe/Belgrade": "RS",
    "Europe/Bucharest": "RO",
    "Europe/Sofia": "BG",
    "Europe/Zagreb": "HR",
    "Europe/Ljubljana": "SI",
    "Europe/Bratislava": "SK",
    "Europe/Sarajevo": "BA",
    "Europe/Skopje": "MK",
    "Europe/Podgorica": "ME",
    "Europe/Tirana": "AL",
    "Europe/Riga": "LV",
    "Europe/Vilnius": "LT",
    "Europe/Tallinn": "EE",
    "Europe/Minsk": "BY",
    "Europe/Chisinau": "MD",
    "Europe/Kiev": "UA",
    "Europe/Kyiv": "UA",
    "Australia/Sydney": "AU",
    "Australia/Melbourne": "AU",
    "Australia/Brisbane": "AU",
    "Australia/Perth": "AU",
    "Australia/Adelaide": "AU",
    "Pacific/Auckland": "NZ",
    "Africa/Cairo": "EG",
    "Africa/Johannesburg": "ZA",
    "Africa/Lagos": "NG",
    "Africa/Nairobi": "KE",
    "Africa/Casablanca": "MA",
    "America/Toronto": "CA",
    "America/Vancouver": "CA",
    "America/Mexico_City": "MX",
    "America/Sao_Paulo": "BR",
    "America/Buenos_Aires": "AR",
    "America/Argentina/Buenos_Aires": "AR",
    "America/Lima": "PE",
    "America/Bogota": "CO",
    "America/Santiago": "CL",
    "Asia/Manila": "PH",
    "Asia/Bangkok": "TH",
    "Asia/Jakarta": "ID",
    "Asia/Kuala_Lumpur": "MY",
    "Asia/Ho_Chi_Minh": "VN",
    "Asia/Riyadh": "SA",
    "Asia/Tehran": "IR",
    "Asia/Jerusalem": "IL",
    "Asia/Karachi": "PK",
    "Asia/Dhaka": "BD",
    "Asia/Taipei": "TW",
    "Asia/Almaty": "KZ",
}


class TimezoneService:
    """
    Service for timezone operations.

    Uses Python's zoneinfo for reliable timezone handling.
    """

    def __init__(self, store: JsonStore):
        self.store = store
        self._alias_map = TIMEZONE_ALIASES.copy()
        self._country_map = TIMEZONE_COUNTRIES.copy()
        self._flag_map = COUNTRY_FLAGS.copy()

    def get_country(self, tz_id: str) -> str:
        """Get country name for a timezone ID."""
        # First try our manual mapping
        if tz_id in self._country_map:
            return self._country_map[tz_id]

        # Try to get country from IANA → country code mapping + pycountry
        if HAS_PYCOUNTRY and tz_id in TZ_TO_COUNTRY_CODE:
            country_code = TZ_TO_COUNTRY_CODE[tz_id]
            try:
                country = pycountry.countries.get(alpha_2=country_code)
                if country:
                    return country.name
            except Exception:
                pass

        return ""

    def get_flag(self, country: str) -> str:
        """Get flag emoji for a country name."""
        # First try our manual mapping
        if country in self._flag_map:
            return self._flag_map[country]

        # Try to get flag from pycountry
        if HAS_PYCOUNTRY and country:
            try:
                # Try to find by name
                c = pycountry.countries.search_fuzzy(country)
                if c:
                    # Convert country code to flag emoji
                    code = c[0].alpha_2
                    flag = "".join(chr(0x1F1E6 + ord(char) - ord('A')) for char in code)
                    return flag
            except Exception:
                pass

        return ""

    def get_country_and_flag(self, tz_id: str) -> Tuple[str, str]:
        """Get both country name and flag for a timezone ID."""
        # First try our manual mapping
        if tz_id in self._country_map:
            country = self._country_map[tz_id]
            flag = self._flag_map.get(country, "")
            if not flag and HAS_PYCOUNTRY:
                flag = self.get_flag(country)
            return country, flag

        # Try pycountry with TZ mapping
        if HAS_PYCOUNTRY and tz_id in TZ_TO_COUNTRY_CODE:
            country_code = TZ_TO_COUNTRY_CODE[tz_id]
            try:
                country_obj = pycountry.countries.get(alpha_2=country_code)
                if country_obj:
                    # Convert country code to flag emoji
                    flag = "".join(chr(0x1F1E6 + ord(char) - ord('A')) for char in country_code)
                    return country_obj.name, flag
            except Exception:
                pass

        return "", ""

    def get_clock_emoji(self, hour: int) -> str:
        """Get clock emoji for the given hour."""
        return CLOCK_EMOJIS[hour % 24]

    async def resolve_timezone(self, query: str) -> Optional[Tuple[str, str]]:
        """
        Resolve a timezone query to (IANA_ID, display_name).

        Returns None if timezone cannot be resolved.
        """
        query = query.strip()
        query_lower = query.lower()

        # Check cache first
        cached = await self.store.get_cached_timezone(query_lower)
        if cached:
            return (cached, self._make_display_name(cached))

        # 1. Direct IANA ID match
        if query in VALID_TIMEZONES:
            await self.store.cache_timezone(query_lower, query)
            return (query, self._make_display_name(query))

        # 2. Case-insensitive IANA ID match
        for tz in VALID_TIMEZONES:
            if tz.lower() == query_lower:
                await self.store.cache_timezone(query_lower, tz)
                return (tz, self._make_display_name(tz))

        # 3. Check configured aliases
        if query_lower in self._alias_map:
            tz_id = self._alias_map[query_lower]
            await self.store.cache_timezone(query_lower, tz_id)
            return (tz_id, self._make_display_name(tz_id))

        # 4. Partial match on city name in IANA IDs
        for tz in VALID_TIMEZONES:
            parts = tz.split("/")
            if len(parts) >= 2:
                city = parts[-1].replace("_", " ").lower()
                if query_lower == city:
                    await self.store.cache_timezone(query_lower, tz)
                    return (tz, self._make_display_name(tz))

        # 5. Fuzzy match - timezone contains query
        matches = []
        for tz in VALID_TIMEZONES:
            if query_lower in tz.lower():
                matches.append(tz)

        if len(matches) == 1:
            tz_id = matches[0]
            await self.store.cache_timezone(query_lower, tz_id)
            return (tz_id, self._make_display_name(tz_id))

        if matches:
            matches.sort(key=len)
            tz_id = matches[0]
            await self.store.cache_timezone(query_lower, tz_id)
            return (tz_id, self._make_display_name(tz_id))

        logger.warning(f"Could not resolve timezone: {query}")
        return None

    def _make_display_name(self, tz_id: str) -> str:
        """Create a human-readable display name from IANA ID."""
        if "/" in tz_id:
            city = tz_id.split("/")[-1]
            return city.replace("_", " ")
        return tz_id

    def get_current_time(self, tz_id: str) -> datetime:
        """Get the current time in a specific timezone."""
        try:
            tz = ZoneInfo(tz_id)
            return datetime.now(tz)
        except Exception as e:
            logger.error(f"Error getting time for {tz_id}: {e}")
            return datetime.now(ZoneInfo("UTC"))

    def format_time(self, dt: datetime, include_seconds: bool = False) -> str:
        """Format a datetime for display."""
        if include_seconds:
            return dt.strftime("%H:%M:%S")
        return dt.strftime("%H:%M")

    def format_offset(self, dt: datetime) -> str:
        """Format UTC offset nicely."""
        offset = dt.strftime("%z")
        if offset:
            hours = int(offset[:3])
            mins = int(offset[0] + offset[3:5])
            if mins == 0:
                return f"UTC{hours:+d}"
            else:
                return f"UTC{hours:+d}:{abs(mins):02d}"
        return "UTC"

    def format_time_entry(self, tz_id: str, display_name: str, show_utc_offset: bool = False) -> str:
        """
        Format a single timezone entry with city, country, flag, and time.

        Example: "🇺🇿 Tashkent, Uzbekistan: <b>00:55</b>"
        """
        dt = self.get_current_time(tz_id)
        time_str = self.format_time(dt)
        country, flag = self.get_country_and_flag(tz_id)

        # Build location string
        if country and flag:
            location = f"{flag} {display_name}, {country}"
        elif country:
            location = f"{display_name}, {country}"
        else:
            location = display_name

        if show_utc_offset:
            offset_str = self.format_offset(dt)
            return f"{location}: <b>{time_str}</b> ({offset_str})"
        else:
            return f"{location}: <b>{time_str}</b>"

    def format_all_times(
        self,
        timezones: Dict[str, "TimezoneEntry"],
        is_live: bool = False,
        show_utc_offset: bool = False
    ) -> str:
        """
        Format current times for all group timezones.

        Uses blockquote formatting. Sorted earliest to latest by UTC offset.
        """
        if not timezones:
            return "No timezones configured for this group.\n\nAdmins can add timezones with /addtime <code>&lt;city&gt;</code>"

        lines = ["<b>Current Times</b>\n"]

        # Sort by UTC offset (earliest → latest)
        sorted_tzs = sorted(
            timezones.values(),
            key=lambda e: self.get_current_time(e.tz).utcoffset() or timedelta(0)
        )

        # Build blockquote with entries
        blockquote_lines = []
        for entry in sorted_tzs:
            dt = self.get_current_time(entry.tz)
            time_str = self.format_time(dt)
            country, flag = self.get_country_and_flag(entry.tz)

            # Build location string
            if country and flag:
                location = f"{flag} {entry.display_name}, {country}"
            elif country:
                location = f"{entry.display_name}, {country}"
            else:
                location = entry.display_name

            # Build time display (bold time)
            if show_utc_offset:
                offset_str = self.format_offset(dt)
                blockquote_lines.append(f"{location}: <b>{time_str}</b> ({offset_str})")
            else:
                blockquote_lines.append(f"{location}: <b>{time_str}</b>")

        lines.append("<blockquote>" + "\n".join(blockquote_lines) + "</blockquote>")

        if is_live:
            lines.append("\n<i>🔄 Live updates every 25s</i>")

        return "\n".join(lines)

    def convert_time(
        self,
        time_str: str,
        from_tz: str,
        to_timezones: List[Tuple[str, str]]
    ) -> Optional[str]:
        """
        Convert a time from one timezone to multiple others.
        """
        parsed_time = self._parse_time(time_str)
        if parsed_time is None:
            return None

        hour, minute = parsed_time

        try:
            src_tz = ZoneInfo(from_tz)
            now = datetime.now(src_tz)
            src_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        except Exception as e:
            logger.error(f"Error creating source datetime: {e}")
            return None

        src_display = self._make_display_name(from_tz)
        src_country = self.get_country(from_tz)
        src_flag = self.get_flag(src_country)

        if src_country and src_flag:
            src_full = f"{src_flag} {src_display}, {src_country}"
        elif src_country:
            src_full = f"{src_display}, {src_country}"
        else:
            src_full = src_display

        lines = [
            "<b>Time Conversion</b>",
            f"\n{time_str} in <b>{src_full}</b>\n"
        ]

        # Build blockquote with conversions
        blockquote_lines = []
        for tz_id, display_name in to_timezones:
            try:
                target_tz = ZoneInfo(tz_id)
                target_dt = src_dt.astimezone(target_tz)
                target_time = self.format_time(target_dt)
                country = self.get_country(tz_id)
                flag = self.get_flag(country)

                day_diff = target_dt.date() - src_dt.date()
                if day_diff.days == 1:
                    day_marker = " (+1 day)"
                elif day_diff.days == -1:
                    day_marker = " (-1 day)"
                else:
                    day_marker = ""

                # Build location string
                if country and flag and "(you)" not in display_name:
                    location = f"{flag} {display_name}, {country}"
                elif country and "(you)" not in display_name:
                    location = f"{display_name}, {country}"
                else:
                    location = display_name

                blockquote_lines.append(f"{location}: <b>{target_time}</b>{day_marker}")
            except Exception as e:
                logger.error(f"Error converting to {tz_id}: {e}")
                blockquote_lines.append(f"{display_name}: conversion error")

        lines.append("<blockquote>" + "\n".join(blockquote_lines) + "</blockquote>")

        return "\n".join(lines)

    def _parse_time(self, time_str: str) -> Optional[Tuple[int, int]]:
        """Parse various time formats into (hour, minute)."""
        time_str = time_str.strip().lower()

        # Try 24h format: HH:MM
        match = re.match(r"^(\d{1,2}):(\d{2})$", time_str)
        if match:
            hour, minute = int(match.group(1)), int(match.group(2))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return (hour, minute)

        # Try 24h compact: HHMM
        match = re.match(r"^(\d{2})(\d{2})$", time_str)
        if match:
            hour, minute = int(match.group(1)), int(match.group(2))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return (hour, minute)

        # Try 12h format: H:MMam/pm or Hpm
        match = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)$", time_str)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            period = match.group(3)

            if 1 <= hour <= 12 and 0 <= minute <= 59:
                if period == "pm" and hour != 12:
                    hour += 12
                elif period == "am" and hour == 12:
                    hour = 0
                return (hour, minute)

        # Try just hour: "18"
        match = re.match(r"^(\d{1,2})$", time_str)
        if match:
            hour = int(match.group(1))
            if 0 <= hour <= 23:
                return (hour, 0)

        return None

    def get_user_time_display(self, tz_id: str, display_name: str) -> str:
        """Format user's current time for /timehere."""
        dt = self.get_current_time(tz_id)
        day = dt.strftime("%A")
        country = self.get_country(tz_id)
        flag = self.get_flag(country)

        if country and flag:
            location = f"{flag} {display_name}, {country}"
        elif country:
            location = f"{display_name}, {country}"
        else:
            location = display_name

        return (
            f"<b>Your Current Time</b>\n\n"
            f"<b>{location}</b>\n"
            f"{day}, {dt.strftime('%B %d, %Y')}\n"
            f"<b>{dt.strftime('%H:%M:%S')}</b>"
        )


# Import for type hint only
try:
    from ..storage.schemas import TimezoneEntry
except ImportError:
    from storage.schemas import TimezoneEntry
