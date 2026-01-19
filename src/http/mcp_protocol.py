"""
MCP Protocol Endpoints

HTTP endpoints for MCP tool calls (daemon mode).
Uses Pydantic models as the single source of truth for tool schemas.
"""

from typing import Any, Callable, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field, ValidationError

from logging_config import get_logger

logger = get_logger("http.mcp")

router = APIRouter()


# --- Request/Response Models ---


class MCPToolCallRequest(BaseModel):
    """Request body for MCP tool call."""

    name: str
    arguments: dict = {}


class MCPToolResult(BaseModel):
    """Response for MCP tool call."""

    content: Any
    isError: bool = False


# --- Tool Input Models ---
# These Pydantic models are the SINGLE SOURCE OF TRUTH for tool schemas.
# The JSON Schema is auto-generated from these models.


class OrientSessionInput(BaseModel):
    project_path: str = Field(..., description="Absolute path to the project repository")


class SearchCortexInput(BaseModel):
    query: str = Field(..., description="Natural language search query")
    repository: Optional[str] = Field(None, description="Repository identifier for filtering")
    min_score: Optional[float] = Field(None, description="Minimum relevance score (0-1)")
    branch: Optional[str] = Field(None, description="Optional branch filter")
    initiative: Optional[str] = Field(None, description="Initiative ID or name to filter results")
    include_completed: bool = Field(True, description="Include content from completed initiatives")
    types: Optional[list[str]] = Field(
        None,
        description="Filter by document types. Valid: skeleton, note, session_summary, insight, tech_stack, initiative, file_metadata, data_contract, entry_point, dependency, idiom. Example: ['note', 'insight'] for understanding-only search.",
    )
    preset: Optional[str] = Field(
        None,
        description="Search preset. Overrides types. Valid: 'understanding' (insights, notes), 'navigation' (file_metadata, entry_points), 'structure' (file_metadata, dependencies, skeleton)",
    )


class IngestCodeInput(BaseModel):
    path: str = Field(..., description="Absolute path to codebase root")
    repository: Optional[str] = Field(
        None, description="Optional repository identifier (defaults to directory name)"
    )
    force_full: bool = Field(False, description="Force full re-ingestion")
    include_patterns: Optional[list[str]] = Field(
        None,
        description="Glob patterns for selective ingestion. Only files matching at least one pattern are indexed (e.g., ['src/**', 'tests/**'])",
    )
    use_cortexignore: bool = Field(
        True, description="Load ignore patterns from global ~/.cortex/cortexignore and .cortexignore files"
    )


class GetIngestStatusInput(BaseModel):
    task_id: str = Field(
        ..., description="Task ID returned by ingest_code_into_cortex for async operations"
    )


class SessionSummaryInput(BaseModel):
    summary: str = Field(
        ...,
        description="Detailed summary of the session: what changed, why, decisions made, problems solved, and future TODOs",
    )
    changed_files: list[str] = Field(..., description="List of modified file paths")
    repository: Optional[str] = Field(None, description="Repository identifier")
    initiative: Optional[str] = Field(
        None, description="Initiative ID or name to tag (uses focused initiative if not specified)"
    )


class SaveNoteInput(BaseModel):
    content: str = Field(..., description="Note content")
    title: Optional[str] = Field(None, description="Optional title")
    tags: Optional[list[str]] = Field(None, description="Optional tags")
    repository: Optional[str] = Field(None, description="Repository identifier")
    initiative: Optional[str] = Field(
        None, description="Initiative ID or name to tag (uses focused initiative if not specified)"
    )


class InsightInput(BaseModel):
    insight: str = Field(..., description="The analysis/understanding to save")
    files: list[str] = Field(..., description="List of file paths this insight is about (REQUIRED)")
    title: Optional[str] = Field(None, description="Optional title for the insight")
    tags: Optional[list[str]] = Field(None, description="Optional tags for categorization")
    repository: Optional[str] = Field(
        None, description="Repository identifier (auto-detected if not provided)"
    )
    initiative: Optional[str] = Field(
        None, description="Initiative ID or name to tag (uses focused initiative if not specified)"
    )


class SetRepoContextInput(BaseModel):
    repository: str = Field(..., description="Repository identifier (e.g., 'Cortex', 'my-app')")
    tech_stack: str = Field(
        ...,
        description="Technologies, patterns, architecture description. Focus on stable structural info, not specifics that get stale.",
    )


class SetInitiativeInput(BaseModel):
    repository: str = Field(..., description="Repository identifier")
    name: str = Field(..., description="Initiative/epic name")
    status: Optional[str] = Field(None, description="Current state/progress (optional)")


class CreateInitiativeInput(BaseModel):
    repository: str = Field(..., description="Repository identifier (e.g., 'Cortex', 'my-app')")
    name: str = Field(
        ..., description="Initiative name (e.g., 'Auth Migration', 'Performance Optimization')"
    )
    goal: Optional[str] = Field(None, description="Optional goal/description for the initiative")
    auto_focus: bool = Field(
        True, description="Whether to focus this initiative on creation (default: true)"
    )


class ListInitiativesInput(BaseModel):
    repository: str = Field(..., description="Repository identifier")
    status: Literal["all", "active", "completed"] = Field(
        "all", description="Filter by status: 'all', 'active', or 'completed'"
    )


class FocusInitiativeInput(BaseModel):
    repository: str = Field(..., description="Repository identifier")
    initiative: str = Field(..., description="Initiative ID or name to focus")


class CompleteInitiativeInput(BaseModel):
    initiative: str = Field(..., description="Initiative ID or name to complete")
    summary: str = Field(..., description="Completion summary describing what was accomplished")
    repository: Optional[str] = Field(
        None, description="Repository identifier (optional if using initiative ID)"
    )


class GetRepoContextInput(BaseModel):
    repository: str = Field(..., description="Repository identifier")


class ConfigureCortexInput(BaseModel):
    min_score: Optional[float] = Field(None, description="Minimum relevance score (0-1)")
    verbose: Optional[bool] = Field(None, description="Enable verbose output")
    top_k_retrieve: Optional[int] = Field(None, description="Candidates before reranking")
    top_k_rerank: Optional[int] = Field(None, description="Results after reranking")
    llm_provider: Optional[str] = Field(
        None, description="LLM provider: anthropic, claude-cli, ollama, openrouter, or none"
    )
    recency_boost: Optional[bool] = Field(
        None, description="Enable recency boosting for notes/session_summaries"
    )
    recency_half_life_days: Optional[float] = Field(
        None, description="Days until recency boost decays to ~0.5"
    )
    enabled: Optional[bool] = Field(None, description="Enable or disable Cortex memory system")


class GetSkeletonInput(BaseModel):
    repository: Optional[str] = Field(None, description="Repository name")


class GetCortexVersionInput(BaseModel):
    expected_commit: Optional[str] = Field(
        None,
        description="Git commit hash to compare against (e.g., local HEAD). If provided, returns needs_rebuild field.",
    )


class RecallRecentWorkInput(BaseModel):
    repository: str = Field(..., description="Repository identifier")
    days: int = Field(7, description="Number of days to look back (default: 7)")
    limit: int = Field(20, description="Maximum number of items to return (default: 20)")
    include_code: bool = Field(
        False, description="Include code changes in results (default: false, notes/session_summaries only)"
    )


class SummarizeInitiativeInput(BaseModel):
    initiative: str = Field(..., description="Initiative ID or name")
    repository: Optional[str] = Field(
        None, description="Repository identifier (optional if using initiative ID)"
    )


class ValidateInsightInput(BaseModel):
    insight_id: str = Field(..., description="The insight ID to validate (e.g., 'insight:abc123')")
    validation_result: Literal["still_valid", "partially_valid", "no_longer_valid"] = Field(
        ..., description="Your assessment after re-reading the linked files"
    )
    notes: Optional[str] = Field(
        None, description="Optional notes about what changed or why validation failed"
    )
    deprecate: bool = Field(
        False,
        description="If True and validation_result is 'no_longer_valid', mark insight as deprecated",
    )
    replacement_insight: Optional[str] = Field(
        None, description="If deprecating, optionally provide updated insight content to save as replacement"
    )
    repository: Optional[str] = Field(None, description="Repository identifier (optional)")


class GetAutocaptureStatusInput(BaseModel):
    pass  # No parameters


class ConfigureAutocaptureInput(BaseModel):
    enabled: Optional[bool] = Field(None, description="Enable or disable auto-capture")
    llm_provider: Optional[Literal["anthropic", "ollama", "openrouter", "claude-cli"]] = Field(
        None, description="Primary LLM provider for summarization"
    )
    auto_commit_async: Optional[bool] = Field(
        None,
        description="When true (default), hook exits fast and daemon processes in background. When false, hook waits for LLM summary + commit to complete.",
    )
    sync_timeout: Optional[int] = Field(
        None, description="Timeout in seconds for sync mode (default: 60, range: 10-300)"
    )
    min_tokens: Optional[int] = Field(
        None, description="Minimum token threshold for significant sessions"
    )
    min_file_edits: Optional[int] = Field(
        None, description="Minimum file edit threshold for significant sessions"
    )
    min_tool_calls: Optional[int] = Field(
        None, description="Minimum tool call threshold for significant sessions"
    )


# --- Tool Registry ---


class ToolDef:
    """Definition of an MCP tool with its function, input model, and description."""

    def __init__(
        self,
        name: str,
        fn: Callable,
        input_model: type[BaseModel],
        description: str,
    ):
        self.name = name
        self.fn = fn
        self.input_model = input_model
        self.description = description

    def schema(self) -> dict:
        """Generate MCP-compatible JSON schema for this tool."""
        json_schema = self.input_model.model_json_schema()
        # Remove Pydantic metadata that MCP doesn't need
        json_schema.pop("title", None)
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": json_schema,
        }


def _build_tool_registry() -> dict[str, ToolDef]:
    """
    Build the tool registry with lazy imports to avoid circular dependencies.

    Returns a dict mapping tool names to their ToolDef.
    """
    from src.tools import (
        session_summary_to_cortex,
        complete_initiative,
        configure_cortex,
        create_initiative,
        focus_initiative,
        get_repo_context,
        get_cortex_version,
        get_skeleton,
        ingest_code_into_cortex,
        insight_to_cortex,
        list_initiatives,
        orient_session,
        recall_recent_work,
        save_note_to_cortex,
        search_cortex,
        set_initiative,
        set_repo_context,
        summarize_initiative,
        validate_insight,
    )
    from src.tools.ingest import get_ingest_status
    from src.tools.autocapture import (
        get_autocapture_status,
        configure_autocapture,
    )

    tools = [
        ToolDef(
            name="orient_session",
            fn=orient_session,
            input_model=OrientSessionInput,
            description="Entry point for starting a session. Returns indexed status, skeleton, tech stack, active initiative, and staleness detection.",
        ),
        ToolDef(
            name="search_cortex",
            fn=search_cortex,
            input_model=SearchCortexInput,
            description="Search the Cortex memory for relevant code, documentation, or notes.",
        ),
        ToolDef(
            name="ingest_code_into_cortex",
            fn=ingest_code_into_cortex,
            input_model=IngestCodeInput,
            description="Ingest a codebase directory into Cortex memory. Extracts structured metadata (file_metadata, data_contract, entry_point, dependency) to help AI agents navigate codebases.",
        ),
        ToolDef(
            name="get_ingest_status",
            fn=get_ingest_status,
            input_model=GetIngestStatusInput,
            description="Get the status of an async ingestion task. Use this to poll progress after ingest_code_into_cortex returns a task_id for async operations (full reindex or large delta).",
        ),
        ToolDef(
            name="session_summary_to_cortex",
            fn=session_summary_to_cortex,
            input_model=SessionSummaryInput,
            description="Save a session summary and re-index changed files. IMPORTANT: Write a comprehensive summary that captures the FULL context of this session, including: (1) What was implemented/changed and WHY, (2) Key architectural decisions made, (3) Problems encountered and how they were solved, (4) Non-obvious patterns or gotchas discovered, (5) Future work or TODOs identified. This summary will be retrieved in future sessions to restore context, so include enough detail to resume this work months later.",
        ),
        ToolDef(
            name="save_note_to_cortex",
            fn=save_note_to_cortex,
            input_model=SaveNoteInput,
            description="Save a note, documentation snippet, or decision to Cortex memory.",
        ),
        ToolDef(
            name="insight_to_cortex",
            fn=insight_to_cortex,
            input_model=InsightInput,
            description="Save architectural insights linked to specific code files. **Use this tool proactively** when you've done significant code analysis and want to preserve your understanding. Examples: 'This module uses the observer pattern', 'The auth flow has a race condition here'. Insights are linked to files so future searches return both code AND your previous analysis.",
        ),
        ToolDef(
            name="set_repo_context",
            fn=set_repo_context,
            input_model=SetRepoContextInput,
            description="Set static tech stack context for a repository. This context is returned by orient_session and helps Claude understand the codebase. IMPORTANT: Only include stable, structural information that won't become stale. DO include: languages, frameworks, architecture patterns, module responsibilities, design philosophy. DO NOT include: version numbers, phase/status indicators, counts (e.g., '7 modules'), dates, or anything that changes frequently.",
        ),
        ToolDef(
            name="set_initiative",
            fn=set_initiative,
            input_model=SetInitiativeInput,
            description="(Legacy) Set or update the current initiative/workstream for a repository. Use create_initiative instead.",
        ),
        ToolDef(
            name="create_initiative",
            fn=create_initiative,
            input_model=CreateInitiativeInput,
            description="Create a new initiative for a repository. Initiatives track multi-session work like epics, migrations, or features. New session summaries and notes are automatically tagged with the focused initiative.",
        ),
        ToolDef(
            name="list_initiatives",
            fn=list_initiatives,
            input_model=ListInitiativesInput,
            description="List all initiatives for a repository with optional status filtering.",
        ),
        ToolDef(
            name="focus_initiative",
            fn=focus_initiative,
            input_model=FocusInitiativeInput,
            description="Set focus to an initiative. New session summaries and notes will be tagged with this initiative.",
        ),
        ToolDef(
            name="complete_initiative",
            fn=complete_initiative,
            input_model=CompleteInitiativeInput,
            description="Mark an initiative as completed with a summary. The initiative and its associated session summaries/notes remain searchable but with recency decay.",
        ),
        ToolDef(
            name="get_repo_context",
            fn=get_repo_context,
            input_model=GetRepoContextInput,
            description="Get stored tech stack and initiative context for a repository.",
        ),
        ToolDef(
            name="configure_cortex",
            fn=configure_cortex,
            input_model=ConfigureCortexInput,
            description="Configure Cortex runtime settings.",
        ),
        ToolDef(
            name="get_skeleton",
            fn=get_skeleton,
            input_model=GetSkeletonInput,
            description="Get the file tree structure for a repository.",
        ),
        ToolDef(
            name="get_cortex_version",
            fn=get_cortex_version,
            input_model=GetCortexVersionInput,
            description="Get Cortex daemon build and version information. Pass expected_commit to check if rebuild is needed.",
        ),
        ToolDef(
            name="recall_recent_work",
            fn=recall_recent_work,
            input_model=RecallRecentWorkInput,
            description="Recall recent session summaries and notes for a repository. Returns a timeline view of recent work, grouped by day, with initiative context. Answers 'What did I work on this week?' without manual search queries.",
        ),
        ToolDef(
            name="summarize_initiative",
            fn=summarize_initiative,
            input_model=SummarizeInitiativeInput,
            description="Generate a narrative summary of an initiative's progress. Gathers all session summaries and notes tagged with the initiative and synthesizes a timeline with key decisions, problems solved, and current state.",
        ),
        ToolDef(
            name="validate_insight",
            fn=validate_insight,
            input_model=ValidateInsightInput,
            description="Validate a stored insight against current code state. Use this after re-reading linked files to confirm whether a stale insight is still accurate. Can mark invalid insights as deprecated and optionally create a replacement.",
        ),
        ToolDef(
            name="get_autocapture_status",
            fn=get_autocapture_status,
            input_model=GetAutocaptureStatusInput,
            description="Get status of the auto-capture system including hook installation, LLM provider availability, configuration, and recent capture statistics.",
        ),
        ToolDef(
            name="configure_autocapture",
            fn=configure_autocapture,
            input_model=ConfigureAutocaptureInput,
            description="Configure auto-capture settings. Changes are persisted to ~/.cortex/config.yaml.",
        ),
    ]

    return {tool.name: tool for tool in tools}


# Lazy-initialized registry
_tool_registry: dict[str, ToolDef] | None = None


def _get_registry() -> dict[str, ToolDef]:
    """Get or initialize the tool registry."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = _build_tool_registry()
    return _tool_registry


# --- Endpoints ---


@router.get("/tools/list")
def mcp_list_tools() -> dict[str, Any]:
    """
    List available MCP tools.

    Returns tool definitions in MCP protocol format with auto-generated schemas.
    """
    logger.info("MCP tools/list requested")
    registry = _get_registry()
    return {"tools": [tool.schema() for tool in registry.values()]}


@router.post("/tools/call")
def mcp_call_tool(request: MCPToolCallRequest) -> MCPToolResult:
    """
    Execute an MCP tool with Pydantic validation.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        Tool result or error
    """
    logger.info(f"MCP tools/call: {request.name}")

    registry = _get_registry()
    tool = registry.get(request.name)

    if not tool:
        logger.error(f"Unknown tool: {request.name}")
        return MCPToolResult(
            content={"error": f"Unknown tool: {request.name}"},
            isError=True,
        )

    try:
        # Validate input with Pydantic model
        validated = tool.input_model.model_validate(request.arguments)
        # Call function with validated arguments
        result = tool.fn(**validated.model_dump(exclude_none=True))
        logger.debug(f"Tool {request.name} completed successfully")
        return MCPToolResult(content=result)
    except ValidationError as e:
        logger.error(f"Tool {request.name} validation failed: {e}")
        return MCPToolResult(
            content={"error": f"Invalid arguments: {e.errors()}"},
            isError=True,
        )
    except Exception as e:
        logger.error(f"Tool {request.name} failed: {e}")
        return MCPToolResult(
            content={"error": str(e)},
            isError=True,
        )
