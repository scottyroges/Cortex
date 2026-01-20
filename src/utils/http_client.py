"""
Standardized HTTP Client Utilities

Provides a consistent interface for making HTTP requests across Cortex.
Uses `requests` for synchronous calls with standardized error handling.

Usage:
    from src.utils.http_client import http_get, http_post
    from src.exceptions import HTTPRequestError

    # Simple GET
    response = http_get("https://api.example.com/data", timeout=5)

    # POST with JSON
    response = http_post(
        "https://api.example.com/generate",
        json={"prompt": "hello"},
        timeout=30
    )
"""

from typing import Any

import requests

from src.configs.constants import get_timeout
from src.exceptions import HTTPConnectionError, HTTPRequestError, HTTPTimeoutError

# Default timeout for HTTP requests (seconds)
DEFAULT_TIMEOUT = get_timeout("http_default", 10)

# Re-export for backwards compatibility
HTTPError = HTTPRequestError


def _handle_request_error(e: Exception, url: str) -> None:
    """
    Convert requests exceptions to Cortex HTTP exceptions.

    Args:
        e: The requests exception
        url: The request URL (for error messages)

    Raises:
        HTTPConnectionError: Connection failed
        HTTPTimeoutError: Request timed out
        HTTPRequestError: Bad status code
    """
    if isinstance(e, requests.exceptions.ConnectionError):
        raise HTTPConnectionError(f"Connection failed: {url}") from e
    elif isinstance(e, requests.exceptions.Timeout):
        raise HTTPTimeoutError(f"Request timed out: {url}") from e
    elif isinstance(e, requests.exceptions.HTTPError):
        raise HTTPRequestError(
            f"HTTP {e.response.status_code}: {url}",
            status_code=e.response.status_code,
            response_text=e.response.text[:500] if e.response.text else None,
        ) from e
    else:
        raise


def http_get(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    raise_for_status: bool = True,
) -> requests.Response:
    """
    Make a GET request with standardized error handling.

    Args:
        url: Request URL
        headers: Optional headers dict
        timeout: Request timeout in seconds
        raise_for_status: Raise HTTPRequestError on 4xx/5xx responses

    Returns:
        requests.Response object

    Raises:
        HTTPConnectionError: Connection failed
        HTTPTimeoutError: Request timed out
        HTTPRequestError: Bad status code (if raise_for_status=True)
    """
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        if raise_for_status:
            response.raise_for_status()
        return response
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.HTTPError,
    ) as e:
        _handle_request_error(e, url)
        raise  # Unreachable, but satisfies type checker


def http_post(
    url: str,
    json: dict[str, Any] | None = None,
    data: bytes | str | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    raise_for_status: bool = True,
) -> requests.Response:
    """
    Make a POST request with standardized error handling.

    Args:
        url: Request URL
        json: JSON body (will set Content-Type automatically)
        data: Raw body data
        headers: Optional headers dict
        timeout: Request timeout in seconds
        raise_for_status: Raise HTTPRequestError on 4xx/5xx responses

    Returns:
        requests.Response object

    Raises:
        HTTPConnectionError: Connection failed
        HTTPTimeoutError: Request timed out
        HTTPRequestError: Bad status code (if raise_for_status=True)
    """
    try:
        response = requests.post(url, json=json, data=data, headers=headers, timeout=timeout)
        if raise_for_status:
            response.raise_for_status()
        return response
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.HTTPError,
    ) as e:
        _handle_request_error(e, url)
        raise  # Unreachable, but satisfies type checker


def http_json_get(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """
    GET request that returns parsed JSON.

    Args:
        url: Request URL
        headers: Optional headers dict
        timeout: Request timeout in seconds

    Returns:
        Parsed JSON as dict

    Raises:
        HTTPConnectionError: Connection failed
        HTTPTimeoutError: Request timed out
        HTTPRequestError: Bad status code or invalid JSON
    """
    response = http_get(url, headers=headers, timeout=timeout)
    try:
        return response.json()
    except ValueError as e:
        raise HTTPRequestError(f"Invalid JSON response from {url}") from e


def http_json_post(
    url: str,
    json: dict[str, Any],
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """
    POST request with JSON body that returns parsed JSON.

    Args:
        url: Request URL
        json: JSON body to send
        headers: Optional headers dict
        timeout: Request timeout in seconds

    Returns:
        Parsed JSON as dict

    Raises:
        HTTPConnectionError: Connection failed
        HTTPTimeoutError: Request timed out
        HTTPRequestError: Bad status code or invalid JSON
    """
    response = http_post(url, json=json, headers=headers, timeout=timeout)
    try:
        return response.json()
    except ValueError as e:
        raise HTTPRequestError(f"Invalid JSON response from {url}") from e
