"""
Time Bot - Main Entry Point

A Telegram bot for managing timezones in groups with live-updating time displays.

Features:
- /time - Live-updating display of all group timezones
- /timehere - Show user's personal time
- /when - Convert times between timezones
- /addtime, /removetime - Manage group timezones (admin only)
- /settimezone - Set personal timezone

Usage:
    python -m timebot.main

Environment Variables:
    API_ID - Telegram API ID
    API_HASH - Telegram API Hash
    BOT_TOKEN - Bot token from @BotFather
"""

import asyncio
import logging
import signal
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Load .env file BEFORE importing config
import os
_this_dir = Path(__file__).parent
_env_file = _this_dir / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        # python-dotenv not installed, load manually
        with open(_env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

from pyrogram import Client

# Handle imports for both direct execution and module execution
from pyrogram.types import BotCommand

try:
    from .config import (
        API_ID, API_HASH, BOT_TOKEN,
        GROUPS_FILE, USERS_FILE, STATE_FILE, CACHE_FILE,
        LOG_LEVEL, BOT_COMMANDS
    )
    from .storage import JsonStore
    from .services import TimezoneService, TaskManager, PermissionService
    from .handlers import register_all_handlers
except ImportError:
    # Running directly (python main.py)
    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent))
    from config import (
        API_ID, API_HASH, BOT_TOKEN,
        GROUPS_FILE, USERS_FILE, STATE_FILE, CACHE_FILE,
        LOG_LEVEL, BOT_COMMANDS
    )
    from storage import JsonStore
    from services import TimezoneService, TaskManager, PermissionService
    from handlers import register_all_handlers

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


@dataclass
class Services:
    """Container for all bot services."""
    store: JsonStore
    timezone: TimezoneService
    tasks: TaskManager
    permissions: PermissionService


class TimeBot:
    """
    Main bot class that orchestrates all components.

    Lifecycle:
    1. Initialize storage
    2. Create services
    3. Register handlers
    4. Start bot
    5. Handle graceful shutdown
    """

    def __init__(self):
        self.client: Optional[Client] = None
        self.services: Optional[Services] = None
        self._shutdown_event = asyncio.Event()

    async def start(self):
        """Initialize and start the bot."""
        logger.info("Starting Time Bot...")

        # Validate configuration
        if not all([API_ID, API_HASH, BOT_TOKEN]):
            logger.error(
                "Missing configuration! Set API_ID, API_HASH, and BOT_TOKEN "
                "environment variables."
            )
            sys.exit(1)

        # Initialize storage
        store = JsonStore(
            groups_file=GROUPS_FILE,
            users_file=USERS_FILE,
            state_file=STATE_FILE,
            cache_file=CACHE_FILE
        )
        await store.initialize()

        # Create services
        timezone_service = TimezoneService(store)
        task_manager = TaskManager(store, timezone_service)
        permission_service = PermissionService()

        self.services = Services(
            store=store,
            timezone=timezone_service,
            tasks=task_manager,
            permissions=permission_service
        )

        # Create Pyrogram client
        self.client = Client(
            name="timebot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workdir=str(GROUPS_FILE.parent)  # Store session in data dir
        )

        # Register all command handlers
        register_all_handlers(self.client, self.services)

        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()

        # Start the bot
        logger.info("Connecting to Telegram...")
        await self.client.start()

        me = await self.client.get_me()
        logger.info(f"Bot started as @{me.username} (ID: {me.id})")

        # Register bot commands with Telegram
        await self._register_commands()

        # Start auto-delete worker
        await self.services.tasks.start_auto_delete_worker(self.client)

        # Resume any active /time_live tasks from before restart
        resumed = await self.services.tasks.resume_active_tasks(self.client)
        if resumed:
            logger.info(f"Resumed {resumed} live time task(s)")

        # Wait for shutdown signal
        await self._shutdown_event.wait()

        # Graceful shutdown
        await self.shutdown()

    async def shutdown(self):
        """Gracefully shutdown the bot."""
        logger.info("Shutting down...")

        # Stop all active tasks
        if self.services:
            await self.services.tasks.shutdown()

        # Stop the client
        if self.client:
            await self.client.stop()

        logger.info("Shutdown complete.")

    async def _register_commands(self):
        """Register bot commands with Telegram."""
        try:
            commands = [
                BotCommand(command=cmd, description=desc)
                for cmd, desc in BOT_COMMANDS
            ]
            await self.client.set_bot_commands(commands)
            logger.info(f"Registered {len(commands)} bot commands")
        except Exception as e:
            logger.warning(f"Failed to register bot commands: {e}")

    def _setup_signal_handlers(self):
        """Setup handlers for graceful shutdown on SIGINT/SIGTERM."""
        loop = asyncio.get_event_loop()

        def signal_handler():
            logger.info("Received shutdown signal")
            self._shutdown_event.set()

        # Handle both SIGINT (Ctrl+C) and SIGTERM
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, signal_handler)
            except NotImplementedError:
                # Windows doesn't support add_signal_handler
                signal.signal(sig, lambda s, f: signal_handler())


def main():
    """Entry point for the bot."""
    bot = TimeBot()

    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
