"""
HTTP Controllers

FastAPI routers for API, browse, and MCP protocol endpoints.
Also provides the FastAPI app factory and server runner.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.controllers.http.api import router as api_router
from src.controllers.http.browse import router as browse_router
from src.controllers.http.mcp_protocol import router as mcp_router

__all__ = ["api_router", "browse_router", "mcp_router", "get_app", "run_server", "get_startup_time"]

# Track server startup time
_startup_time = datetime.now(timezone.utc).isoformat()

# Lazy-initialized app
_app: Optional[FastAPI] = None


def get_startup_time() -> str:
    """Get the server startup time."""
    return _startup_time


def _create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Cortex Server",
        description="HTTP endpoints for Cortex memory browser and API",
        version="2.0.0",
    )

    # Include routers
    app.include_router(browse_router, prefix="/browse", tags=["browse"])
    app.include_router(api_router, tags=["api"])
    app.include_router(mcp_router, prefix="/mcp", tags=["mcp"])

    @app.get("/health")
    def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}

    # Serve static web UI files
    static_dir = Path(__file__).parent.parent.parent.parent / "static"

    if static_dir.exists():
        # Serve static assets (JS, CSS, images)
        assets_dir = static_dir / "assets"
        if assets_dir.exists():
            app.mount("/ui/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/ui")
        @app.get("/ui/{full_path:path}")
        async def serve_spa(full_path: str = "") -> FileResponse:
            """Serve the SPA for all /ui/* routes."""
            return FileResponse(static_dir / "index.html")

    return app


def get_app() -> FastAPI:
    """Get the FastAPI application (creates it on first call)."""
    global _app
    if _app is None:
        _app = _create_app()
    return _app


# For backward compatibility, expose app at module level
# This uses a property-like pattern via __getattr__
def __getattr__(name: str):
    if name == "app":
        return get_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def run_server(host: str = "0.0.0.0", port: int = 8080):
    """Run the FastAPI server."""
    import uvicorn
    from src.configs import get_logger
    logger = get_logger("http")
    logger.info(f"Starting HTTP server on {host}:{port}")
    uvicorn.run(get_app(), host=host, port=port, log_level="warning")
