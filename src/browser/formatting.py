"""
Human-readable content formatting for the Cortex browser.

Converts stored data to clean, readable output:
- Proper newlines (no escaped \\n)
- Parsed JSON arrays for tags/files
- Relative timestamps
- Type-specific metadata formatting
"""

import json
import re
from datetime import datetime
from typing import Any, Optional


def format_content(text: str) -> str:
    """
    Convert stored content to human-readable form.

    - Converts literal \\n to actual newlines
    - Converts \\t to spaces
    - Strips excessive whitespace
    - Preserves intentional markdown formatting
    """
    if not text:
        return ""

    # Replace escaped newlines with actual newlines
    result = text.replace("\\n", "\n")

    # Replace escaped tabs with spaces
    result = result.replace("\\t", "    ")

    # Replace other common escapes
    result = result.replace("\\r", "")
    result = result.replace("\\\\", "\\")

    # Collapse multiple blank lines into at most two
    result = re.sub(r"\n{3,}", "\n\n", result)

    # Strip leading/trailing whitespace but preserve internal structure
    result = result.strip()

    return result


def format_tags(tags: Optional[str]) -> str:
    """
    Convert JSON array string or comma-separated tags to readable list.

    '["auth", "security"]' -> "auth, security"
    'auth,security' -> "auth, security"
    """
    if not tags:
        return ""

    # Try to parse as JSON first
    try:
        parsed = json.loads(tags)
        if isinstance(parsed, list):
            return ", ".join(str(t) for t in parsed)
    except (json.JSONDecodeError, TypeError):
        pass

    # Fall back to comma-separated
    return ", ".join(t.strip() for t in tags.split(",") if t.strip())


def format_files(files: Optional[str]) -> list[str]:
    """
    Convert JSON array string to list of file paths.

    '["src/auth.py", "src/user.py"]' -> ["src/auth.py", "src/user.py"]
    """
    if not files:
        return []

    try:
        parsed = json.loads(files)
        if isinstance(parsed, list):
            return [str(f) for f in parsed]
    except (json.JSONDecodeError, TypeError):
        pass

    return []


def format_timestamp(iso_str: Optional[str], relative: bool = True) -> str:
    """
    Convert ISO8601 timestamp to human-readable format.

    Args:
        iso_str: ISO8601 timestamp string
        relative: If True, return relative time ("2 hours ago")
                  If False, return formatted date ("Jan 10, 2024 2:30 PM")
    """
    if not iso_str:
        return ""

    try:
        # Parse ISO format (handle with/without timezone)
        if iso_str.endswith("Z"):
            iso_str = iso_str[:-1] + "+00:00"

        # Try parsing with timezone
        try:
            dt = datetime.fromisoformat(iso_str)
        except ValueError:
            # Try without timezone
            dt = datetime.fromisoformat(iso_str.split("+")[0].split("Z")[0])

        if not relative:
            return dt.strftime("%b %d, %Y %I:%M %p")

        # Calculate relative time
        now = datetime.utcnow()
        if dt.tzinfo:
            dt = dt.replace(tzinfo=None)

        diff = now - dt
        seconds = diff.total_seconds()

        if seconds < 0:
            return "just now"
        elif seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}m ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours}h ago"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days}d ago"
        elif seconds < 2592000:
            weeks = int(seconds / 604800)
            return f"{weeks}w ago"
        else:
            return dt.strftime("%b %d, %Y")

    except (ValueError, TypeError):
        return iso_str or ""


def format_metadata(meta: dict[str, Any], doc_type: str) -> dict[str, str]:
    """
    Format all metadata fields for display based on document type.

    Returns a dict of field_name -> formatted_value for display.
    """
    formatted = {}

    # Common fields
    if meta.get("repository"):
        formatted["Repository"] = meta["repository"]

    if meta.get("title"):
        formatted["Title"] = meta["title"]

    if meta.get("created_at"):
        formatted["Created"] = format_timestamp(meta["created_at"])

    if meta.get("status"):
        formatted["Status"] = meta["status"]

    # Type-specific fields
    if doc_type == "note":
        if meta.get("tags"):
            formatted["Tags"] = format_tags(meta["tags"])
        if meta.get("initiative_name"):
            formatted["Initiative"] = meta["initiative_name"]

    elif doc_type == "insight":
        if meta.get("files"):
            files = format_files(meta["files"])
            if files:
                formatted["Files"] = ", ".join(files)
        if meta.get("tags"):
            formatted["Tags"] = format_tags(meta["tags"])
        if meta.get("last_validation_result"):
            formatted["Validation"] = meta["last_validation_result"]
        if meta.get("verified_at"):
            formatted["Verified"] = format_timestamp(meta["verified_at"])
        if meta.get("initiative_name"):
            formatted["Initiative"] = meta["initiative_name"]

    elif doc_type == "commit":
        if meta.get("files"):
            files = format_files(meta["files"])
            if files:
                formatted["Files Changed"] = f"{len(files)} files"
        if meta.get("initiative_name"):
            formatted["Initiative"] = meta["initiative_name"]

    elif doc_type == "initiative":
        if meta.get("goal"):
            formatted["Goal"] = format_content(meta["goal"])
        if meta.get("completed_at"):
            formatted["Completed"] = format_timestamp(meta["completed_at"])

    elif doc_type == "code":
        if meta.get("file_path"):
            formatted["File"] = meta["file_path"]
        if meta.get("language"):
            formatted["Language"] = meta["language"]
        if meta.get("function_name"):
            formatted["Function"] = meta["function_name"]
        if meta.get("class_name"):
            formatted["Class"] = meta["class_name"]

    return formatted


def truncate(text: str, max_length: int = 80, suffix: str = "...") -> str:
    """Truncate text to max_length, adding suffix if truncated."""
    if not text or len(text) <= max_length:
        return text or ""
    return text[: max_length - len(suffix)] + suffix
