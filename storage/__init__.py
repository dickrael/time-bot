"""Storage module for JSON-based persistence."""

import sys
from pathlib import Path

# Handle imports for both direct execution and module execution
try:
    from .json_store import JsonStore
    from .schemas import GroupData, UserData, StateData, CacheData
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from json_store import JsonStore
    from schemas import GroupData, UserData, StateData, CacheData

__all__ = ["JsonStore", "GroupData", "UserData", "StateData", "CacheData"]
