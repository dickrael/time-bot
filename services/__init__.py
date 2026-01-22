"""Services module for Time Bot business logic."""

import sys
from pathlib import Path

# Handle imports for both direct execution and module execution
try:
    from .timezone_service import TimezoneService
    from .task_manager import TaskManager
    from .permission_service import PermissionService
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from timezone_service import TimezoneService
    from task_manager import TaskManager
    from permission_service import PermissionService

__all__ = ["TimezoneService", "TaskManager", "PermissionService"]
