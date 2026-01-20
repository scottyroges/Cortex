"""
Base Document Types and Constants for Cortex

Core type definitions, categories, and constants used across all document types.

Document Categories:
- Navigation (The Map): file_metadata, dependency, skeleton
- Understanding & Usage (The Manual): entry_point, data_contract, idiom
- Semantic Memory (The Brain): note, session_summary, insight, tech_stack, initiative
"""

from enum import Enum
from typing import Literal, TypedDict, get_args


# =============================================================================
# Document Type Literal
# =============================================================================

DocumentType = Literal[
    # Navigation (The Map) - tells the agent WHERE to look
    "file_metadata",
    "dependency",
    "skeleton",
    # Understanding & Usage (The Manual) - tells the agent HOW to use
    "entry_point",
    "data_contract",
    "idiom",
    # Semantic Memory (The Brain) - captures decisions and understanding
    "note",
    "session_summary",
    "insight",
    "tech_stack",
    "initiative",
]

# All valid document types as a tuple (for runtime validation)
ALL_DOCUMENT_TYPES: tuple[str, ...] = get_args(DocumentType)


# =============================================================================
# Type Categories
# =============================================================================


class TypeCategory(str, Enum):
    """Categories of document types for filtering and scoring logic."""

    NAVIGATION = "navigation"  # file_metadata, dependency, skeleton
    USAGE = "usage"  # entry_point, data_contract, idiom
    MEMORY = "memory"  # note, session_summary, insight
    CONTEXT = "context"  # tech_stack, initiative


TYPE_CATEGORIES: dict[DocumentType, TypeCategory] = {
    # Navigation
    "file_metadata": TypeCategory.NAVIGATION,
    "dependency": TypeCategory.NAVIGATION,
    "skeleton": TypeCategory.NAVIGATION,
    # Usage
    "entry_point": TypeCategory.USAGE,
    "data_contract": TypeCategory.USAGE,
    "idiom": TypeCategory.USAGE,
    # Memory
    "note": TypeCategory.MEMORY,
    "session_summary": TypeCategory.MEMORY,
    "insight": TypeCategory.MEMORY,
    # Context
    "tech_stack": TypeCategory.CONTEXT,
    "initiative": TypeCategory.CONTEXT,
}


# =============================================================================
# Base Metadata Schema
# =============================================================================


class BaseMetadata(TypedDict, total=False):
    """Base metadata fields common to all document types."""

    type: str  # DocumentType (str for ChromaDB compatibility)
    repository: str
    branch: str
    created_at: str  # ISO 8601
    indexed_at: str  # ISO 8601
    status: str  # active, deprecated


# =============================================================================
# Constants
# =============================================================================

# Types that should be filtered by branch (code-specific)
BRANCH_FILTERED_TYPES: set[str] = {
    "skeleton",
    "file_metadata",
    "data_contract",
    "entry_point",
    "dependency",
}

# Types that receive recency boosting (understanding decays, code doesn't)
RECENCY_BOOSTED_TYPES: set[str] = {
    "note",
    "session_summary",
}

# Type multipliers for search scoring
# Philosophy: "Code can be grepped. Understanding cannot."
TYPE_MULTIPLIERS: dict[str, float] = {
    # Understanding (highest value - irreplaceable)
    "insight": 2.0,
    "note": 1.5,
    "session_summary": 1.5,
    # Usage (high value - tells agent how)
    "entry_point": 1.4,
    "file_metadata": 1.3,
    "data_contract": 1.3,
    "idiom": 1.3,
    # Context
    "tech_stack": 1.2,
    # Standard
    "dependency": 1.0,
    "skeleton": 1.0,
    "initiative": 1.0,
}

# Search presets for common query patterns
SEARCH_PRESETS: dict[str, list[str]] = {
    # "Why did we...?" / "What was decided...?"
    "understanding": ["insight", "note", "session_summary"],
    # "How do I...?" / "Where is...?"
    "navigation": ["file_metadata", "entry_point", "data_contract", "idiom"],
    # "What's the architecture...?"
    "structure": ["file_metadata", "dependency", "skeleton"],
    # "What calls...?" / "What breaks if...?"
    "trace": ["entry_point", "dependency", "data_contract"],
    # Combined understanding + navigation
    "memory": ["insight", "note", "session_summary", "file_metadata"],
}

# Metadata-only types (no semantic memory, cross-initiative)
METADATA_ONLY_TYPES: set[str] = {
    "file_metadata",
    "data_contract",
    "entry_point",
    "dependency",
    "skeleton",
}
