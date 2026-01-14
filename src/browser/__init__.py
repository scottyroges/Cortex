"""
Cortex Memory Browser

Shared components for browsing Cortex memory.
Terminal (TUI) and Web implementations share this module.
"""

from src.browser.client import CortexClient
from src.browser.models import Document, DocumentSummary, SearchResult, Stats
from src.browser.formatting import (
    format_content,
    format_files,
    format_metadata,
    format_tags,
    format_timestamp,
)

__all__ = [
    "CortexClient",
    "Stats",
    "Document",
    "DocumentSummary",
    "SearchResult",
    "format_content",
    "format_tags",
    "format_files",
    "format_timestamp",
    "format_metadata",
]
