"""
Document Type Validation

Runtime validation utilities for document types.
"""

from .base import ALL_DOCUMENT_TYPES, TYPE_CATEGORIES, DocumentType, TypeCategory


def validate_document_type(type_str: str) -> DocumentType:
    """
    Validate and return a document type.

    Args:
        type_str: String to validate as a document type

    Returns:
        The validated DocumentType

    Raises:
        ValueError: If type_str is not a valid document type
    """
    if type_str not in ALL_DOCUMENT_TYPES:
        raise ValueError(
            f"Invalid document type: '{type_str}'. "
            f"Valid types: {', '.join(ALL_DOCUMENT_TYPES)}"
        )
    return type_str  # type: ignore


def is_valid_document_type(type_str: str) -> bool:
    """Check if a string is a valid document type."""
    return type_str in ALL_DOCUMENT_TYPES


def get_type_category(doc_type: str) -> TypeCategory | None:
    """Get the category for a document type."""
    return TYPE_CATEGORIES.get(doc_type)  # type: ignore
