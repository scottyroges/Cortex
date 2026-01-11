# Cortex Memory System

This project is **Cortex**, a local RAG memory system for Claude Code.

## Quick Reference

When working in this codebase:
- **Search**: `search_cortex` for code/notes lookup
- **Ingest**: `ingest_code_into_cortex` to index a repo
- **Save**: `save_note_to_cortex` for decisions/learnings
- **Commit**: `commit_to_cortex` at end of significant work

## Direct Tool Macros

When the user types `cortex>>` followed by a command, execute the corresponding MCP tool directly without interpretation:

| User Input | Action |
|------------|--------|
| `cortex>> search <query>` | Call `search_cortex` with the query |
| `cortex>> save <content>` | Call `save_note_to_cortex` with the content |
| `cortex>> ingest <path>` | Call `ingest_code_into_cortex` with the path |
| `cortex>> skeleton` | Call `get_skeleton` for current project |
| `cortex>> status` | Call `get_cortex_version` to check daemon status |

### Examples

```
User: cortex>> search authentication middleware
Action: search_cortex(query="authentication middleware")

User: cortex>> save Decided to use JWT tokens for session management
Action: save_note_to_cortex(content="Decided to use JWT tokens for session management")

User: cortex>> ingest ~/Projects/api-server
Action: ingest_code_into_cortex(path="~/Projects/api-server")
```

These macros bypass natural language interpretation - just execute the tool directly with the provided arguments.
