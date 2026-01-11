"""
Cortex MCP Tools

All MCP tool implementations organized by function.
"""

from src.tools.admin import configure_cortex, get_cortex_version, get_skeleton, toggle_cortex
from src.tools.context import (
    get_context_from_cortex,
    set_initiative,
    set_repo_context,
    update_initiative_status,
)
from src.tools.ingest import ingest_code_into_cortex
from src.tools.notes import commit_to_cortex, save_note_to_cortex
from src.tools.search import search_cortex

__all__ = [
    # Search
    "search_cortex",
    # Ingest
    "ingest_code_into_cortex",
    # Notes
    "save_note_to_cortex",
    "commit_to_cortex",
    # Context
    "set_repo_context",
    "set_initiative",
    "update_initiative_status",
    "get_context_from_cortex",
    # Admin
    "configure_cortex",
    "toggle_cortex",
    "get_cortex_version",
    "get_skeleton",
]
