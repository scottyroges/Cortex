"""
Session Processing Logic

Shared logic for processing Claude Code sessions - generates summaries
via LLM and saves to Cortex memory. Used by both async queue processing
and synchronous API endpoints.
"""

from dataclasses import dataclass
from typing import Optional

from src.configs import get_logger

logger = get_logger("autocapture.processor")


@dataclass
class ProcessingResult:
    """Result of session processing."""

    success: bool
    """Whether processing completed successfully."""

    summary: Optional[str] = None
    """Generated summary text (if successful)."""

    error: Optional[str] = None
    """Error message (if failed)."""

    session_id: Optional[str] = None
    """Session identifier."""


def process_session(
    session_id: str,
    transcript_text: str,
    files_edited: list[str],
    repository: str,
    initiative_id: Optional[str] = None,
    max_transcript_chars: int = 100000,
) -> ProcessingResult:
    """
    Process a session: generate LLM summary and save to Cortex.

    This is the shared implementation used by both:
    - QueueProcessor (async background processing)
    - /process-sync endpoint (synchronous processing)

    Args:
        session_id: Unique session identifier
        transcript_text: Full transcript text for summarization
        files_edited: List of files edited in the session
        repository: Repository name
        initiative_id: Optional initiative ID to tag the session
        max_transcript_chars: Maximum transcript length (default 100k)

    Returns:
        ProcessingResult with success status, summary, or error
    """
    # Import here to avoid circular imports at module load time
    from src.configs.yaml_config import load_yaml_config
    from src.external.llm import get_provider
    from src.tools.memory import conclude_session

    # Validate input
    if not transcript_text or not transcript_text.strip():
        logger.debug(f"Empty transcript for session {session_id}")
        return ProcessingResult(
            success=True,
            session_id=session_id,
            error="empty_transcript",
        )

    # Load config and get LLM provider
    try:
        config = load_yaml_config()
        provider = get_provider(config)
        if provider is None:
            return ProcessingResult(
                success=False,
                session_id=session_id,
                error="No LLM provider available",
            )
    except Exception as e:
        logger.error(f"Failed to get LLM provider: {e}")
        return ProcessingResult(
            success=False,
            session_id=session_id,
            error=f"No LLM provider: {e}",
        )

    # Generate summary
    try:
        # Truncate transcript if needed
        truncated_text = transcript_text[:max_transcript_chars]
        logger.debug(f"Generating summary for session {session_id}")
        summary = provider.summarize_session(truncated_text)

        if not summary:
            return ProcessingResult(
                success=False,
                session_id=session_id,
                error="Summarization returned empty result",
            )

        logger.debug(f"Generated summary ({len(summary)} chars)")
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        return ProcessingResult(
            success=False,
            session_id=session_id,
            error=f"Summarization failed: {e}",
        )

    # Save to Cortex
    try:
        conclude_session(
            summary=summary,
            changed_files=files_edited,
            repository=repository,
            initiative=initiative_id,
        )
        initiative_info = f" (initiative: {initiative_id})" if initiative_id else ""
        logger.info(f"Saved session {session_id} to Cortex: {repository}{initiative_info}")

        return ProcessingResult(
            success=True,
            session_id=session_id,
            summary=summary,
        )
    except Exception as e:
        logger.error(f"Failed to save session to Cortex: {e}")
        return ProcessingResult(
            success=False,
            session_id=session_id,
            error=f"Save failed: {e}",
        )
