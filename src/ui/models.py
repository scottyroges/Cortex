"""
Data models for the Cortex browser.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Stats:
    """Collection statistics."""
    total_documents: int
    by_repository: dict[str, int] = field(default_factory=dict)
    by_type: dict[str, int] = field(default_factory=dict)
    by_language: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Stats":
        return cls(
            total_documents=data.get("total_documents", 0),
            by_repository=data.get("by_repository", {}),
            by_type=data.get("by_type", {}),
            by_language=data.get("by_language", {}),
        )


@dataclass
class DocumentSummary:
    """Summary of a document for list display."""
    id: str
    doc_type: str
    repository: str
    title: Optional[str] = None
    created_at: Optional[str] = None
    status: Optional[str] = None
    initiative_name: Optional[str] = None
    # For insights
    last_validation_result: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocumentSummary":
        meta = data.get("metadata", {})
        return cls(
            id=data.get("id", ""),
            doc_type=meta.get("type", "unknown"),
            repository=meta.get("repository", "unknown"),
            title=meta.get("title"),
            created_at=meta.get("created_at"),
            status=meta.get("status"),
            initiative_name=meta.get("initiative_name"),
            last_validation_result=meta.get("last_validation_result"),
        )


@dataclass
class Document:
    """Full document with content."""
    id: str
    content: str
    metadata: dict[str, Any]
    has_embedding: bool = False

    @property
    def doc_type(self) -> str:
        return self.metadata.get("type", "unknown")

    @property
    def repository(self) -> str:
        return self.metadata.get("repository", "unknown")

    @property
    def title(self) -> Optional[str]:
        return self.metadata.get("title")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Document":
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            metadata=data.get("metadata", {}),
            has_embedding=data.get("has_embedding", False),
        )


@dataclass
class SearchResultScores:
    """Scores from search."""
    rrf: Optional[float] = None
    rerank: Optional[float] = None
    vector_distance: Optional[float] = None
    bm25: Optional[float] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchResultScores":
        return cls(
            rrf=data.get("rrf"),
            rerank=data.get("rerank"),
            vector_distance=data.get("vector_distance"),
            bm25=data.get("bm25"),
        )


@dataclass
class SearchResult:
    """A single search result."""
    id: str
    content_preview: str
    metadata: dict[str, Any]
    scores: SearchResultScores

    @property
    def doc_type(self) -> str:
        return self.metadata.get("type", "unknown")

    @property
    def title(self) -> Optional[str]:
        return self.metadata.get("title")

    @property
    def best_score(self) -> float:
        """Return the best available score for sorting/display."""
        if self.scores.rerank is not None:
            return self.scores.rerank
        if self.scores.rrf is not None:
            return self.scores.rrf
        return 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchResult":
        return cls(
            id=data.get("id", ""),
            content_preview=data.get("content_preview", ""),
            metadata=data.get("metadata", {}),
            scores=SearchResultScores.from_dict(data.get("scores", {})),
        )


@dataclass
class SearchResponse:
    """Response from a search query."""
    query: str
    results: list[SearchResult]
    timing_ms: float
    result_count: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchResponse":
        return cls(
            query=data.get("query", ""),
            results=[SearchResult.from_dict(r) for r in data.get("results", [])],
            timing_ms=data.get("timing", {}).get("total_ms", 0),
            result_count=data.get("result_count", 0),
        )
