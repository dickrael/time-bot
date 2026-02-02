"""
Timezone Service for Time Bot.

Handles:
- Timezone alias resolution
- Time formatting with country names
- Time conversion between timezones
- IANA timezone validation

Uses WorldTimeAPI for accurate time fetching.
Uses pytz + pycountry for automatic country/flag detection.
"""

import asyncio
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from zoneinfo import ZoneInfo, available_timezones
import re

import aiohttp

# Handle imports for both direct execution and module execution
try:
    from ..config import TIMEZONE_ALIASES, CLOCK_EMOJIS
    from ..storage import JsonStore
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import TIMEZONE_ALIASES, CLOCK_EMOJIS
    from storage import JsonStore

# Import pytz for timezone→country mapping (required)
import pytz

# Build complete timezone → country code mapping from pytz
TZ_TO_COUNTRY_CODE: Dict[str, str] = {}
for country_code, timezones in pytz.country_timezones.items():
    for tz in timezones:
        TZ_TO_COUNTRY_CODE[tz] = country_code

# Add mappings for deprecated/link timezone IDs
TZ_TO_COUNTRY_CODE.update({
    "Asia/Tel_Aviv": "IL",  # Link to Asia/Jerusalem
    "Israel": "IL",         # Legacy name
    "Turkey": "TR",         # Legacy name for Europe/Istanbul
    "Egypt": "EG",          # Legacy name
    "HST": "US",            # Hawaii Standard Time
    "NZ-CHAT": "NZ",        # Chatham Islands
    "Pacific/Samoa": "WS",  # Samoa
})

# Auto-generate country name -> main timezone mappings
COUNTRY_TO_TIMEZONE: Dict[str, str] = {}
for country_code, tz_list in pytz.country_timezones.items():
    if tz_list:
        main_tz = tz_list[0]  # First timezone is usually the main one
        try:
            country_obj = pycountry.countries.get(alpha_2=country_code)
            if country_obj:
                # Add country name (lowercase)
                COUNTRY_TO_TIMEZONE[country_obj.name.lower()] = main_tz
                # Add common name if different
                if hasattr(country_obj, 'common_name'):
                    COUNTRY_TO_TIMEZONE[country_obj.common_name.lower()] = main_tz
        except Exception:
            pass

logger.info(f"Auto-generated {len(COUNTRY_TO_TIMEZONE)} country->timezone mappings")

# Import pycountry for country names (required)
import pycountry

logger = logging.getLogger(__name__)

# Pre-compute available timezones for validation
VALID_TIMEZONES = available_timezones()

# WorldTimeAPI settings
WORLDTIME_API_URL = "http://worldtimeapi.org/api/timezone"
TIME_CACHE_TTL = 30  # Cache time data for 30 seconds
API_TIMEOUT = 10  # API request timeout in seconds

# Valid timezones from WorldTimeAPI (populated at startup)
WORLDTIME_VALID_TZS: set = set()


class TimezoneService:
    """
    Service for timezone operations.

    Uses WorldTimeAPI for accurate time fetching with caching.
    Country/flag detection via pytz + pycountry (no manual mappings).
    """

    def __init__(self, store: JsonStore):
        self.store = store
        self._alias_map = TIMEZONE_ALIASES.copy()
        # Cache: {tz_id: {"datetime": datetime_obj, "utc_offset": str, "fetched_at": timestamp}}
        self._time_cache: Dict[str, Dict[str, Any]] = {}
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=10)  # Limit concurrent connections
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
                connector=connector
            )
        return self._session

    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def load_api_timezones(self) -> bool:
        """Fetch and cache the list of valid timezones from WorldTimeAPI."""
        global WORLDTIME_VALID_TZS
        try:
            session = await self._get_session()
            async with session.get(WORLDTIME_API_URL) as response:
                if response.status == 200:
                    data = await response.json()
                    WORLDTIME_VALID_TZS = set(data)
                    logger.info(f"Loaded {len(WORLDTIME_VALID_TZS)} valid timezones from WorldTimeAPI")
                    return True
                else:
                    logger.warning(f"Failed to load API timezones: status {response.status}")
                    return False
        except Exception as e:
            logger.warning(f"Failed to load API timezones: {e}")
            return False

    def _country_code_to_flag(self, country_code: str) -> str:
        """Convert ISO 3166-1 alpha-2 country code to flag emoji."""
        return "".join(chr(0x1F1E6 + ord(char) - ord('A')) for char in country_code.upper())

    def get_country(self, tz_id: str) -> str:
        """Get country name for a timezone ID using pytz + pycountry."""
        if tz_id in TZ_TO_COUNTRY_CODE:
            country_code = TZ_TO_COUNTRY_CODE[tz_id]
            try:
                country = pycountry.countries.get(alpha_2=country_code)
                if country:
                    return country.name
            except Exception:
                pass
        return ""

    def get_flag(self, tz_id: str) -> str:
        """Get flag emoji for a timezone ID."""
        if tz_id in TZ_TO_COUNTRY_CODE:
            country_code = TZ_TO_COUNTRY_CODE[tz_id]
            return self._country_code_to_flag(country_code)
        return ""

    def get_country_and_flag(self, tz_id: str) -> Tuple[str, str]:
        """Get both country name and flag for a timezone ID."""
        if tz_id in TZ_TO_COUNTRY_CODE:
            country_code = TZ_TO_COUNTRY_CODE[tz_id]
            try:
                country_obj = pycountry.countries.get(alpha_2=country_code)
                if country_obj:
                    flag = self._country_code_to_flag(country_code)
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
        Only returns timezones that exist in VALID_TIMEZONES.
        """
        query = query.strip()
        query_lower = query.lower()
        logger.debug(f"Resolving timezone query: '{query}' (lower: '{query_lower}')")

        # Check cache first (but validate it's still valid)
        cached = await self.store.get_cached_timezone(query_lower)
        if cached and cached in VALID_TIMEZONES:
            return (cached, self._make_display_name(cached))

        # 1. Check configured aliases FIRST (maps common names to proper IANA IDs)
        if query_lower in self._alias_map:
            tz_id = self._alias_map[query_lower]
            if tz_id in VALID_TIMEZONES:
                await self.store.cache_timezone(query_lower, tz_id)
                return (tz_id, self._make_display_name(tz_id))
            else:
                logger.warning(f"Alias '{query_lower}' points to invalid timezone: {tz_id}")

        # 1b. Check auto-generated country name mappings
        if query_lower in COUNTRY_TO_TIMEZONE:
            tz_id = COUNTRY_TO_TIMEZONE[query_lower]
            if tz_id in VALID_TIMEZONES:
                await self.store.cache_timezone(query_lower, tz_id)
                return (tz_id, self._make_display_name(tz_id))

        # 2. Direct IANA ID match (only for proper Area/Location format)
        if "/" in query and query in VALID_TIMEZONES:
            await self.store.cache_timezone(query_lower, query)
            return (query, self._make_display_name(query))

        # 3. Case-insensitive IANA ID match (only for proper Area/Location format)
        if "/" in query:
            for tz in VALID_TIMEZONES:
                if tz.lower() == query_lower:
                    await self.store.cache_timezone(query_lower, tz)
                    return (tz, self._make_display_name(tz))

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

    async def _fetch_time_from_api(self, tz_id: str) -> Optional[Dict[str, Any]]:
        """Fetch current time from WorldTimeAPI."""
        # Check against API's valid timezone list if available
        if WORLDTIME_VALID_TZS and tz_id not in WORLDTIME_VALID_TZS:
            logger.debug(f"Timezone not in API list: {tz_id}")
            return None

        # Fallback check: only fetch valid IANA timezone IDs (must contain '/')
        if "/" not in tz_id and tz_id != "UTC":
            logger.debug(f"Skipping invalid timezone ID for API: {tz_id}")
            return None

        try:
            session = await self._get_session()
            url = f"{WORLDTIME_API_URL}/{tz_id}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Parse the datetime string
                    dt_str = data.get("datetime", "")
                    utc_offset = data.get("utc_offset", "+00:00")

                    # Parse ISO format datetime
                    # Format: "2026-02-02T15:04:22.333448+05:00"
                    dt = datetime.fromisoformat(dt_str)

                    logger.info(f"WorldTimeAPI: {tz_id} = {dt.strftime('%H:%M:%S')}")
                    return {
                        "datetime": dt,
                        "utc_offset": utc_offset,
                        "fetched_at": time.time()
                    }
                else:
                    logger.warning(f"WorldTimeAPI returned {response.status} for {tz_id}")
                    return None
        except asyncio.TimeoutError:
            logger.debug(f"Timeout fetching time for {tz_id}")
            return None
        except aiohttp.ClientError as e:
            logger.debug(f"Network error fetching time for {tz_id}: {e}")
            return None
        except Exception as e:
            logger.debug(f"Error fetching time from API for {tz_id}: {e}")
            return None

    def _get_cached_time(self, tz_id: str) -> Optional[datetime]:
        """Get cached time if still valid."""
        if tz_id in self._time_cache:
            cached = self._time_cache[tz_id]
            age = time.time() - cached["fetched_at"]
            if age < TIME_CACHE_TTL:
                # Adjust cached time by elapsed seconds
                elapsed = timedelta(seconds=age)
                return cached["datetime"] + elapsed
        return None

    async def get_current_time_async(self, tz_id: str) -> datetime:
        """Get the current time in a specific timezone using WorldTimeAPI."""
        # Check cache first
        cached = self._get_cached_time(tz_id)
        if cached:
            return cached

        # Fetch from API
        api_result = await self._fetch_time_from_api(tz_id)
        if api_result:
            self._time_cache[tz_id] = api_result
            return api_result["datetime"]

        # Fallback to local zoneinfo
        logger.warning(f"Fallback to local time for {tz_id}")
        return self.get_current_time(tz_id)

    def get_current_time(self, tz_id: str) -> datetime:
        """Get the current time in a specific timezone (sync fallback)."""
        try:
            tz = ZoneInfo(tz_id)
            return datetime.now(tz)
        except Exception as e:
            logger.error(f"Error getting time for {tz_id}: {e}")
            return datetime.now(ZoneInfo("UTC"))

    async def prefetch_times(self, tz_ids: List[str]) -> None:
        """Prefetch times for multiple timezones in parallel."""
        # Filter out already cached
        to_fetch = [tz for tz in tz_ids if self._get_cached_time(tz) is None]

        if not to_fetch:
            return

        # Fetch all in parallel
        tasks = [self._fetch_time_from_api(tz) for tz in to_fetch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for tz_id, result in zip(to_fetch, results):
            if isinstance(result, dict) and result:
                self._time_cache[tz_id] = result

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

    async def format_all_times(
        self,
        timezones: Dict[str, "TimezoneEntry"],
        is_live: bool = False,
        show_utc_offset: bool = False
    ) -> str:
        """
        Format current times for all group timezones.

        Uses WorldTimeAPI for accurate times. Fetches all in parallel.
        Uses blockquote formatting. Sorted earliest to latest by UTC offset.
        """
        if not timezones:
            return "No timezones configured for this group.\n\nAdmins can add timezones with /addtime <code>&lt;city&gt;</code>"

        # Prefetch all times in parallel
        tz_ids = [entry.tz for entry in timezones.values()]
        await self.prefetch_times(tz_ids)

        lines = ["<b>Current Times</b>\n"]

        # Get times and sort by UTC offset
        tz_times: List[Tuple["TimezoneEntry", datetime]] = []
        for entry in timezones.values():
            dt = await self.get_current_time_async(entry.tz)
            tz_times.append((entry, dt))

        # Sort by UTC offset (earliest → latest)
        tz_times.sort(key=lambda x: x[1].utcoffset() or timedelta(0))

        # Build blockquote with entries
        blockquote_lines = []
        for entry, dt in tz_times:
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
            lines.append("\n<i>🔄 Live updates every 60s</i>")

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
        src_flag = self.get_flag(from_tz)

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
                flag = self.get_flag(tz_id)

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

    async def get_user_time_display(self, tz_id: str, display_name: str) -> str:
        """Format user's current time for /timehere."""
        dt = await self.get_current_time_async(tz_id)
        day = dt.strftime("%A")
        country = self.get_country(tz_id)
        flag = self.get_flag(tz_id)

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
