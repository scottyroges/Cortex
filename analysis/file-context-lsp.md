# File Context Feature: LSP Server for Browsing Notes in Editors

**Status**: Idea / Future Work
**Date**: 2026-01-18

## Problem

Developers browsing unfamiliar code have no way to see the Cortex notes/insights linked to files they're viewing. The understanding is stored but not surfaced at the moment of need.

## Proposed Solution

Build an LSP (Language Server Protocol) server that surfaces Cortex notes/insights while browsing code in any editor.

### Why LSP?

- Works with ALL editors: VS Code, JetBrains, Vim, Neovim, Emacs
- Single implementation, universal support
- Standard protocol with mature tooling (pygls for Python)

## Architecture

```
┌─────────────┐     stdio     ┌─────────────┐     HTTP      ┌─────────────┐
│   Editor    │ ◄───────────► │  LSP Server │ ◄───────────► │   Cortex    │
│ (VS Code,   │               │   (pygls)   │               │   Daemon    │
│  Neovim)    │               └─────────────┘               └─────────────┘
└─────────────┘
```

## LSP Features

| Feature | User Experience |
|---------|-----------------|
| **Hover** | Hover on any line → see insights linked to current file |
| **Code Lens** | "3 insights" indicator at top of file |
| **Diagnostics** | Yellow squiggles for stale insights needing verification |

## Implementation Phases

### Phase 1: Core Infrastructure (~3 hours)

1. **`src/tools/file_context.py`** - Core query function
   - Query insights/notes by file path
   - Handle partial path matching (`auth.py` matches `src/auth.py`)
   - Include staleness status

2. **HTTP endpoint** - `GET /browse/by-file?path=...`
   - Powers both MCP tool and LSP server

3. **MCP tool** - `get_context_for_file`
   - For Claude Code users: "what do we know about this file?"

### Phase 2: LSP Server (~6 hours)

```
src/lsp/
    __init__.py
    server.py      # pygls LSP server
    handlers.py    # hover, codelens, diagnostics
    client.py      # HTTP client for Cortex daemon
    __main__.py    # Entry point: python -m src.lsp
```

Dependencies: `pygls>=2.0.0`, `lsprotocol>=2024.0.0`

### Phase 3: Editor Integration (~4 hours)

1. **VS Code Extension** - `editors/vscode/cortex-insights/`
2. **Documentation** - Setup guides for Neovim, Vim, Emacs, JetBrains

## Technical Considerations

### ChromaDB Limitation

ChromaDB doesn't support `$contains` on JSON arrays. Must fetch all insights and filter in Python. Mitigations:
- Filter by repository first to reduce result set
- Cache results with TTL

### Repository Detection

LSP server needs to map file paths to Cortex repositories:
- Walk up directory tree to find `.git`
- Use directory name as repository identifier
- Cache the mapping

### Daemon Dependency

LSP server requires running Cortex daemon:
- Health check on startup
- Graceful degradation with clear error messages
- Auto-reconnect on daemon restart

## Value Proposition

| User | Benefit |
|------|---------|
| **Claude Code users** | Ask "what do we know about this file?" naturally |
| **Other developers** | See team's documented understanding while browsing code |
| **Onboarding** | New team members see context without asking |

## Related Work

- Current web interface at `src/browser/web/` shows notes but requires switching to browser
- Insights already store `files` metadata - infrastructure exists
- `src/tools/staleness.py` handles insight validation

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/tools/file_context.py` | Create |
| `src/http/browse.py` | Add endpoint |
| `src/http/mcp_protocol.py` | Add MCP tool |
| `src/lsp/` | Create package |
| `editors/vscode/cortex-insights/` | Create extension |
| `requirements.txt` | Add pygls |
| `tests/test_file_context.py` | Create tests |
