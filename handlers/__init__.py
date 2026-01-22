"""Command handlers for Time Bot."""

import sys
from pathlib import Path

# Add paths for fallback imports
_handlers_dir = Path(__file__).parent
_parent_dir = _handlers_dir.parent
if str(_handlers_dir) not in sys.path:
    sys.path.insert(0, str(_handlers_dir))
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

# Handle imports for both direct execution and module execution
try:
    from .time_cmd import register_time_handler
    from .timehere_cmd import register_timehere_handler
    from .when_cmd import register_when_handler
    from .admin_cmds import register_admin_handlers
    from .user_cmds import register_user_handlers
    from .start_help import register_start_help_handlers
    from .owner_cmds import register_owner_handlers
except ImportError:
    from time_cmd import register_time_handler
    from timehere_cmd import register_timehere_handler
    from when_cmd import register_when_handler
    from admin_cmds import register_admin_handlers
    from user_cmds import register_user_handlers
    from start_help import register_start_help_handlers
    from owner_cmds import register_owner_handlers

__all__ = [
    "register_time_handler",
    "register_timehere_handler",
    "register_when_handler",
    "register_admin_handlers",
    "register_user_handlers",
    "register_start_help_handlers",
    "register_owner_handlers",
    "register_all_handlers",
]


def register_all_handlers(app, services):
    """Register all command handlers with the bot."""
    register_start_help_handlers(app, services)
    register_time_handler(app, services)
    register_timehere_handler(app, services)
    register_when_handler(app, services)
    register_admin_handlers(app, services)
    register_user_handlers(app, services)
    register_owner_handlers(app, services)
