"""
Transcript Parsing

Parse Claude Code session transcripts from JSONL format.
Extracts messages, tool calls, and metadata for analysis.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

from logging_config import get_logger

logger = get_logger("autocapture.transcript")


@dataclass
class ToolCall:
    """Represents a single tool call in the session."""

    name: str
    input: dict[str, Any]
    output: Optional[str] = None
    success: bool = True
    timestamp: Optional[datetime] = None

    @property
    def is_file_edit(self) -> bool:
        """Check if this tool call modified a file."""
        return self.name in ("Write", "Edit", "NotebookEdit")

    @property
    def edited_file(self) -> Optional[str]:
        """Get the file path if this was a file edit, None otherwise."""
        if not self.is_file_edit:
            return None
        # Both Write and Edit use file_path parameter
        return self.input.get("file_path") or self.input.get("notebook_path")


@dataclass
class Message:
    """Represents a message in the session transcript."""

    role: str  # "user", "assistant", "system"
    content: str
    timestamp: Optional[datetime] = None
    tool_calls: list[ToolCall] = field(default_factory=list)

    @property
    def approximate_tokens(self) -> int:
        """Rough token count estimate (chars / 4)."""
        return len(self.content) // 4


@dataclass
class ParsedTranscript:
    """Parsed session transcript with extracted data."""

    session_id: str
    project_path: Optional[str]
    messages: list[Message]
    tool_calls: list[ToolCall]
    start_time: Optional[datetime]
    end_time: Optional[datetime]

    @property
    def token_count(self) -> int:
        """Approximate total token count."""
        return sum(m.approximate_tokens for m in self.messages)

    @property
    def files_edited(self) -> list[str]:
        """List of unique file paths that were edited."""
        files = set()
        for tc in self.tool_calls:
            if tc.edited_file:
                files.add(tc.edited_file)
        return sorted(files)

    @property
    def duration_seconds(self) -> int:
        """Session duration in seconds, or 0 if unknown."""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds())
        return 0

    @property
    def tool_call_count(self) -> int:
        """Total number of tool calls."""
        return len(self.tool_calls)

    def to_text(self, max_chars: Optional[int] = None) -> str:
        """
        Convert transcript to plain text for summarization.

        Args:
            max_chars: Maximum characters to include (None for unlimited)

        Returns:
            Plain text representation of the transcript
        """
        lines = []

        for msg in self.messages:
            role = msg.role.upper()
            lines.append(f"[{role}]")
            lines.append(msg.content)

            # Include tool calls inline
            for tc in msg.tool_calls:
                lines.append(f"\n[TOOL: {tc.name}]")
                if tc.output:
                    # Truncate long outputs
                    output = tc.output[:500] if len(tc.output) > 500 else tc.output
                    lines.append(f"Output: {output}")
            lines.append("")

        text = "\n".join(lines)

        if max_chars and len(text) > max_chars:
            text = text[:max_chars] + "\n\n[... transcript truncated ...]"

        return text


# =============================================================================
# Content Block Parsing
# =============================================================================


@dataclass
class ContentBlockResult:
    """Result of parsing content blocks."""

    text_parts: list[str] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)


class ContentBlockParser:
    """Parses different types of content blocks from Claude Code transcripts."""

    def __init__(self, timestamp: Optional[datetime] = None):
        self.timestamp = timestamp

    def parse_text_block(self, block: dict) -> Optional[str]:
        """Extract text from a text block."""
        text = block.get("text", "")
        return text if text else None

    def parse_tool_use_block(self, block: dict) -> ToolCall:
        """Parse a tool_use block into a ToolCall."""
        return ToolCall(
            name=block.get("name", "unknown"),
            input=block.get("input", {}),
            timestamp=self.timestamp,
        )

    def parse_tool_result_block(self, block: dict) -> Optional[str]:
        """Extract content from a tool_result block."""
        result_content = block.get("content", "")
        if isinstance(result_content, list):
            # Content can be array of text blocks
            return " ".join(
                b.get("text", "") for b in result_content if b.get("type") == "text"
            )
        return result_content if result_content else None

    def parse_content_array(self, content: list) -> ContentBlockResult:
        """Parse an array of content blocks."""
        result = ContentBlockResult()

        for block in content:
            block_type = block.get("type", "")

            if block_type == "text":
                text = self.parse_text_block(block)
                if text:
                    result.text_parts.append(text)

            elif block_type == "tool_use":
                tc = self.parse_tool_use_block(block)
                result.tool_calls.append(tc)

            elif block_type == "tool_result":
                # Tool result - could track for matching with tool calls
                # Currently we just parse but don't match
                pass

        return result


# =============================================================================
# Metadata Extraction
# =============================================================================


class TranscriptMetadataExtractor:
    """Extracts session metadata from transcript entries."""

    def __init__(self):
        self.project_path: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def extract_timestamp(self, entry: dict) -> Optional[datetime]:
        """Extract timestamp from an entry."""
        if "timestamp" not in entry:
            return None

        try:
            ts = entry["timestamp"]
            if isinstance(ts, (int, float)):
                timestamp = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                self._update_time_bounds(timestamp)
                return timestamp
        except (ValueError, TypeError):
            pass
        return None

    def _update_time_bounds(self, timestamp: datetime) -> None:
        """Update session start/end times."""
        if self.start_time is None or timestamp < self.start_time:
            self.start_time = timestamp
        if self.end_time is None or timestamp > self.end_time:
            self.end_time = timestamp

    def extract_project_path(self, entry: dict) -> Optional[str]:
        """Extract project path from entry (first occurrence wins)."""
        if self.project_path is not None:
            return self.project_path

        if "cwd" in entry:
            self.project_path = entry["cwd"]
        elif "project" in entry:
            self.project_path = entry["project"]

        return self.project_path


# =============================================================================
# Legacy Format Handler
# =============================================================================


class LegacyFormatHandler:
    """Handles legacy transcript formats."""

    def parse_legacy_tool_use(
        self, entry: dict, timestamp: Optional[datetime]
    ) -> list[ToolCall]:
        """Parse legacy toolUse array at entry level."""
        tool_calls = []
        for tu in entry.get("toolUse", []):
            tc = ToolCall(
                name=tu.get("name", "unknown"),
                input=tu.get("input", {}),
                timestamp=timestamp,
            )
            tool_calls.append(tc)
        return tool_calls


# =============================================================================
# Main Parsing Functions
# =============================================================================


def parse_transcript_file(file_path: str | Path) -> ParsedTranscript:
    """
    Parse a transcript from a JSONL file.

    Args:
        file_path: Path to the JSONL transcript file

    Returns:
        ParsedTranscript with extracted data

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Transcript file not found: {file_path}")

    content = file_path.read_text(encoding="utf-8")
    session_id = file_path.stem  # Use filename as session ID

    return parse_transcript_jsonl(content, session_id)


def parse_transcript_jsonl(content: str, session_id: str = "unknown") -> ParsedTranscript:
    """
    Parse a transcript from JSONL content.

    Claude Code transcripts are JSONL files where each line is a JSON object
    representing an event in the session.

    Args:
        content: JSONL content string
        session_id: Session identifier

    Returns:
        ParsedTranscript with extracted data
    """
    messages: list[Message] = []
    all_tool_calls: list[ToolCall] = []

    metadata = TranscriptMetadataExtractor()
    legacy_handler = LegacyFormatHandler()

    for line_num, line in enumerate(content.strip().split("\n"), 1):
        line = line.strip()
        if not line:
            continue

        try:
            entry = json.loads(line)
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON on line {line_num}: {e}")
            continue

        # Extract metadata
        timestamp = metadata.extract_timestamp(entry)
        metadata.extract_project_path(entry)

        # Extract message content
        message = entry.get("message", {})
        role = message.get("role", entry.get("type", ""))
        msg_content = message.get("content", entry.get("display", entry.get("content", "")))

        # Handle string content
        if isinstance(msg_content, str) and msg_content:
            messages.append(
                Message(
                    role=role,
                    content=msg_content,
                    timestamp=timestamp,
                )
            )

        # Handle array content blocks
        elif isinstance(msg_content, list):
            parser = ContentBlockParser(timestamp)
            result = parser.parse_content_array(msg_content)

            # Collect tool calls
            all_tool_calls.extend(result.tool_calls)

            # Create message if we have content
            combined_text = "\n".join(result.text_parts)
            if combined_text or result.tool_calls:
                messages.append(
                    Message(
                        role=role,
                        content=combined_text,
                        timestamp=timestamp,
                        tool_calls=result.tool_calls,
                    )
                )

        # Handle legacy format
        if "toolUse" in entry:
            legacy_tools = legacy_handler.parse_legacy_tool_use(entry, timestamp)
            all_tool_calls.extend(legacy_tools)

    return ParsedTranscript(
        session_id=session_id,
        project_path=metadata.project_path,
        messages=messages,
        tool_calls=all_tool_calls,
        start_time=metadata.start_time,
        end_time=metadata.end_time,
    )


def extract_changed_files(transcript: ParsedTranscript) -> list[str]:
    """
    Extract list of files that were modified in the session.

    Args:
        transcript: Parsed transcript

    Returns:
        List of file paths that were edited
    """
    return transcript.files_edited
