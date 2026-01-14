"""
Cortex Memory Browser - Terminal UI

A Textual-based TUI for exploring Cortex memory.
"""

from src.browser.terminal.app import CortexBrowserApp


def run_browser(base_url: str = "http://localhost:8080") -> None:
    """
    Run the Cortex memory browser TUI.

    Args:
        base_url: URL of the Cortex daemon HTTP server
    """
    app = CortexBrowserApp(base_url=base_url)
    app.run()


__all__ = ["run_browser", "CortexBrowserApp"]
