"""
Cortex Browser Widgets.
"""

from src.browser.terminal.widgets.detail_panel import DetailPanel
from src.browser.terminal.widgets.list_browser import (
    DocumentListItem,
    DocumentSelected,
    ListBrowser,
)
from src.browser.terminal.widgets.search_panel import (
    SearchPanel,
    SearchRequested,
    SearchResultItem,
    SearchResultSelected,
)
from src.browser.terminal.widgets.stats_panel import StatsPanel

__all__ = [
    "StatsPanel",
    "ListBrowser",
    "DocumentListItem",
    "DocumentSelected",
    "SearchPanel",
    "SearchRequested",
    "SearchResultItem",
    "SearchResultSelected",
    "DetailPanel",
]
