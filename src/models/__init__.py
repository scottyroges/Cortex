"""
Cortex Document Models

Central exports for all document types, schemas, and validation utilities.
"""

# Base types and constants
from .base import (
    ALL_DOCUMENT_TYPES,
    BRANCH_FILTERED_TYPES,
    METADATA_ONLY_TYPES,
    RECENCY_BOOSTED_TYPES,
    SEARCH_PRESETS,
    TYPE_CATEGORIES,
    TYPE_MULTIPLIERS,
    BaseMetadata,
    DocumentType,
    TypeCategory,
)

# Navigation schemas (The Map)
from .navigation import (
    DependencyDoc,
    FileMetadataDoc,
    SkeletonDoc,
)

# Usage schemas (The Manual)
from .usage import (
    DataContractDoc,
    EntryPointDoc,
    IdiomDoc,
)

# Memory schemas (The Brain)
from .memory import (
    InitiativeDoc,
    InsightDoc,
    NoteDoc,
    SessionSummaryDoc,
    TechStackDoc,
)

# Validation utilities
from .validation import (
    get_type_category,
    is_valid_document_type,
    validate_document_type,
)

__all__ = [
    # Types
    "DocumentType",
    "TypeCategory",
    "ALL_DOCUMENT_TYPES",
    # Category mapping
    "TYPE_CATEGORIES",
    # Base schema
    "BaseMetadata",
    # Navigation schemas
    "FileMetadataDoc",
    "DependencyDoc",
    "SkeletonDoc",
    # Usage schemas
    "EntryPointDoc",
    "DataContractDoc",
    "IdiomDoc",
    # Memory schemas
    "NoteDoc",
    "SessionSummaryDoc",
    "InsightDoc",
    "TechStackDoc",
    "InitiativeDoc",
    # Constants
    "BRANCH_FILTERED_TYPES",
    "RECENCY_BOOSTED_TYPES",
    "TYPE_MULTIPLIERS",
    "SEARCH_PRESETS",
    "METADATA_ONLY_TYPES",
    # Validation
    "validate_document_type",
    "is_valid_document_type",
    "get_type_category",
]
