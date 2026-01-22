"""
Task Manager for Time Bot.

Handles the lifecycle of live-updating /time_live messages.
Now supports forever updates (no lifetime limit) with 25-second intervals.

Key changes from original:
- No lifetime limit - updates forever until cancelled
- 25-second update interval
- Better error handling with FloodWait support
- Automatic cleanup on failure
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, TYPE_CHECKING

from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, MessageNotModified, MessageIdInvalid

# Handle imports for both direct execution and module execution
try:
    from ..config import TIME_UPDATE_INTERVAL
    from ..storage import JsonStore
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import TIME_UPDATE_INTERVAL
    from storage import JsonStore

if TYPE_CHECKING:
    from pyrogram import Client
    try:
        from .timezone_service import TimezoneService
    except ImportError:
        from services.timezone_service import TimezoneService

logger = logging.getLogger(__name__)


class TaskManager:
    """
    Manages live-updating /time_live message tasks.

    Features:
    - Only ONE active task per chat
    - Forever updates (no lifetime limit)
    - Safe cancellation on new /time_live
    - FloodWait handling
    - Automatic cleanup on errors
    """

    def __init__(
        self,
        store: JsonStore,
        tz_service: "TimezoneService"
    ):
        self.store = store
        self.tz_service = tz_service

        # Active tasks: chat_id -> asyncio.Task
        self._active_tasks: Dict[int, asyncio.Task] = {}

        # Lock to prevent race conditions
        self._lock = asyncio.Lock()

    async def start_time_task(
        self,
        client: "Client",
        chat_id: int,
        message_id: int
    ) -> None:
        """
        Start a new live-updating task for a /time_live message.

        If there's an existing task for this chat, it will be cancelled first.
        """
        async with self._lock:
            # Cancel existing task if any
            existing_task = self._active_tasks.get(chat_id)
            if existing_task and not existing_task.done():
                logger.info(f"Cancelling existing task for chat {chat_id}")
                existing_task.cancel()
                try:
                    await existing_task
                except asyncio.CancelledError:
                    pass

            # Record active message in persistent storage
            await self.store.set_active_time_message(chat_id, message_id)

            # Create and start the new task
            task = asyncio.create_task(
                self._update_loop(client, chat_id, message_id),
                name=f"time_live_{chat_id}"
            )
            self._active_tasks[chat_id] = task

            logger.info(f"Started live task for chat {chat_id}, message {message_id}")

    async def stop_time_task(self, chat_id: int) -> bool:
        """
        Stop the active /time_live task for a chat.

        Returns True if a task was stopped.
        """
        # Get task under lock, but release before awaiting to avoid deadlock
        async with self._lock:
            task = self._active_tasks.get(chat_id)

        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            return True
        return False

    async def refresh_live_message(self, client: "Client", chat_id: int) -> bool:
        """
        Immediately refresh the live message for a chat.

        Called when timezones are added/removed to update display instantly.
        Returns True if a live message was refreshed.
        """
        # Check if there's an active live message
        active = await self.store.get_active_time_message(chat_id)
        if not active:
            return False

        # Check if task is still running
        if not self.is_chat_active(chat_id):
            return False

        try:
            # Get current config and timezones
            config = await self.store.get_group_config(chat_id)
            timezones = await self.store.get_group_timezones(chat_id)

            # Format the updated message
            new_text = self.tz_service.format_all_times(
                timezones,
                is_live=True,
                show_utc_offset=config.show_utc_offset
            )

            # Edit the message
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=active.message_id,
                text=new_text,
                parse_mode=ParseMode.HTML
            )
            logger.info(f"Refreshed live message in chat {chat_id}")
            return True

        except Exception as e:
            logger.warning(f"Failed to refresh live message in chat {chat_id}: {e}")
            return False

    async def _update_loop(
        self,
        client: "Client",
        chat_id: int,
        message_id: int
    ) -> None:
        """
        The main update loop for a /time_live message.

        Runs FOREVER until cancelled or edit fails permanently.
        """
        consecutive_errors = 0
        max_errors = 5
        last_text = ""

        try:
            while True:
                # Wait for next update interval
                await asyncio.sleep(TIME_UPDATE_INTERVAL)

                # Get current config and timezones for this chat
                config = await self.store.get_group_config(chat_id)
                timezones = await self.store.get_group_timezones(chat_id)

                # Format the updated message (with is_live=True)
                new_text = self.tz_service.format_all_times(
                    timezones,
                    is_live=True,
                    show_utc_offset=config.show_utc_offset
                )

                # Skip if text hasn't changed (prevents MESSAGE_NOT_MODIFIED)
                if new_text == last_text:
                    continue

                # Try to edit the message
                try:
                    await client.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=new_text,
                        parse_mode=ParseMode.HTML
                    )
                    consecutive_errors = 0
                    last_text = new_text

                except MessageNotModified:
                    # Content hasn't changed, this is fine
                    pass

                except FloodWait as e:
                    # Handle rate limiting
                    wait_time = e.value
                    logger.warning(f"FloodWait for chat {chat_id}: waiting {wait_time}s")
                    await asyncio.sleep(wait_time)

                except MessageIdInvalid:
                    # Message was deleted
                    logger.info(f"Message deleted in chat {chat_id}, stopping task")
                    break

                except Exception as e:
                    consecutive_errors += 1
                    error_msg = str(e).lower()

                    # Check for permanent failures
                    permanent_errors = [
                        "message not found",
                        "message to edit not found",
                        "message was deleted",
                        "chat not found",
                        "bot was kicked",
                        "have no rights",
                        "chat_write_forbidden",
                        "user_banned_in_channel",
                    ]

                    if any(err in error_msg for err in permanent_errors):
                        logger.info(f"Permanent error for chat {chat_id}: {e}")
                        break

                    if consecutive_errors >= max_errors:
                        logger.warning(f"Too many errors for chat {chat_id}, stopping")
                        break

                    logger.warning(f"Error editing message in chat {chat_id}: {e}")

        except asyncio.CancelledError:
            logger.info(f"Task for chat {chat_id} was cancelled")
            raise

        finally:
            await self._cleanup_task(chat_id)

    async def _cleanup_task(self, chat_id: int) -> None:
        """Clean up after a task ends."""
        async with self._lock:
            self._active_tasks.pop(chat_id, None)
            await self.store.clear_active_time_message(chat_id)
            logger.debug(f"Cleaned up task for chat {chat_id}")

    def get_active_task_count(self) -> int:
        """Get the number of currently active tasks."""
        return sum(1 for t in self._active_tasks.values() if not t.done())

    def get_active_chats(self) -> list:
        """Get list of chat IDs with active tasks."""
        return [
            chat_id for chat_id, task in self._active_tasks.items()
            if not task.done()
        ]

    def is_chat_active(self, chat_id: int) -> bool:
        """Check if a chat has an active live task."""
        task = self._active_tasks.get(chat_id)
        return task is not None and not task.done()

    async def start_auto_delete_worker(self, client: "Client") -> None:
        """Start the auto-delete background worker."""
        self._delete_worker = asyncio.create_task(
            self._auto_delete_loop(client),
            name="auto_delete_worker"
        )
        logger.info("Started auto-delete worker")

        # Process any pending deletes from before restart
        await self._process_pending_deletes(client)

    async def _auto_delete_loop(self, client: "Client") -> None:
        """Background loop that processes scheduled message deletions."""
        try:
            while True:
                await asyncio.sleep(5)  # Check every 5 seconds
                await self._process_pending_deletes(client)
        except asyncio.CancelledError:
            logger.info("Auto-delete worker cancelled")
            raise

    async def _process_pending_deletes(self, client: "Client") -> None:
        """Process all messages that are due for deletion."""
        pending = await self.store.get_pending_deletes()

        for chat_id, message_id, key in pending:
            try:
                await client.delete_messages(chat_id, message_id)
                logger.debug(f"Auto-deleted message {message_id} in chat {chat_id}")
            except Exception as e:
                logger.debug(f"Could not delete message {message_id}: {e}")
            finally:
                await self.store.remove_scheduled_delete(key)

    async def shutdown(self) -> None:
        """Gracefully shutdown all active tasks."""
        logger.info("Shutting down task manager...")

        # Stop auto-delete worker
        if hasattr(self, '_delete_worker') and self._delete_worker and not self._delete_worker.done():
            self._delete_worker.cancel()
            try:
                await self._delete_worker
            except asyncio.CancelledError:
                pass

        async with self._lock:
            tasks = list(self._active_tasks.values())

        if not tasks:
            return

        for task in tasks:
            if not task.done():
                task.cancel()

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"Shut down {len(tasks)} task(s)")
