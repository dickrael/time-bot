"""
JSON Schema definitions for Time Bot storage.

These dataclasses define the structure of all persisted data.
JSON files are crash-safe through atomic writes.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class TimezoneEntry:
    """Single timezone entry in a group."""
    tz: str  # IANA timezone ID
    display_name: str  # Human-readable name
    added_by: int  # User ID who added it
    added_at: str  # ISO timestamp

    def to_dict(self) -> dict:
        return {
            "tz": self.tz,
            "display_name": self.display_name,
            "added_by": self.added_by,
            "added_at": self.added_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TimezoneEntry":
        return cls(
            tz=data["tz"],
            display_name=data["display_name"],
            added_by=data["added_by"],
            added_at=data["added_at"]
        )


@dataclass
class GroupConfig:
    """Configuration for a group."""
    cooldown_seconds: int = 30
    show_utc_offset: bool = False  # Default: hide UTC offset

    def to_dict(self) -> dict:
        return {
            "cooldown_seconds": self.cooldown_seconds,
            "show_utc_offset": self.show_utc_offset
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GroupConfig":
        return cls(
            cooldown_seconds=data.get("cooldown_seconds", 30),
            show_utc_offset=data.get("show_utc_offset", False)
        )


@dataclass
class GroupData:
    """Complete data for a single group."""
    timezones: Dict[str, TimezoneEntry] = field(default_factory=dict)
    config: GroupConfig = field(default_factory=GroupConfig)

    def to_dict(self) -> dict:
        return {
            "timezones": {k: v.to_dict() for k, v in self.timezones.items()},
            "config": self.config.to_dict()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GroupData":
        timezones = {}
        for k, v in data.get("timezones", {}).items():
            timezones[k] = TimezoneEntry.from_dict(v)
        config = GroupConfig.from_dict(data.get("config", {}))
        return cls(timezones=timezones, config=config)


@dataclass
class UserData:
    """Timezone preference for a single user."""
    timezone: str  # IANA timezone ID
    display_name: str  # Human-readable name
    set_at: str  # ISO timestamp

    def to_dict(self) -> dict:
        return {
            "timezone": self.timezone,
            "display_name": self.display_name,
            "set_at": self.set_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserData":
        return cls(
            timezone=data["timezone"],
            display_name=data["display_name"],
            set_at=data["set_at"]
        )


@dataclass
class ActiveTimeMessage:
    """Tracks an active /time_live message being edited."""
    message_id: int
    started_at: str  # ISO timestamp

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "started_at": self.started_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ActiveTimeMessage":
        return cls(
            message_id=data["message_id"],
            started_at=data["started_at"]
        )


@dataclass
class UserCooldown:
    """Tracks cooldown for a user in a specific chat."""
    expires_at: str  # ISO timestamp
    last_message_id: Optional[int] = None  # For cleanup

    def to_dict(self) -> dict:
        return {
            "expires_at": self.expires_at,
            "last_message_id": self.last_message_id
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserCooldown":
        return cls(
            expires_at=data["expires_at"],
            last_message_id=data.get("last_message_id")
        )


@dataclass
class ScheduledDelete:
    """Tracks a message scheduled for deletion."""
    chat_id: int
    message_id: int
    delete_at: str  # ISO timestamp

    def to_dict(self) -> dict:
        return {
            "chat_id": self.chat_id,
            "message_id": self.message_id,
            "delete_at": self.delete_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduledDelete":
        return cls(
            chat_id=data["chat_id"],
            message_id=data["message_id"],
            delete_at=data["delete_at"]
        )


@dataclass
class StateData:
    """Runtime state data."""
    active_time_messages: Dict[str, ActiveTimeMessage] = field(default_factory=dict)
    # Per-user cooldowns: "chat_id:user_id" -> UserCooldown
    user_cooldowns: Dict[str, UserCooldown] = field(default_factory=dict)
    # Owner-only mode - when True, only basic commands work for non-owners
    owner_only_mode: bool = False
    # Messages scheduled for auto-deletion
    scheduled_deletes: Dict[str, ScheduledDelete] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "active_time_messages": {k: v.to_dict() for k, v in self.active_time_messages.items()},
            "user_cooldowns": {k: v.to_dict() for k, v in self.user_cooldowns.items()},
            "owner_only_mode": self.owner_only_mode,
            "scheduled_deletes": {k: v.to_dict() for k, v in self.scheduled_deletes.items()}
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StateData":
        active = {}
        for k, v in data.get("active_time_messages", {}).items():
            active[k] = ActiveTimeMessage.from_dict(v)

        cooldowns = {}
        for k, v in data.get("user_cooldowns", {}).items():
            cooldowns[k] = UserCooldown.from_dict(v)

        scheduled = {}
        for k, v in data.get("scheduled_deletes", {}).items():
            scheduled[k] = ScheduledDelete.from_dict(v)

        return cls(
            active_time_messages=active,
            user_cooldowns=cooldowns,
            owner_only_mode=data.get("owner_only_mode", False),
            scheduled_deletes=scheduled
        )


@dataclass
class CacheData:
    """Cached data for performance."""
    alias_cache: Dict[str, str] = field(default_factory=dict)
    last_cleanup: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "alias_cache": self.alias_cache,
            "last_cleanup": self.last_cleanup
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CacheData":
        return cls(
            alias_cache=data.get("alias_cache", {}),
            last_cleanup=data.get("last_cleanup")
        )
