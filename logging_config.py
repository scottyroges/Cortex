"""
Cortex Logging Configuration

Configures logging based on environment variables:
- CORTEX_DEBUG: Enable debug logging (default: false)
- CORTEX_LOG_FILE: Log file path (default: stderr only)
"""

import logging
import os
import sys
from typing import Optional


def setup_logging(
    debug: Optional[bool] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Configure logging for Cortex.

    Args:
        debug: Enable debug level. Defaults to CORTEX_DEBUG env var.
        log_file: Log file path. Defaults to CORTEX_LOG_FILE env var.

    Returns:
        Root logger for cortex
    """
    # Read from env if not provided
    if debug is None:
        debug = os.environ.get("CORTEX_DEBUG", "").lower() in ("true", "1", "yes")
    if log_file is None:
        log_file = os.environ.get("CORTEX_LOG_FILE")

    # Set log level
    level = logging.DEBUG if debug else logging.INFO

    # Create formatter with component tags
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Get root cortex logger
    logger = logging.getLogger("cortex")
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Always add stderr handler (but only for warnings+ unless debug)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    if log_file:
        # If logging to file, only show warnings on stderr
        stderr_handler.setLevel(logging.WARNING)
    else:
        stderr_handler.setLevel(level)
    logger.addHandler(stderr_handler)

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")

    return logger


def get_logger(component: str) -> logging.Logger:
    """
    Get a logger for a specific component.

    Args:
        component: Component name (e.g., "search", "ingest", "server")

    Returns:
        Logger instance for the component
    """
    return logging.getLogger(f"cortex.{component}")
