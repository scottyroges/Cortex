"""
Navigation Document Schemas (The Map)

Tells the agent WHERE to look in the codebase.

Document Types:
- file_metadata: Primary search anchor with file descriptions
- dependency: Import/export relationships between files
- skeleton: Directory structure overview
"""

from .base import BaseMetadata


class FileMetadataDoc(BaseMetadata):
    """Metadata for file_metadata documents - the primary search anchor."""

    file_path: str
    language: str
    description: str  # AI-generated behavioral summary
    exports: str  # CSV list of exported symbols (limited to 20)
    is_entry_point: bool
    is_barrel: bool
    is_test: bool
    is_config: bool
    entry_point_type: str  # main, api_route, cli, event_handler
    related_tests: str  # CSV of test file paths
    file_hash: str  # MD5 for staleness tracking


class DependencyDoc(BaseMetadata):
    """Metadata for dependency documents - the impact graph."""

    file_path: str
    imports: str  # CSV list of imported files
    imported_by: str  # CSV list of files that import this
    import_count: int
    imported_by_count: int
    impact_tier: str  # High (>5 dependents), Medium (2-5), Low (0-1)


class SkeletonDoc(BaseMetadata):
    """Metadata for skeleton documents - the directory structure."""

    total_files: int
    total_dirs: int
