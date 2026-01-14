"""
Main Textual Application for the Cortex Memory Browser.
"""

from pathlib import Path

from textual.app import App
from textual.binding import Binding

from src.browser.client import CortexClient
from src.browser.terminal.screens.main import MainScreen

# Path to the stylesheet
STYLES_PATH = Path(__file__).parent / "styles.tcss"


class CortexBrowserApp(App):
    """
    Cortex Memory Browser - Terminal UI.

    A Textual-based interface for exploring notes, insights,
    commits, and initiatives stored in Cortex memory.
    """

    TITLE = "Cortex Memory Browser"
    CSS_PATH = STYLES_PATH if STYLES_PATH.exists() else None

    CSS = """
    Screen {
        background: $surface;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True, priority=True),
        Binding("?", "show_help", "Help", show=True),
    ]

    def __init__(self, base_url: str = "http://localhost:8080"):
        super().__init__()
        self.client = CortexClient(base_url=base_url)

    async def on_mount(self) -> None:
        """Called when app is mounted."""
        # Check connection and push main screen
        connected = await self.client.health_check()
        if connected:
            self.sub_title = "Connected"
        else:
            self.sub_title = "Disconnected"

        # Push the main screen
        await self.push_screen(MainScreen(self.client))

    def action_show_help(self) -> None:
        """Show help notification."""
        self.notify(
            "q: Quit | r: Refresh | /: Search | Esc: Clear\n"
            "j/k or arrows: Navigate | Enter: Select",
            title="Keyboard Shortcuts",
            timeout=5,
        )


if __name__ == "__main__":
    app = CortexBrowserApp()
    app.run()
