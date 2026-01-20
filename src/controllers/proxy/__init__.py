"""
Host-side proxy server.

Runs on the host (not in Docker) to provide access to host-only
resources like the claude CLI from inside the Docker daemon.
"""

from src.controllers.proxy.server import run_server, main

__all__ = ["run_server", "main"]
