"""
Memory Document Schemas (The Brain)

Captures decisions, understanding, and context that persists across sessions.

Document Types:
- note: Decisions and learnings
- session_summary: End-of-session context
- insight: Understanding anchored to specific files
- tech_stack: Repository technology context
- initiative: Multi-session workstreams
"""

from .base import BaseMetadata


class NoteDoc(BaseMetadata):
    """Metadata for note documents - decisions and learnings."""

    title: str
    tags: str  # JSON array
    initiative_id: str
    initiative_name: str
    verified_at: str  # ISO 8601


class SessionSummaryDoc(BaseMetadata):
    """Metadata for session_summary documents - end-of-session context."""

    files: str  # JSON array of changed files
    initiative_id: str
    initiative_name: str


class InsightDoc(BaseMetadata):
    """Metadata for insight documents - understanding anchored to files."""

    title: str
    tags: str  # JSON array
    files: str  # JSON array (required, non-empty)
    file_hashes: str  # JSON dict for staleness tracking
    initiative_id: str
    initiative_name: str
    verified_at: str  # ISO 8601
    last_validation_result: str  # still_valid, partially_valid, no_longer_valid


class TechStackDoc(BaseMetadata):
    """Metadata for tech_stack documents - repository context."""

    pass  # Uses only base fields


class InitiativeDoc(BaseMetadata):
    """Metadata for initiative documents - multi-session workstreams."""

    name: str
    goal: str
    completed_at: str  # ISO 8601, if completed
    completion_summary: str
