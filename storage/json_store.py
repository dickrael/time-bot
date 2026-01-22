"""
JSON Storage Engine for Time Bot.

Features:
- Atomic writes (write to temp file, then rename)
- Thread-safe operations via asyncio locks
- Auto-save on modifications
- Crash-safe recovery
- In-memory caching with disk persistence
"""

import json
import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Any, Tuple
from datetime import datetime
import shutil

# Handle imports for both direct execution and module execution
try:
    from .schemas import (
        GroupData, UserData, StateData, CacheData,
        TimezoneEntry, ActiveTimeMessage, GroupConfig, UserCooldown, ScheduledDelete
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from schemas import (
        GroupData, UserData, StateData, CacheData,
        TimezoneEntry, ActiveTimeMessage, GroupConfig, UserCooldown, ScheduledDelete
    )

logger = logging.getLogger(__name__)


class JsonStore:
    """
    Centralized JSON storage manager.

    All data is held in memory and persisted to disk atomically.
    Uses locks to prevent concurrent write corruption.
    """

    def __init__(
        self,
        groups_file: Path,
        users_file: Path,
        state_file: Path,
        cache_file: Path
    ):
        self.groups_file = groups_file
        self.users_file = users_file
        self.state_file = state_file
        self.cache_file = cache_file

        # In-memory data stores
        self._groups: Dict[str, GroupData] = {}
        self._users: Dict[str, UserData] = {}
        self._state: StateData = StateData()
        self._cache: CacheData = CacheData()

        # Locks for thread-safe operations
        self._groups_lock = asyncio.Lock()
        self._users_lock = asyncio.Lock()
        self._state_lock = asyncio.Lock()
        self._cache_lock = asyncio.Lock()

        self._initialized = False

    async def initialize(self) -> None:
        """Load all data from disk into memory."""
        if self._initialized:
            return

        logger.info("Initializing JSON storage...")

        # Load groups
        self._groups = await self._load_file(
            self.groups_file,
            lambda d: {k: GroupData.from_dict(v) for k, v in d.items()}
        ) or {}

        # Load users
        self._users = await self._load_file(
            self.users_file,
            lambda d: {k: UserData.from_dict(v) for k, v in d.items()}
        ) or {}

        # Load state
        self._state = await self._load_file(
            self.state_file,
            lambda d: StateData.from_dict(d)
        ) or StateData()

        # Log what we loaded
        logger.info(f"Loaded {len(self._state.active_time_messages)} active time message(s) from state")

        # Keep active messages - will be resumed by task manager

        # Load cache
        self._cache = await self._load_file(
            self.cache_file,
            lambda d: CacheData.from_dict(d)
        ) or CacheData()

        self._initialized = True
        logger.info(
            f"Storage initialized: {len(self._groups)} groups, "
            f"{len(self._users)} users"
        )

    async def _load_file(self, path: Path, parser) -> Optional[Any]:
        """Load and parse a JSON file."""
        if not path.exists():
            return None

        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None, lambda: json.loads(path.read_text(encoding="utf-8"))
            )
            return parser(data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in {path}: {e}")
            backup = path.with_suffix(".json.bak")
            if backup.exists():
                logger.info(f"Attempting recovery from {backup}")
                try:
                    data = json.loads(backup.read_text(encoding="utf-8"))
                    return parser(data)
                except Exception:
                    pass
            return None
        except Exception as e:
            logger.error(f"Error loading {path}: {e}")
            return None

    async def _save_file(self, path: Path, data: dict) -> bool:
        """Atomically save data to a JSON file."""
        try:
            temp_path = path.with_suffix(".json.tmp")
            backup_path = path.with_suffix(".json.bak")

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: temp_path.write_text(
                    json.dumps(data, indent=2, ensure_ascii=False),
                    encoding="utf-8"
                )
            )

            if path.exists():
                await loop.run_in_executor(
                    None, lambda: shutil.copy2(path, backup_path)
                )

            await loop.run_in_executor(
                None, lambda: temp_path.replace(path)
            )

            return True
        except Exception as e:
            logger.error(f"Error saving {path}: {e}")
            return False

    # ==================== GROUP OPERATIONS ====================

    async def get_group(self, chat_id: int) -> GroupData:
        """Get group data, creating if not exists."""
        key = str(chat_id)
        async with self._groups_lock:
            if key not in self._groups:
                self._groups[key] = GroupData()
            return self._groups[key]

    async def add_group_timezone(
        self,
        chat_id: int,
        tz_id: str,
        display_name: str,
        added_by: int
    ) -> bool:
        """Add a timezone to a group. Returns False if already exists."""
        key = str(chat_id)
        async with self._groups_lock:
            if key not in self._groups:
                self._groups[key] = GroupData()

            group = self._groups[key]

            for entry in group.timezones.values():
                if entry.tz == tz_id:
                    return False

            tz_key = tz_id.replace("/", "_").lower()

            group.timezones[tz_key] = TimezoneEntry(
                tz=tz_id,
                display_name=display_name,
                added_by=added_by,
                added_at=datetime.utcnow().isoformat() + "Z"
            )

            await self._save_groups()
            return True

    async def remove_group_timezone(self, chat_id: int, tz_query: str) -> Optional[str]:
        """Remove a timezone from a group. Returns removed name or None."""
        key = str(chat_id)
        async with self._groups_lock:
            if key not in self._groups:
                return None

            group = self._groups[key]
            query_lower = tz_query.lower()

            to_remove = None
            for tz_key, entry in group.timezones.items():
                if (
                    query_lower in entry.tz.lower() or
                    query_lower in entry.display_name.lower() or
                    query_lower == tz_key
                ):
                    to_remove = tz_key
                    break

            if to_remove:
                removed = group.timezones.pop(to_remove)
                await self._save_groups()
                return removed.display_name

            return None

    async def get_group_timezones(self, chat_id: int) -> Dict[str, TimezoneEntry]:
        """Get all timezones for a group."""
        group = await self.get_group(chat_id)
        return group.timezones.copy()

    async def set_group_config(self, chat_id: int, config: GroupConfig) -> None:
        """Update group configuration."""
        key = str(chat_id)
        async with self._groups_lock:
            if key not in self._groups:
                self._groups[key] = GroupData()
            self._groups[key].config = config
            await self._save_groups()

    async def get_group_config(self, chat_id: int) -> GroupConfig:
        """Get group configuration."""
        group = await self.get_group(chat_id)
        return group.config

    async def export_group_data(self, chat_id: int) -> dict:
        """Export group data as raw dict."""
        group = await self.get_group(chat_id)
        return group.to_dict()

    async def _save_groups(self) -> None:
        """Save groups to disk (call within lock)."""
        data = {k: v.to_dict() for k, v in self._groups.items()}
        await self._save_file(self.groups_file, data)

    # ==================== USER OPERATIONS ====================

    async def get_user_timezone(self, user_id: int) -> Optional[UserData]:
        """Get user's timezone setting."""
        key = str(user_id)
        async with self._users_lock:
            return self._users.get(key)

    async def set_user_timezone(
        self,
        user_id: int,
        tz_id: str,
        display_name: str
    ) -> None:
        """Set user's timezone."""
        key = str(user_id)
        async with self._users_lock:
            self._users[key] = UserData(
                timezone=tz_id,
                display_name=display_name,
                set_at=datetime.utcnow().isoformat() + "Z"
            )
            await self._save_users()

    async def _save_users(self) -> None:
        """Save users to disk (call within lock)."""
        data = {k: v.to_dict() for k, v in self._users.items()}
        await self._save_file(self.users_file, data)

    # ==================== STATE OPERATIONS ====================

    async def get_active_time_message(self, chat_id: int) -> Optional[ActiveTimeMessage]:
        """Get the active /time_live message for a chat."""
        key = str(chat_id)
        async with self._state_lock:
            return self._state.active_time_messages.get(key)

    async def get_all_active_time_messages(self) -> Dict[int, ActiveTimeMessage]:
        """Get all active /time_live messages for resuming on restart."""
        async with self._state_lock:
            return {
                int(k): v for k, v in self._state.active_time_messages.items()
            }

    async def set_active_time_message(self, chat_id: int, message_id: int) -> None:
        """Record a new active /time_live message."""
        key = str(chat_id)
        async with self._state_lock:
            self._state.active_time_messages[key] = ActiveTimeMessage(
                message_id=message_id,
                started_at=datetime.utcnow().isoformat() + "Z"
            )
            await self._save_state()

    async def clear_active_time_message(self, chat_id: int) -> None:
        """Clear the active /time_live message for a chat."""
        key = str(chat_id)
        async with self._state_lock:
            self._state.active_time_messages.pop(key, None)
            await self._save_state()

    # ==================== PER-USER COOLDOWN OPERATIONS ====================

    async def get_user_cooldown(
        self,
        chat_id: int,
        user_id: int
    ) -> Tuple[Optional[datetime], Optional[int]]:
        """
        Get cooldown info for a user in a chat.

        Returns (expiry_datetime, last_message_id) or (None, None) if no cooldown.
        """
        key = f"{chat_id}:{user_id}"
        async with self._state_lock:
            cooldown = self._state.user_cooldowns.get(key)
            if cooldown:
                try:
                    ts = cooldown.expires_at.rstrip("Z")
                    if ts.endswith("+00:00"):
                        ts = ts[:-6]
                    expiry = datetime.fromisoformat(ts)
                    return (expiry, cooldown.last_message_id)
                except Exception:
                    return (None, None)
            return (None, None)

    async def set_user_cooldown(
        self,
        chat_id: int,
        user_id: int,
        expires_at: datetime,
        message_id: Optional[int] = None
    ) -> None:
        """Set cooldown for a user in a chat."""
        key = f"{chat_id}:{user_id}"
        async with self._state_lock:
            self._state.user_cooldowns[key] = UserCooldown(
                expires_at=expires_at.isoformat() + "Z",
                last_message_id=message_id
            )
            await self._save_state()

    async def clear_user_cooldown(self, chat_id: int, user_id: int) -> None:
        """Clear cooldown for a user in a chat."""
        key = f"{chat_id}:{user_id}"
        async with self._state_lock:
            self._state.user_cooldowns.pop(key, None)
            await self._save_state()

    # ==================== OWNER MODE OPERATIONS ====================

    async def get_owner_only_mode(self) -> bool:
        """Get owner-only mode status."""
        async with self._state_lock:
            return self._state.owner_only_mode

    async def set_owner_only_mode(self, enabled: bool) -> None:
        """Set owner-only mode status."""
        async with self._state_lock:
            self._state.owner_only_mode = enabled
            await self._save_state()

    # ==================== SCHEDULED DELETE OPERATIONS ====================

    async def schedule_delete(
        self,
        chat_id: int,
        message_id: int,
        delete_at: datetime
    ) -> None:
        """Schedule a message for deletion."""
        key = f"{chat_id}:{message_id}"
        async with self._state_lock:
            self._state.scheduled_deletes[key] = ScheduledDelete(
                chat_id=chat_id,
                message_id=message_id,
                delete_at=delete_at.isoformat() + "Z"
            )
            await self._save_state()

    async def get_pending_deletes(self) -> list:
        """Get all messages due for deletion."""
        now = datetime.utcnow()
        pending = []
        async with self._state_lock:
            for key, item in list(self._state.scheduled_deletes.items()):
                try:
                    ts = item.delete_at.rstrip("Z")
                    if ts.endswith("+00:00"):
                        ts = ts[:-6]
                    delete_time = datetime.fromisoformat(ts)
                    if now >= delete_time:
                        pending.append((item.chat_id, item.message_id, key))
                except Exception:
                    pass
        return pending

    async def remove_scheduled_delete(self, key: str) -> None:
        """Remove a scheduled delete entry."""
        async with self._state_lock:
            self._state.scheduled_deletes.pop(key, None)
            await self._save_state()

    async def _save_state(self) -> None:
        """Save state to disk (call within lock)."""
        await self._save_file(self.state_file, self._state.to_dict())

    # ==================== CACHE OPERATIONS ====================

    async def get_cached_timezone(self, alias: str) -> Optional[str]:
        """Get cached timezone resolution."""
        async with self._cache_lock:
            return self._cache.alias_cache.get(alias.lower())

    async def cache_timezone(self, alias: str, tz_id: str) -> None:
        """Cache a timezone resolution."""
        async with self._cache_lock:
            self._cache.alias_cache[alias.lower()] = tz_id
            await self._save_cache()

    async def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        async with self._cache_lock:
            return {
                "alias_cache_size": len(self._cache.alias_cache),
                "last_cleanup": self._cache.last_cleanup
            }

    async def _save_cache(self) -> None:
        """Save cache to disk (call within lock)."""
        await self._save_file(self.cache_file, self._cache.to_dict())

    # ==================== HEALTH CHECK ====================

    async def check_integrity(self) -> dict:
        """Check JSON file integrity."""
        results = {}

        for name, path in [
            ("groups", self.groups_file),
            ("users", self.users_file),
            ("state", self.state_file),
            ("cache", self.cache_file)
        ]:
            if not path.exists():
                results[name] = {"status": "missing", "size": 0}
            else:
                try:
                    content = path.read_text(encoding="utf-8")
                    json.loads(content)
                    results[name] = {"status": "ok", "size": len(content)}
                except json.JSONDecodeError:
                    results[name] = {"status": "corrupted", "size": 0}
                except Exception as e:
                    results[name] = {"status": f"error: {e}", "size": 0}

        return results
