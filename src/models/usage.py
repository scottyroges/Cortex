"""
Usage Document Schemas (The Manual)

Tells the agent HOW to use the codebase.

Document Types:
- entry_point: Triggers and entry points (API routes, CLI commands, etc.)
- data_contract: Type definitions and data shapes
- idiom: Gold standard coding patterns
"""

from .base import BaseMetadata


class EntryPointDoc(BaseMetadata):
    """Metadata for entry_point documents - the triggers."""

    file_path: str
    entry_type: str  # main, api_route, cli, event_handler
    language: str
    triggers: str  # JSON array: [{"method": "POST", "route": "/v1/ingest"}]
    summary: str  # User-facing behavior description
    file_hash: str


class DataContractDoc(BaseMetadata):
    """Metadata for data_contract documents - the shapes."""

    name: str  # Type/interface name
    file_path: str
    contract_type: str  # interface, class, dataclass, type_alias, pydantic_model
    language: str
    fields: str  # CSV: name1:type1,name2:type2 (limited to 20)
    validation_rules: str  # JSON array of validation rules


class IdiomDoc(BaseMetadata):
    """Metadata for idiom documents - the gold standard coding patterns."""

    title: str
    language: str
    description: str  # What this idiom enforces
    related_files: str  # JSON array of file paths
