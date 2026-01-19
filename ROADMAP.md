# Cortex Roadmap

**Memory for AI Agents.** A local, privacy-first system that gives AI coding assistants persistent understanding across sessions.

## The Core Insight

> **Code can be grepped. Understanding cannot.**

AI agents already have powerful tools for searching code (Glob, Grep, Read). What they lack is **memory** - the ability to recall decisions, understand context, and learn from past work.

Cortex fills this gap by storing:
- **What was decided** and why (insights, notes)
- **What was done** in past sessions (commits, initiatives)
- **What matters** in this codebase (entry points, patterns, importance)

---

## Core Principles

1. **Understanding over Code**: Store *decisions and insights*, not just code chunks
2. **Zero Friction**: Memory that requires manual discipline won't be used reliably
3. **Proactive Surfacing**: Load relevant context *before* it's needed
4. **Grep's Gaps**: Focus on what search tools fundamentally can't do

---

## Current State (Jan 2026)

| Capability | Status | Notes |
|------------|--------|-------|
| **Semantic Memory** | ✅ Strong | Insights, notes, session summaries capture understanding |
| **Initiative Tracking** | ✅ Strong | Multi-session work with summaries |
| **Session Recall** | ✅ Good | "What did I work on?" queries |
| **Staleness Detection** | ✅ Good | Insights validated against file changes |
| **Installation & Updates** | ✅ Good | `cortex update`, `cortex doctor`, migrations |
| **Auto-Capture** | ✅ Good | Session hooks, LLM summarization, async queue |
| **Metadata-First Indexing** | ✅ Good | file_metadata, data_contract, entry_point, dependency documents |
| **Structural Knowledge** | ✅ Good | Dependency graph, entry points, data contracts extracted via AST |

*See `analysis/metadata-first-architecture.md` for design rationale.*

---

## Phase 1: Foundation ✅

*Core infrastructure complete.*

- Dockerized deployment with ChromaDB
- Hybrid search (Vector + BM25 + FlashRank reranking)
- Metadata-first indexing (file_metadata, data_contract, entry_point, dependency)
- AST parsing via tree-sitter (Python, TypeScript, Kotlin)
- MCP server integration
- Core tools: `search_cortex`, `ingest_code_into_cortex`, `save_note_to_cortex`

---

## Phase 2: Semantic Memory ✅

*The irreplaceable value layer - complete.*

| Feature | Status | Description |
|---------|--------|-------------|
| Insights | ✅ | Understanding anchored to specific files with staleness detection |
| Notes | ✅ | Decisions, learnings, domain knowledge |
| Session Summaries | ✅ | Auto-captured session context with changed files |
| Initiatives | ✅ | Multi-session work tracking with focus system |
| Recall | ✅ | "What did I work on this week?" timeline view |
| Summarize | ✅ | Narrative summary of initiative progress |
| Staleness | ✅ | "Remember but Verify" - detect when insights may be outdated |

---

## Phase 3: Zero-Friction & Developer Experience ✅

*Complete. Cortex is effortless to install, use, and explore.*

### Memory Browser ✅

*Complete - Web UI for exploring memory.*

| Feature | Status | Description |
|---------|--------|-------------|
| **Web UI** | ✅ | Browser-based memory explorer at `http://localhost:8080` |
| **Stats Dashboard** | ✅ | Counts by type, storage stats |
| **Search Preview** | ✅ | Interactive search with result preview |
| **Edit/Delete** | ✅ | Modify or remove stored memories |

### Installation & Updates ✅

*Zero-friction onboarding and maintenance - complete.*

| Feature | Status | Description |
|---------|--------|-------------|
| **Auto-Update Check** | ✅ | `orient_session` returns `update_available: true` when local code differs from daemon |
| **`cortex update`** | ✅ | Single command backs up, pulls, rebuilds, migrates, and restarts |
| **Health Check** | ✅ | `cortex doctor` (essential) and `cortex doctor --verbose` (comprehensive) |
| **Migration System** | ✅ | Schema versioning with auto-migrations on startup, auto-backup before migrate |

### Auto-Capture ✅

*Eliminate manual discipline requirements - complete.*

| Feature | Status | Description |
|---------|--------|-------------|
| **Session Lifecycle Hooks** | ✅ | Claude Code `SessionEnd` hook auto-captures summaries |
| **Transcript Parsing** | ✅ | JSONL parser extracts messages, tool calls, file edits |
| **Significance Detection** | ✅ | Configurable thresholds (tokens, file edits, tool calls) |
| **LLM Summarization** | ✅ | Multi-provider support (Claude CLI, Anthropic, Ollama, OpenRouter) |
| **Async Queue Processing** | ✅ | Non-blocking hook (<100ms), daemon processes in background |
| **Hook Management CLI** | ✅ | `cortex hooks install/status/repair/uninstall` |
| **MCP Tools** | ✅ | `get_autocapture_status`, `configure_autocapture` |

#### Future Enhancements (Lower Priority)

| Feature | Description | Value |
|---------|-------------|-------|
| **Git Commit Watcher** | Background process watches for git commits, auto-indexes changed files + commit messages. | Memory stays fresh automatically |
| **Log Eater** | Ingest `~/.claude/sessions` logs with LLM summarization. Backfill memory retroactively. | Memory from past sessions without workflow change |

### Lower Priority

| Feature | Description | Value |
|---------|-------------|-------|
| **One-Line Installer** | `curl -fsSL https://get.cortex.dev \| bash` - Downloads, configures Claude Code MCP settings, pulls Docker image. | Zero-friction onboarding |
| **Homebrew Formula** | `brew install cortex-memory` - Native package for macOS users. | Platform-native experience |
| **Version Pinning** | Allow users to pin to specific version in config. | Stability for production use |
| **Linux/Windows Packages** | apt/dnf packages, WSL2 support | Broader platform support |

---

## Phase 4: Smarter Search ✅

*Understanding surfaces first, not code noise.*

| Feature | Status | Description |
|---------|--------|-------------|
| **Type-Based Scoring** | ✅ | Boost insights (2x), notes (1.5x), session_summaries (1.5x). `src/search/type_scoring.py` |
| **Document Type Filter** | ✅ | `types` parameter filters by document type with branch-aware filtering |
| **Conditional Index Rebuild** | ✅ | BM25 index cached, thread-safe with `RLock`, ~3s faster when warm |
| **Metadata-First Mode** | ✅ | No raw code chunks - only structured metadata (file_metadata, etc.) |
| **Entry Point Detection** | ✅ | Auto-extracted during ingest (HTTP routes, CLI commands, main functions) |

### Future Enhancements

| Feature | Description | Value |
|---------|-------------|-------|
| **Importance Scoring** | Analyze git frequency + import centrality | High-impact files surface first |

---

## Code Quality Initiative ✅

*Completed Jan 2026. Addressed technical debt from codebase analysis.*

### Critical Fixes ✅

| Issue | Solution | Status |
|-------|----------|--------|
| **Queue processor non-atomic writes** | Tempfile + rename pattern in `queue_processor.py` | ✅ Done |
| **Migration no rollback** | Backup before each migration, restore on failure | ✅ Done |

### Code Duplication Elimination ✅

| Duplication | Solution | Status |
|-------------|----------|--------|
| **Resource initialization** | `src/http/resources.py` with thread-safe ResourceManager | ✅ Done |
| **Subprocess patterns** | `src/git/subprocess_utils.py` | ✅ Done |
| **Initiative resolution** | `resolve_initiative()` in `src/tools/initiative_utils.py` | ✅ Done |
| **`_find_initiative`** | `find_initiative()` in `src/tools/initiative_utils.py` | ✅ Done |

### Function Complexity ✅

| Function | Solution | Status |
|----------|----------|--------|
| `search_cortex` | Extracted `SearchPipeline` dataclass | ✅ Done |
| `ingest_codebase` | Strategy pattern (`DeltaSyncStrategy`) | ✅ Done |
| `orient_session` | Extracted `RepositoryContext`, `StalenessDetector` | ✅ Done |
| `parse_transcript_jsonl` | Extracted `ContentBlockParser`, `TranscriptMetadataExtractor` | ✅ Done |

### Test Coverage Expansion ✅

| Module | Status | Details |
|--------|--------|---------|
| Auto-capture | ✅ Done | 62+ tests in `test_autocapture.py` |
| Performance | ✅ Done | 8 benchmarks in `test_benchmarks.py` (latency, throughput, large codebase) |
| E2E workflow | ✅ Done | 9 tests in `test_e2e.py` (orient→ingest→search→commit, initiatives) |

### Lower Priority Items ✅

| Item | Solution | Status |
|------|----------|--------|
| **Exception hierarchy** | `src/exceptions.py` with `CortexError` base + domain-specific exceptions | ✅ Done |
| **HTTP client standardization** | `src/http/http_client.py` replacing urllib in LLM providers | ✅ Done |
| **Configuration extraction** | `TIMEOUTS` dict in `src/config.py` with `get_timeout()` helper | ✅ Done |

---

## Phase 5: Structural Intelligence 🔄

*Fill the gaps that Grep fundamentally cannot address.*

### Codebase Understanding

| Feature | Status | Description |
|---------|--------|-------------|
| **Dependency Graph** | ✅ | Imports parsed during ingest, file→file relationships with impact_tier |
| **Entry Point Map** | ✅ | HTTP routes, CLI commands, main functions extracted as entry_point docs |
| **Data Contracts** | ✅ | Interfaces, types, schemas, dataclasses extracted as data_contract docs |
| **Cross-File Relationships** | ⬜ | Track which files are commonly edited together |
| **Architecture Detection** | ⬜ | Identify patterns: monorepo structure, layer boundaries |

### Datastore Management

| Feature | Status | Description |
|---------|--------|-------------|
| **Async Operations** | ✅ | Background processing for large ingests with progress tracking |
| **Datastore Analysis** | ✅ | Stats by type via browse API and web UI |
| **Cleanup Tools** | ⬜ | Remove orphaned chunks, stale entries |
| **Selective Purge** | ⬜ | Delete by repository, branch, type, date range |

---

## Phase 6: External Knowledge ⬜

*Capture knowledge from outside the codebase.*

| Feature | Description | Value |
|---------|-------------|-------|
| **Error Database** | Exact-match stack trace lookup. `log_error` / `solve_error` tools. | "I've seen this before" for errors |
| **Documentation Ingest** | Ingest external docs with source attribution. Search returns "from React docs:" context. | Library knowledge in memory |
| **Web Clipper** | Browser extension to save from Confluence, Stack Overflow, ChatGPT. | Capture research and decisions |
| **Constraints** | Negative rules ("DO NOT USE X") injected in preamble. | Prevent known mistakes |

---

## Phase 7: IDE Integration ⬜

*Surface Cortex insights while browsing code in any editor.*

| Feature | Description | Value |
|---------|-------------|-------|
| **File Context Query** | `get_context_for_file` MCP tool + HTTP endpoint | "What do we know about this file?" |
| **LSP Server** | Language Server Protocol server using pygls | Universal editor support |
| **Hover Provider** | Show linked insights on hover | Context at point of need |
| **Code Lens** | "N insights" indicator at file top | Visual awareness |
| **Stale Diagnostics** | Warning squiggles for outdated insights | Verification prompts |
| **VS Code Extension** | Packaged extension for VS Code users | Easy installation |
| **Editor Docs** | Setup guides for Neovim, Vim, Emacs, JetBrains | Universal access |

*See `analysis/file-context-lsp.md` for full design.*

---

## Phase 8: Scale & Teams ⬜

*Future: enterprise features.*

| Feature | Description |
|---------|-------------|
| **Cross-Initiative Search** | "What auth decisions have we made across all projects?" |
| **Pattern Library** | "You've solved rate limiting 3 times - here's what worked." |
| **Multi-User** | Team-shared memory with access control |
| **Memory Sync** | Sync across machines (personal cloud backup) |
| **Federated Routing** | Shard by domain for large codebases |

---

## Architecture

```
┌─────────────────┐     stdio      ┌──────────────────┐
│   Claude Code   │ ◄────────────► │   MCP Server     │
└─────────────────┘                └────────┬─────────┘
                                            │
        ┌───────────────────────────────────┼───────────────────────────────────┐
        │                                   │                                   │
┌───────▼───────┐                  ┌────────▼────────┐                 ┌────────▼────────┐
│    Search     │                  │    Ingestion    │                 │  Semantic Memory│
│ Vector + BM25 │                  │ Metadata-First  │                 │ Notes, Insights │
└───────┬───────┘                  │ + AST Parsing   │                 │ Session Summaries│
        │                          └────────┬────────┘                 └─────────────────┘
┌───────▼───────┐                           │
│   FlashRank   │                  ┌────────▼────────┐
│   Reranker    │                  │    ChromaDB     │
└───────────────┘                  │   (Embedded)    │
                                   └─────────────────┘
```

**Document Types:**
- **Navigation**: skeleton, file_metadata, dependency
- **Usage**: data_contract, entry_point, idiom
- **Memory**: note, insight, session_summary, initiative
- **Context**: tech_stack

---

## Legend

- ✅ Implemented
- 🔄 In progress / Next up
- ⬜ Not started

