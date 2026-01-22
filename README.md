# Time Bot

A Telegram bot for managing and displaying timezones in group chats. Features live-updating time displays, timezone conversions, and personal timezone settings.

## Features

- **Live Time Display** - `/time_live` shows continuously updating times (every 25 seconds)
- **Static Time Display** - `/time` shows current times for all group timezones
- **Time Conversion** - `/when 18:00 Tokyo` converts times between zones
- **Personal Timezone** - Each user can set their own timezone
- **Country Flags** - Displays country flags next to timezone names
- **Auto-Delete** - Bot messages in groups auto-delete to reduce clutter
- **Owner Mode** - Restrict bot to basic commands only
- **Admin Controls** - Group admins manage timezone lists
- **Per-User Cooldowns** - Prevents spam in groups
- **Persistent Storage** - All data survives bot restarts

## Commands

### Everyone
| Command | Description |
|---------|-------------|
| `/time` | Show current times for all group timezones |
| `/timehere` | Show your personal current time |
| `/when <time> <zone>` | Convert time to group timezones |
| `/settimezone <city>` | Set your personal timezone |
| `/mytimezone` | Check your timezone setting |
| `/help` | Show help message |

### Admins Only
| Command | Description |
|---------|-------------|
| `/time_live` | Start live-updating time display |
| `/addtime <city>` | Add a timezone to the group |
| `/removetime <city>` | Remove a timezone from the group |
| `/listtimes` | List all configured timezones |
| `/timeconfig` | View/edit group settings |
| `/timeconfig cooldown <sec>` | Set command cooldown |
| `/timeconfig offset on/off` | Show/hide UTC offsets |
| `/timeexport` | Export group data as CSV |
| `/timehealth` | Check bot health status |

### Owner Only
| Command | Description |
|---------|-------------|
| `/ownermode on/off` | Enable/disable restricted mode |

## Installation

### Prerequisites
- Python 3.10+
- Telegram API credentials from [my.telegram.org](https://my.telegram.org)
- Bot token from [@BotFather](https://t.me/BotFather)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/dickrael/time-bot.git
cd time-bot
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
```

5. Run the bot:
```bash
python -m timebot.main
```

## Configuration

Edit `config.py` to customize:

- `OWNER_ID` - Your Telegram user ID for owner commands
- `TIME_UPDATE_INTERVAL` - Seconds between live updates (default: 25)
- `TIME_COOLDOWN_SECONDS` - Default cooldown per user (default: 30)
- `TIMEZONE_ALIASES` - Custom timezone shortcuts
- `TIMEZONE_COUNTRIES` - Timezone to country mappings
- `COUNTRY_FLAGS` - Country to flag emoji mappings

## Project Structure

```
timebot/
├── main.py              # Entry point
├── config.py            # Configuration
├── requirements.txt     # Dependencies
├── handlers/            # Command handlers
│   ├── admin_cmds.py    # Admin commands
│   ├── user_cmds.py     # User commands
│   ├── time_cmd.py      # /time command
│   ├── when_cmd.py      # /when command
│   ├── timehere_cmd.py  # /timehere command
│   ├── start_help.py    # /start and /help
│   ├── owner_cmds.py    # Owner commands
│   └── common.py        # Shared utilities
├── services/            # Business logic
│   ├── timezone_service.py   # Timezone operations
│   ├── task_manager.py       # Background tasks
│   └── permission_service.py # Permission checks
├── storage/             # Data persistence
│   ├── json_store.py    # JSON file storage
│   └── schemas.py       # Data structures
├── langs/               # Localization
│   └── en.py            # English strings
└── data/                # Runtime data (gitignored)
    ├── groups.json      # Group configurations
    ├── users.json       # User preferences
    ├── state.json       # Bot state
    └── cache.json       # Timezone cache
```

## Timezone Input Formats

The bot accepts various timezone formats:

- **City names**: `Tokyo`, `New York`, `London`
- **Country names**: `Japan`, `Germany`, `UK`
- **Abbreviations**: `PST`, `EST`, `CET`, `JST`
- **IANA IDs**: `America/New_York`, `Europe/London`

## Time Input Formats

For `/when` command:

- **24-hour**: `18:00`, `14:30`, `0900`
- **12-hour**: `6pm`, `3:30am`, `12:00pm`

## Auto-Delete Timing

Messages auto-delete in groups to reduce clutter:

| Command Type | Delete After |
|--------------|--------------|
| `/time` | 25 seconds |
| `/timehere` | 30 seconds |
| `/when` | 45 seconds |
| Admin commands | 30 seconds |
| User commands | 30 seconds |
| `/start`, `/help` | 45 seconds |
| `/time_live` | Never (updates forever) |

## License

MIT License

## Contributing

Pull requests are welcome. For major changes, please open an issue first.
