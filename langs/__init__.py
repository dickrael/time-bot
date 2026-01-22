"""Language module for Time Bot."""

from .en import STRINGS

def get_string(key: str, **kwargs) -> str:
    """Get a localized string by key, with optional formatting."""
    text = STRINGS.get(key, f"[Missing: {key}]")
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text

__all__ = ["get_string", "STRINGS"]
