# Metadata-First Code Intelligence

> **Philosophy**: "Code can be grepped. Understanding cannot."

## The Problem with Code Chunking

Raw code chunking is the "Hello World" of RAG, and it rarely works for real engineering.

**What happens when you chunk raw code:**
- Fill your vector store with syntax noise (braces, imports, boilerplate)
- A search for "how do we handle auth" returns 50 files that import the auth library, but misses the one file that defines the strategy
- Agents get lost in implementation details instead of finding entry points

**The insight:** To make an agent "smart," stop storing *implementation* (which the agent can read if told where to look) and start storing *maps and metadata*.

---

## What to Store Instead

### 1. The Repo Map (File Metadata)

Instead of chunking file content, parse the code and store a summarized skeleton of every file.

**Store:**
- File path
- LLM-generated description (dense, search-optimized)
- Exports: class names, function signatures (inputs/outputs), constants
- Imports: what other modules this file depends on
- Classification: is_entry_point, is_barrel, is_test, is_config

**Why it works:** When the agent asks "Where is the user logic?", the vector search hits the description, not a random line of code. It gives the agent the precise file path so it can read the actual file if needed.

### 2. Data Contracts (Types & Schemas)

The "truth" of an application lives in its data shapes.

**Store:**
- TypeScript interfaces and types
- Database schemas (Mongoose, Prisma, TypeORM)
- API definitions (OpenAPI/Swagger)
- DTOs and validation schemas
- Pydantic models, dataclasses

**Why it works:** Agents struggle to hallucinate correct property names. By feeding it the `CreateUserDto` or `UserSchema`, you ensure it uses `user.emailAddress` instead of `user.email` without guessing.

### 3. Entry Points (Navigation)

Where features start - the doors into the codebase.

**Store:**
- Main/index files
- API routes and handlers
- CLI commands
- Event handlers
- Barrel files (re-export aggregators)

**Why it works:** Agents need to know where to start. "Add a user endpoint" → find the routes file → read it → add the endpoint.

### 4. Dependency Graph (Relationships)

File-to-file import relationships for impact analysis.

**Store:**
- Forward dependencies: what does this file import?
- Reverse dependencies: what files import this one?
- Hub detection: files with many dependents (high impact)

**Why it works:** "What depends on auth.py?" becomes a direct lookup, not a grep across the entire codebase.

### 5. Semantic Memory (Understanding)

This is Cortex's existing strength - keep it.

**Already have:**
- **Insights**: Understanding anchored to specific files
- **Notes**: Decisions, learnings, domain knowledge
- **Commits**: Session summaries with context
- **Initiatives**: Multi-session work tracking

**Why it's irreplaceable:** This is what grep fundamentally cannot find.

---

## The Description is Critical

**Risk:** If the file description is weak (e.g., "User controller file"), your RAG fails. A search for "how do we encrypt passwords?" will never match "User controller file."

**Solution:** Mandatory LLM generation with a specific prompt:

```
Analyze this {language} code from {file_path}.

Write a dense, search-optimized summary (2-3 sentences) that includes:
1. The main responsibility (e.g., "Handles user authentication")
2. Key algorithms or patterns used (e.g., "Implements sliding window rate limiting")
3. Specific technologies/libraries (e.g., "Uses Stripe API for billing")
4. Any validation constraints if present (e.g., "Validates email format")

Be specific. "User controller" is bad.
"REST endpoints for user CRUD with JWT auth and Stripe billing integration" is good.
```

---

## Barrel File Problem

In TypeScript/Python, "Entry Points" are often obscured by "Barrel Files" - files that just `export * from './child'`.

**Risk:** The agent looks for `user.service.ts` but your dependency graph points to `index.ts`. The agent gets stuck at the door.

**Solution:** Detect and tag barrel files:
- If a file is purely re-exports, tag it as `is_barrel: true`
- This allows the agent to "step through" the barrel file to the real implementation

**Detection patterns:**
- TypeScript: `export * from`, `export { x } from`
- Python: `from .module import *`, `__all__ = [...]`

---

## Two-Step Lookup Pattern

Don't try to stuff the answer into the RAG response. Use RAG to find the *pointer*.

**Example:**
1. User query: "Add a new field to the user profile"
2. Agent RAG lookup: Finds `user.schema.ts` (data contract) and `user.controller.ts` (file metadata)
3. Agent action: Now knows exactly which files to open and read

The RAG tells the agent WHERE to look. The agent reads the actual code.

---

## What NOT to Store

| Don't Store (Low Value) | Do Store (High Value) |
|------------------------|----------------------|
| Full function bodies | Function signatures & descriptions |
| Import statements | Dependency graph (who calls whom) |
| node_modules content | Version numbers & key library names |
| Getter/setter boilerplate | Business logic summaries |
| Raw code chunks | LLM-generated file descriptions |

---

## Search Presets

Different queries need different document types:

```python
SEARCH_PRESETS = {
    # "Why did we do X?" - understanding queries
    "understanding": ["insight", "note", "commit"],

    # "Where is X?" - navigation queries
    "navigation": ["file_metadata", "entry_point", "data_contract"],

    # "What's the structure?" - architecture queries
    "structure": ["file_metadata", "dependency"],

    # "Where is this error coming from?" - debugging
    "trace": ["entry_point", "dependency", "data_contract"],
}
```

---

## Type Scoring

Boost understanding over implementation:

```python
TYPE_MULTIPLIERS = {
    # Understanding (irreplaceable - grep can't find this)
    "insight": 2.0,
    "note": 1.5,
    "commit": 1.5,

    # Navigation (high value - tells agent where to look)
    "entry_point": 1.4,
    "file_metadata": 1.3,
    "data_contract": 1.3,
    "dependency": 1.0,

    # Context
    "tech_stack": 1.2,
    "skeleton": 1.0,
    "initiative": 1.0,
}
```

---

## Implementation Strategy

### Phase 1: AST Extraction
- Add tree-sitter for Python, TypeScript, Kotlin
- Extract imports, exports, classes, functions
- Detect entry points and barrel files

### Phase 2: LLM Descriptions
- Generate dense descriptions during ingestion
- Batch files for efficiency
- Cache to avoid re-generation on delta sync

### Phase 3: New Document Types
- `file_metadata`: Rich per-file info
- `data_contract`: Interfaces, types, schemas
- `entry_point`: Main files, routes, CLI handlers
- `dependency`: Import relationships

### Phase 4: Clean Break
- Delete all `code` chunks from ChromaDB
- Remove chunking code
- Update search to use new types

---

## Future Enhancements

**v2 candidates:**
- Validation rules extraction (Zod, Joi, Pydantic constraints)
- Pattern detection (Repository, Singleton, Middleware)
- Additional languages (Go, Rust, Java, C#)
- Transitive dependency analysis

---

## References

- Original analysis: `analysis/code-indexing-analysis.md`
- Implementation plan: `~/.claude/plans/ancient-hugging-moore.md`
- Core philosophy from ROADMAP.md: "Code can be grepped. Understanding cannot."
