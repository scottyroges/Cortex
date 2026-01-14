"""
Search Panel Widget

Interactive search with live results and score display.
"""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.timer import Timer
from textual.widget import Widget
from textual.widgets import Input, Label, ListItem, ListView, Static

from src.browser.formatting import format_content, truncate
from src.browser.models import SearchResponse, SearchResult


class SearchResultSelected(Message):
    """Message sent when a search result is selected."""

    def __init__(self, doc_id: str) -> None:
        self.doc_id = doc_id
        super().__init__()


class SearchResultItem(ListItem):
    """A single search result in the list."""

    def __init__(self, result: SearchResult) -> None:
        super().__init__()
        self.result = result

    def compose(self) -> ComposeResult:
        """Create the result item content."""
        # Type indicator with color
        type_colors = {
            "note": "cyan",
            "insight": "yellow",
            "commit": "green",
            "initiative": "magenta",
            "code": "blue",
        }
        color = type_colors.get(self.result.doc_type, "white")
        type_label = f"[{color}]{self.result.doc_type[:4]}[/{color}]"

        # Title or ID
        title = self.result.title or self.result.id
        title = truncate(title, 35)

        # Score
        score = self.result.best_score
        score_str = f"[dim]{score:.2f}[/dim]" if score else ""

        # Preview (cleaned up)
        preview = format_content(self.result.content_preview)
        preview = truncate(preview.replace("\n", " "), 60)

        yield Static(f"{type_label} {title} {score_str}")
        yield Static(f"[dim]{preview}[/dim]")


class SearchPanel(Widget):
    """
    Interactive search panel.

    Features:
    - Search input with debouncing
    - Live results with scores
    - Keyboard navigation
    """

    DEFAULT_CSS = """
    SearchPanel {
        width: 100%;
        height: auto;
        min-height: 8;
        border: solid $primary;
        padding: 0 1;
    }

    SearchPanel .search-title {
        text-style: bold;
        padding: 1 0 0 0;
    }

    SearchPanel Input {
        margin: 1 0;
    }

    SearchPanel .search-status {
        color: $text-muted;
        height: 1;
    }

    SearchPanel ListView {
        height: auto;
        max-height: 20;
    }

    SearchPanel .search-result-item {
        padding: 0;
    }

    SearchPanel .search-empty {
        padding: 1;
        color: $text-muted;
        text-style: italic;
    }
    """

    query: reactive[str] = reactive("")
    results: reactive[SearchResponse | None] = reactive(None)
    searching: reactive[bool] = reactive(False)

    # Debounce timer
    _debounce_timer: Timer | None = None
    DEBOUNCE_MS = 300

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Vertical():
            yield Label("Search", classes="search-title")
            yield Input(placeholder="Type to search...", id="search-input")
            yield Static("", id="search-status", classes="search-status")
            yield ListView(id="search-results")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes with debouncing."""
        if event.input.id == "search-input":
            self.query = event.value

            # Cancel existing timer
            if self._debounce_timer:
                self._debounce_timer.stop()

            # Start new debounce timer
            if self.query.strip():
                self._debounce_timer = self.set_timer(
                    self.DEBOUNCE_MS / 1000,
                    self._trigger_search,
                )
            else:
                # Clear results immediately when input is empty
                self._clear_results()

    def _trigger_search(self) -> None:
        """Trigger the search after debounce."""
        if self.query.strip():
            self.post_message(SearchRequested(self.query))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle result selection."""
        if isinstance(event.item, SearchResultItem):
            self.post_message(SearchResultSelected(event.item.result.id))

    def watch_results(self, response: SearchResponse | None) -> None:
        """React to search results changes."""
        if response is not None:
            self._render_results(response)

    def watch_searching(self, searching: bool) -> None:
        """React to searching state changes."""
        status = self.query_one("#search-status", Static)
        if searching:
            status.update("Searching...")
        else:
            status.update("")

    def _render_results(self, response: SearchResponse) -> None:
        """Render search results."""
        list_view = self.query_one("#search-results", ListView)
        list_view.clear()

        status = self.query_one("#search-status", Static)
        status.update(f"{response.result_count} results in {response.timing_ms:.0f}ms")

        if not response.results:
            list_view.mount(Static("No results found", classes="search-empty"))
        else:
            for result in response.results:
                list_view.mount(SearchResultItem(result))

    def _clear_results(self) -> None:
        """Clear search results."""
        list_view = self.query_one("#search-results", ListView)
        list_view.clear()
        status = self.query_one("#search-status", Static)
        status.update("")

    def set_results(self, response: SearchResponse) -> None:
        """Update with search results."""
        self.searching = False
        self.results = response

    def set_searching(self) -> None:
        """Set searching state."""
        self.searching = True

    def set_error(self, message: str) -> None:
        """Set error state."""
        self.searching = False
        list_view = self.query_one("#search-results", ListView)
        list_view.clear()
        list_view.mount(Static(f"[red]Error: {message}[/red]", classes="search-empty"))
        status = self.query_one("#search-status", Static)
        status.update("")

    def focus_input(self) -> None:
        """Focus the search input."""
        self.query_one("#search-input", Input).focus()


class SearchRequested(Message):
    """Message sent when a search should be performed."""

    def __init__(self, query: str) -> None:
        self.query = query
        super().__init__()
