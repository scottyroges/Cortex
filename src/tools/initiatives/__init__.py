"""
Initiative Management Tools

MCP tools for managing multi-session initiatives.
"""

from src.tools.initiatives.initiatives import (
    STALE_THRESHOLD_DAYS,
    check_initiative_staleness,
    complete_initiative,
    create_initiative,
    detect_completion_signals,
    focus_initiative,
    get_focused_initiative,
    list_initiatives,
    manage_initiative,
    summarize_initiative,
)
from src.tools.initiatives.initiative_utils import (
    calculate_duration,
    calculate_duration_from_now,
    find_initiative,
    resolve_initiative,
)

__all__ = [
    # Constants
    "STALE_THRESHOLD_DAYS",
    # Main tool
    "manage_initiative",
    # Individual tools
    "create_initiative",
    "list_initiatives",
    "focus_initiative",
    "complete_initiative",
    "summarize_initiative",
    # Utility functions
    "get_focused_initiative",
    "detect_completion_signals",
    "check_initiative_staleness",
    "find_initiative",
    "resolve_initiative",
    "calculate_duration",
    "calculate_duration_from_now",
]
