"""
Configuration module for Time Bot.
All configurable settings are centralized here.
"""

import os
from pathlib import Path

# Bot credentials - set via environment variables
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Owner ID - has special privileges
OWNER_ID = 674193259

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# JSON storage files
GROUPS_FILE = DATA_DIR / "groups.json"
USERS_FILE = DATA_DIR / "users.json"
STATE_FILE = DATA_DIR / "state.json"
CACHE_FILE = DATA_DIR / "cache.json"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Time settings
TIME_UPDATE_INTERVAL = 60  # seconds between live message updates
TIME_COOLDOWN_SECONDS = 30  # default cooldown for /time command per user

# Clock emojis for different hours (0-23)
CLOCK_EMOJIS = [
    "🕛", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚",
    "🕛", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚"
]

# Timezone to country mapping (for display purposes)
TIMEZONE_COUNTRIES = {
    # Americas
    "America/New_York": "USA",
    "America/Los_Angeles": "USA",
    "America/Chicago": "USA",
    "America/Denver": "USA",
    "America/Phoenix": "USA",
    "America/Anchorage": "USA",
    "America/Toronto": "Canada",
    "America/Vancouver": "Canada",
    "America/Mexico_City": "Mexico",
    "America/Sao_Paulo": "Brazil",
    "America/Buenos_Aires": "Argentina",
    "America/Argentina/Buenos_Aires": "Argentina",
    "America/Lima": "Peru",
    "America/Bogota": "Colombia",
    "America/Santiago": "Chile",

    # Europe
    "Europe/London": "UK",
    "Europe/Paris": "France",
    "Europe/Berlin": "Germany",
    "Europe/Rome": "Italy",
    "Europe/Madrid": "Spain",
    "Europe/Amsterdam": "Netherlands",
    "Europe/Brussels": "Belgium",
    "Europe/Vienna": "Austria",
    "Europe/Zurich": "Switzerland",
    "Europe/Stockholm": "Sweden",
    "Europe/Oslo": "Norway",
    "Europe/Copenhagen": "Denmark",
    "Europe/Helsinki": "Finland",
    "Europe/Warsaw": "Poland",
    "Europe/Prague": "Czech Republic",
    "Europe/Budapest": "Hungary",
    "Europe/Athens": "Greece",
    "Europe/Istanbul": "Turkey",
    "Europe/Moscow": "Russia",
    "Europe/Kiev": "Ukraine",
    "Europe/Kyiv": "Ukraine",
    "Europe/Lisbon": "Portugal",
    "Europe/Dublin": "Ireland",
    "Europe/Belgrade": "Serbia",
    "Europe/Bucharest": "Romania",
    "Europe/Sofia": "Bulgaria",
    "Europe/Zagreb": "Croatia",
    "Europe/Ljubljana": "Slovenia",
    "Europe/Bratislava": "Slovakia",
    "Europe/Sarajevo": "Bosnia",
    "Europe/Skopje": "North Macedonia",
    "Europe/Podgorica": "Montenegro",
    "Europe/Tirana": "Albania",
    "Europe/Riga": "Latvia",
    "Europe/Vilnius": "Lithuania",
    "Europe/Tallinn": "Estonia",
    "Europe/Minsk": "Belarus",
    "Europe/Chisinau": "Moldova",
    "Europe/Luxembourg": "Luxembourg",
    "Europe/Monaco": "Monaco",
    "Europe/Malta": "Malta",
    "Europe/Andorra": "Andorra",
    "Europe/San_Marino": "San Marino",

    # Asia
    "Asia/Tokyo": "Japan",
    "Asia/Seoul": "South Korea",
    "Asia/Shanghai": "China",
    "Asia/Hong_Kong": "Hong Kong",
    "Asia/Singapore": "Singapore",
    "Asia/Bangkok": "Thailand",
    "Asia/Jakarta": "Indonesia",
    "Asia/Manila": "Philippines",
    "Asia/Kuala_Lumpur": "Malaysia",
    "Asia/Ho_Chi_Minh": "Vietnam",
    "Asia/Kolkata": "India",
    "Asia/Mumbai": "India",
    "Asia/Delhi": "India",
    "Asia/Dubai": "UAE",
    "Asia/Riyadh": "Saudi Arabia",
    "Asia/Tehran": "Iran",
    "Asia/Jerusalem": "Israel",
    "Asia/Tashkent": "Uzbekistan",
    "Asia/Almaty": "Kazakhstan",
    "Asia/Karachi": "Pakistan",
    "Asia/Dhaka": "Bangladesh",
    "Asia/Taipei": "Taiwan",

    # Oceania
    "Australia/Sydney": "Australia",
    "Australia/Melbourne": "Australia",
    "Australia/Brisbane": "Australia",
    "Australia/Perth": "Australia",
    "Australia/Adelaide": "Australia",
    "Pacific/Auckland": "New Zealand",
    "Pacific/Chatham": "New Zealand",
    "Pacific/Fiji": "Fiji",
    "Pacific/Honolulu": "USA",
    "Pacific/Guam": "USA",

    # Africa
    "Africa/Cairo": "Egypt",
    "Africa/Johannesburg": "South Africa",
    "Africa/Lagos": "Nigeria",
    "Africa/Nairobi": "Kenya",
    "Africa/Casablanca": "Morocco",

    # Special
    "UTC": "UTC",
}

# Country name to flag emoji mapping
COUNTRY_FLAGS = {
    # Americas
    "USA": "🇺🇸",
    "Canada": "🇨🇦",
    "Mexico": "🇲🇽",
    "Brazil": "🇧🇷",
    "Argentina": "🇦🇷",
    "Peru": "🇵🇪",
    "Colombia": "🇨🇴",
    "Chile": "🇨🇱",

    # Europe
    "UK": "🇬🇧",
    "France": "🇫🇷",
    "Germany": "🇩🇪",
    "Italy": "🇮🇹",
    "Spain": "🇪🇸",
    "Netherlands": "🇳🇱",
    "Belgium": "🇧🇪",
    "Austria": "🇦🇹",
    "Switzerland": "🇨🇭",
    "Sweden": "🇸🇪",
    "Norway": "🇳🇴",
    "Denmark": "🇩🇰",
    "Finland": "🇫🇮",
    "Poland": "🇵🇱",
    "Czech Republic": "🇨🇿",
    "Hungary": "🇭🇺",
    "Greece": "🇬🇷",
    "Turkey": "🇹🇷",
    "Russia": "🇷🇺",
    "Ukraine": "🇺🇦",
    "Portugal": "🇵🇹",
    "Ireland": "🇮🇪",
    "Serbia": "🇷🇸",
    "Romania": "🇷🇴",
    "Bulgaria": "🇧🇬",
    "Croatia": "🇭🇷",
    "Slovenia": "🇸🇮",
    "Slovakia": "🇸🇰",
    "Bosnia": "🇧🇦",
    "North Macedonia": "🇲🇰",
    "Montenegro": "🇲🇪",
    "Albania": "🇦🇱",
    "Latvia": "🇱🇻",
    "Lithuania": "🇱🇹",
    "Estonia": "🇪🇪",
    "Belarus": "🇧🇾",
    "Moldova": "🇲🇩",
    "Luxembourg": "🇱🇺",
    "Monaco": "🇲🇨",
    "Malta": "🇲🇹",
    "Andorra": "🇦🇩",
    "San Marino": "🇸🇲",

    # Asia
    "Japan": "🇯🇵",
    "South Korea": "🇰🇷",
    "China": "🇨🇳",
    "Hong Kong": "🇭🇰",
    "Singapore": "🇸🇬",
    "Thailand": "🇹🇭",
    "Indonesia": "🇮🇩",
    "Philippines": "🇵🇭",
    "Malaysia": "🇲🇾",
    "Vietnam": "🇻🇳",
    "India": "🇮🇳",
    "UAE": "🇦🇪",
    "Saudi Arabia": "🇸🇦",
    "Iran": "🇮🇷",
    "Israel": "🇮🇱",
    "Uzbekistan": "🇺🇿",
    "Kazakhstan": "🇰🇿",
    "Pakistan": "🇵🇰",
    "Bangladesh": "🇧🇩",
    "Taiwan": "🇹🇼",

    # Oceania
    "Australia": "🇦🇺",
    "New Zealand": "🇳🇿",
    "Fiji": "🇫🇯",

    # Africa
    "Egypt": "🇪🇬",
    "South Africa": "🇿🇦",
    "Nigeria": "🇳🇬",
    "Kenya": "🇰🇪",
    "Morocco": "🇲🇦",

    # Regions/Special
    "UTC": "🌐",
    "Americas": "🌎",
    "Europe": "🌍",
    "Asia": "🌏",
    "Africa": "🌍",
    "Pacific": "🌊",
    "Atlantic": "🌊",
    "Indian Ocean": "🌊",
}

# Timezone alias mappings (common shortcuts -> IANA timezone IDs)
TIMEZONE_ALIASES = {
    # US shortcuts
    "pst": "America/Los_Angeles",
    "pdt": "America/Los_Angeles",
    "mst": "America/Denver",
    "mdt": "America/Denver",
    "cst": "America/Chicago",
    "cdt": "America/Chicago",
    "est": "America/New_York",
    "edt": "America/New_York",
    "et": "America/New_York",
    "pt": "America/Los_Angeles",
    "ct": "America/Chicago",
    "mt": "America/Denver",

    # City shortcuts
    "nyc": "America/New_York",
    "la": "America/Los_Angeles",
    "sf": "America/Los_Angeles",
    "chicago": "America/Chicago",
    "denver": "America/Denver",
    "london": "Europe/London",
    "paris": "Europe/Paris",
    "berlin": "Europe/Berlin",
    "tokyo": "Asia/Tokyo",
    "sydney": "Australia/Sydney",
    "melbourne": "Australia/Melbourne",
    "dubai": "Asia/Dubai",
    "singapore": "Asia/Singapore",
    "hongkong": "Asia/Hong_Kong",
    "hk": "Asia/Hong_Kong",
    "seoul": "Asia/Seoul",
    "mumbai": "Asia/Kolkata",
    "delhi": "Asia/Kolkata",
    "moscow": "Europe/Moscow",
    "amsterdam": "Europe/Amsterdam",
    "zurich": "Europe/Zurich",
    "toronto": "America/Toronto",
    "vancouver": "America/Vancouver",
    "tashkent": "Asia/Tashkent",
    "istanbul": "Europe/Istanbul",
    "casablanca": "Africa/Casablanca",
    "cairo": "Africa/Cairo",
    "belgrade": "Europe/Belgrade",
    "bucharest": "Europe/Bucharest",
    "sofia": "Europe/Sofia",
    "zagreb": "Europe/Zagreb",

    # European shortcuts
    "uk": "Europe/London",
    "gmt": "Europe/London",
    "utc": "UTC",
    "cet": "Europe/Paris",
    "eet": "Europe/Helsinki",
    "wet": "Europe/Lisbon",

    # Asian shortcuts
    "jst": "Asia/Tokyo",
    "kst": "Asia/Seoul",
    "ist": "Asia/Kolkata",
    "cst_china": "Asia/Shanghai",
    "hkt": "Asia/Hong_Kong",
    "sgt": "Asia/Singapore",

    # Australian shortcuts
    "aest": "Australia/Sydney",
    "aedt": "Australia/Sydney",
    "awst": "Australia/Perth",

    # Country names
    "japan": "Asia/Tokyo",
    "korea": "Asia/Seoul",
    "india": "Asia/Kolkata",
    "china": "Asia/Shanghai",
    "germany": "Europe/Berlin",
    "france": "Europe/Paris",
    "italy": "Europe/Rome",
    "spain": "Europe/Madrid",
    "brazil": "America/Sao_Paulo",
    "mexico": "America/Mexico_City",
    "argentina": "America/Argentina/Buenos_Aires",
    "russia": "Europe/Moscow",
    "australia": "Australia/Sydney",
    "canada": "America/Toronto",
    "uzbekistan": "Asia/Tashkent",

    # Pacific / Special timezones
    "chatham": "Pacific/Chatham",
    "nz-chat": "Pacific/Chatham",
    "chatham islands": "Pacific/Chatham",
    "chathamislands": "Pacific/Chatham",
    "hawaii": "Pacific/Honolulu",
    "hst": "Pacific/Honolulu",
    "honolulu": "Pacific/Honolulu",
    "fiji": "Pacific/Fiji",
    "samoa": "Pacific/Samoa",
    "tahiti": "Pacific/Tahiti",
    "guam": "Pacific/Guam",

    # Israel (prevent duplicates)
    "israel": "Asia/Jerusalem",
    "tel aviv": "Asia/Jerusalem",
    "telaviv": "Asia/Jerusalem",
    "jerusalem": "Asia/Jerusalem",

    # Country names -> capital/main timezone
    "turkey": "Europe/Istanbul",
    "türkiye": "Europe/Istanbul",
    "egypt": "Africa/Cairo",
    "nigeria": "Africa/Lagos",
    "kenya": "Africa/Nairobi",
    "morocco": "Africa/Casablanca",
    "south africa": "Africa/Johannesburg",
    "uae": "Asia/Dubai",
    "saudi arabia": "Asia/Riyadh",
    "pakistan": "Asia/Karachi",
    "bangladesh": "Asia/Dhaka",
    "indonesia": "Asia/Jakarta",
    "philippines": "Asia/Manila",
    "vietnam": "Asia/Ho_Chi_Minh",
    "thailand": "Asia/Bangkok",
    "malaysia": "Asia/Kuala_Lumpur",
    "singapore": "Asia/Singapore",
    "taiwan": "Asia/Taipei",
    "hong kong": "Asia/Hong_Kong",
    "new zealand": "Pacific/Auckland",
    "iran": "Asia/Tehran",
    "iraq": "Asia/Baghdad",
    "ethiopia": "Africa/Addis_Ababa",
    "zambia": "Africa/Lusaka",
    "gabon": "Africa/Libreville",
}

# Bot commands to register
BOT_COMMANDS = [
    ("time", "Show current times for all group timezones"),
    ("time_live", "Live updating time display (admins)"),
    ("timehere", "Show your personal time"),
    ("when", "Convert time between timezones"),
    ("settimezone", "Set your personal timezone"),
    ("mytimezone", "Check your timezone setting"),
    ("addtime", "Add timezone to group (admins)"),
    ("removetime", "Remove timezone from group (admins)"),
    ("listtimes", "List all group timezones"),
    ("timeconfig", "Group settings (admins)"),
    ("help", "Show help message"),
]

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
