# Code Indexing Value Analysis

**Initiative:** Indexing Value Analysis
**Date:** 2026-01-12
**Question:** Does full codebase indexing provide real value, or should Cortex focus on semantic memory (notes, insights, decisions)?

## Executive Summary

**Key Finding:** Full codebase indexing provides marginal value over Claude Code's native tools (Glob/Grep/Read), while notes and insights provide **irreplaceable value** that native tools cannot replicate.

**Recommendation:** Consider a **"Skeleton + Semantic Memory"** architecture that prioritizes:
1. Notes, insights, and commits (high semantic value, irreplaceable)
2. File skeleton/structure (navigation context)
3. Optional/selective code indexing (for concept search when needed)

The current full-indexing approach treats code chunks the same as notes during retrieval, missing the fundamental insight that **code can be grepped, but understanding cannot**.

---

## 1. Current Architecture

### What Gets Indexed

Cortex stores **five document types**:

| Type | Generation | Purpose | Value Level |
|------|------------|---------|-------------|
| **code** | Automatic | Raw code chunks (~1500 chars) | Low semantic value |
| **note** | Manual | Decisions, learnings, domain knowledge | Medium-High |
| **insight** | Manual | Understanding anchored to specific files | Highest |
| **commit** | Manual | Session summaries, work context | Medium |
| **initiative** | Manual | Multi-session work tracking | Organizational |

### Chunking Strategy

- **Approach**: Hybrid AST-aware + text fallback
- **Chunk size**: 1,500 characters with 200-char overlap
- **Languages**: 18+ languages with syntax-aware splitting (Python, JS, Go, Rust, etc.)
- **Scope extraction**: Regex-based (not full AST) - extracts function/class names
- **Metadata**: file_path, repository, branch, chunk_index, language, scope

**Limitation**: Scope extraction uses regex patterns, not true AST parsing. This can miss:
- Multiline function definitions
- Nested classes/functions
- Complex generic syntax
- Decorators and annotations

### Search/Retrieval Mechanism

```
Query → Hybrid Search (Vector + BM25) → RRF Fusion → Reranking → Recency Boost → Results
```

**Pipeline details:**
1. **Hybrid search**: Retrieves 50 candidates using vector similarity + BM25 keyword matching
2. **RRF fusion**: `score = 1/(60+rank_vector) + 1/(60+rank_bm25)`
3. **Reranking**: Cross-encoder (FlashRank) reduces to top 5
4. **Recency boost**: Applied to notes/commits only (code gets no time decay)
5. **Score filtering**: Results below 0.5 threshold removed

**Critical observation**: Code and notes are treated identically through the search pipeline. No differentiation in scoring despite fundamentally different value propositions.

---

## 2. The Core Tension

Claude Code already has powerful, precise tools:
- **Glob**: Find files by pattern - exhaustive, zero false negatives
- **Grep**: Search content with regex - exact matches, guaranteed completeness
- **Read**: Read specific files - precise, always current

**The question**: When does semantic/RAG search over code chunks provide value that these tools don't?

### Decision Heuristic

```
Do you know the exact text you're looking for?
├── YES → Use Grep (faster, exhaustive, guaranteed)
└── NO → Does your query describe a *concept* or *behavior*?
    ├── YES → RAG might help (semantic understanding)
    └── NO → Use Glob (file patterns) or Read (known files)
```

---

## 3. Analysis: Code Chunks vs Notes/Insights

### Code Chunk Retrieval

**When RAG code search adds value:**
- **Vocabulary mismatch**: Find `throttle` when searching "rate limiting"
- **Concept queries**: "How does caching work?" surfaces relevant chunks
- **Pattern discovery**: "Show me similar validation code"
- **Exploration**: Onboarding to unfamiliar codebase

**When RAG code search adds noise or is inferior:**
- **Exact symbol lookup**: `getUserById` - Grep is perfect
- **File finding**: `**/*config*.json` - Glob is exhaustive
- **Regex patterns**: `TODO.*JIRA-[0-9]+` - RAG can't do this
- **Exhaustive enumeration**: "ALL imports of stripe" - Grep guarantees completeness
- **Fresh code**: Recently written code needs re-indexing; Grep is always current

**Estimated value distribution**: RAG code search helps in ~20-30% of queries (conceptual ones). For the other 70-80%, Grep/Glob are faster and more reliable.

### Notes/Insights Retrieval

**Irreplaceable value - captures what code cannot express:**

1. **Architectural decisions**: "We chose PostgreSQL over MongoDB because..."
2. **Historical context**: "This workaround exists because of Safari bug..."
3. **Gotchas/tribal knowledge**: "Deploy script fails on Mondays due to backup job"
4. **Future work**: "The N+1 query in OrderService needs batching"
5. **Cross-session context**: "Last session I was stuck on webhook verification"

**Key insight**: Notes and insights persist **understanding**. Code captures *what*; notes capture *why*.

### Comparative Value

| Aspect | Code Chunks | Notes | Insights |
|--------|------------|-------|----------|
| Generation | Automatic | Manual | Manual |
| Semantic density | Low | High | Very high |
| Grep-ability | 100% - code can always be grepped | 0% - reasoning never in code | 0% |
| Staleness risk | Auto-updated | Time-based decay | File-hash tracked |
| Search value | Marginal over Grep | Unique | Unique + validated |

---

## 4. What Cortex Captures Beyond Raw Code

### Metadata Captured

**Code chunks:**
```python
{
    "file_path", "repository", "branch", "chunk_index",
    "total_chunks", "language", "type": "code", "indexed_at",
    "function_name", "class_name", "scope"  # Optional, regex-extracted
}
```

**Notes:**
```python
{
    "type": "note", "title", "tags", "repository", "branch",
    "created_at", "verified_at", "status", "created_commit",
    "initiative_id", "initiative_name"
}
```

**Insights (richest):**
```python
{
    "type": "insight", "title", "files",  # LINKED FILES
    "tags", "repository", "branch", "created_at", "verified_at",
    "status", "created_commit", "file_hashes",  # STALENESS DETECTION
    "initiative_id", "last_validation_result", "validation_notes",
    "deprecated_at", "deprecation_reason", "superseded_by"
}
```

### The "Remember but Verify" System

Insights have sophisticated staleness detection:
- **File hash tracking**: Stores MD5 of linked files at creation
- **Triggers**: Verification required when linked files modified/deleted
- **Validation**: Can mark as still_valid, partially_valid, no_longer_valid
- **Lifecycle**: Can deprecate with reason, link to replacement insight

This is a **unique capability** - code can't tell you if your understanding is stale, but insights can.

---

## 5. Scenarios Analysis

### When RAG Code Search Helps

| Scenario | Example Query | Why RAG Wins |
|----------|--------------|--------------|
| Vocabulary mismatch | "rate limiting" | Finds `throttle`, `backoff`, `FloodGuard` |
| Concept exploration | "How does auth work?" | Returns contextual chunks, not line matches |
| Pattern finding | "Similar to this validation" | Embeddings capture structure |
| Onboarding | "Main components?" | Surfaces architecture |

### When RAG Code Search Adds Noise

| Scenario | Example Query | Why Native Tools Win |
|----------|--------------|---------------------|
| Symbol lookup | `getUserById` | Grep: exact, exhaustive |
| File patterns | `**/config/*.json` | Glob: precise, complete |
| Regex matching | `TODO.*JIRA-[0-9]+` | RAG can't do regex |
| Enumeration | "All stripe imports" | Grep guarantees completeness |
| Fresh code | Just wrote it | Grep is always current |

### The Quantitative Reality

- **~70-80% of queries**: Lexically searchable - Grep/Glob sufficient
- **~20-30% of queries**: Conceptual - RAG code search adds value
- **~100% of "why" questions**: Only notes/insights can answer

---

## 6. Alternative Architectures to Consider

### Option A: Full Indexing (Current)

**What**: Index all code chunks + notes + insights + commits

**Pros:**
- Comprehensive coverage
- Concept search available for all code
- Simple mental model ("everything is indexed")

**Cons:**
- High storage/compute cost (100s-1000s of chunks per repo)
- Code chunks add noise to results
- Marginal value over Grep for ~70% of queries
- No differentiation in retrieval scoring

### Option B: Skeleton + Semantic Memory Only

**What**: Index only file structure + notes + insights + commits. No code chunks.

**Pros:**
- Dramatic reduction in index size (10-100x smaller)
- Every indexed item is high semantic value
- Faster search (smaller search space)
- Focus on irreplaceable value (understanding)
- Users use Grep/Glob for code search (better anyway)

**Cons:**
- Lose concept-based code discovery
- Can't find code by semantic description
- Requires mindset shift

### Option C: Hybrid/Smart Indexing (Recommended)

**What**: Index notes/insights/commits + skeleton + selective code (APIs, interfaces, entry points)

**Tiers:**
1. **Always index**: Notes, insights, commits, initiatives
2. **Always index**: File skeleton (structure, not content)
3. **Selectively index**:
   - Entry points (main files, index files)
   - Public APIs and interfaces
   - Configuration files
   - README/documentation
4. **Skip**: Implementation details, test files, vendored code

**Pros:**
- Preserves concept search for important code
- Dramatically smaller index
- High signal-to-noise ratio
- Balances coverage with focus

**Cons:**
- More complex to configure
- Requires defining "important" (heuristics or config)

---

## 7. Findings & Recommendations

### Key Findings

1. **Code indexing provides marginal value over native tools**
   - Grep/Glob handle 70-80% of code search needs better
   - RAG adds value only for conceptual queries

2. **Notes and insights are irreplaceable**
   - Capture understanding that cannot be grepped
   - No native tool equivalent exists
   - This is Cortex's unique value proposition

3. **Current architecture doesn't differentiate**
   - Code chunks and notes scored identically
   - High-value items compete with low-value noise
   - Missed opportunity for semantic prioritization

4. **Staleness detection is underutilized for code**
   - Insights have sophisticated file-hash tracking
   - Code chunks have no staleness concept
   - Could detect when indexed code is outdated

### Recommendations

#### Short-term (Improve Current System)

1. **Boost notes/insights in scoring**
   - Add type-based score multiplier (e.g., insights 2x, notes 1.5x, code 1x)
   - Surface understanding before implementation

2. **Add "notes-only" search mode**
   - `search_cortex(query, types=["note", "insight"])`
   - Skip code entirely when asking "why" questions

3. **Reduce default code retrieval**
   - Lower `top_k_rerank` for code chunks
   - Or add `max_code_results` parameter

#### Medium-term (Architecture Evolution)

4. **Implement selective code indexing**
   - Index entry points, APIs, configs by default
   - Skip implementation details unless requested
   - Use `.cortexinclude` for important paths

5. **Add semantic density scoring**
   - Notes inherently more dense than code
   - Factor this into retrieval ranking

#### Long-term (Strategic Direction)

6. **Consider "Skeleton + Memory" as primary mode**
   - Make full code indexing opt-in
   - Default to notes/insights + structure
   - Position Cortex as "memory layer" not "code search"

7. **Invest in insight generation**
   - Prompt Claude to generate insights from sessions
   - Auto-capture architectural observations
   - Build the understanding layer, not the code index

#### Exploration: Filling Grep's Gaps (See Section 8)

8. **Dependency Graph** (High priority exploration)
   - Parse imports during ingest to build file→file relationships
   - Enable "what depends on X?" and impact analysis queries
   - Complements insights with computed structural knowledge

9. **Entry Point Detection** (High priority exploration)
   - Auto-detect main/index files during ingest
   - Prompt for feature entry points ("Where does auth start?")
   - Reduce onboarding and navigation friction

10. **Importance Scoring** (Medium priority exploration)
    - Analyze git change frequency and import centrality
    - Use to rank search results (important files first)
    - Surface high-impact code automatically

11. **Convention Capture** (Medium priority exploration)
    - Prompt after task completion: "Save the pattern you used"
    - Build institutional knowledge over time
    - Enable "how should I do X?" queries

### The Strategic Question

**What is Cortex for?**

- **Option A**: A code search engine (competing with Grep, losing)
- **Option B**: A memory/understanding layer (unique, irreplaceable)

The analysis strongly suggests **Option B** is the winning strategy. Code search is table stakes that native tools already solve. Memory and understanding persistence is the unique value.

---

## 8. Gaps in Grep: Opportunities Beyond Code Indexing

The previous analysis established that RAG over code chunks provides marginal value over Grep. But this raises a deeper question: **What gaps does Grep have that Cortex could fill with high-value indexed data?**

Insights already fill one gap (understanding). Are there others?

### Grep's Fundamental Limitation

Grep finds **where text appears**, not **what it means**.

| Question | Can Grep Answer? | Why Not? |
|----------|------------------|----------|
| "Where is `getUserById` defined?" | **Yes** | Exact text match |
| "What does the auth module *do*?" | **No** | Requires understanding |
| "What *calls* getUserById?" | **Poorly** | Can grep, but noisy/incomplete |
| "If I change X, what breaks?" | **No** | Requires relationship analysis |
| "Where should I *start* reading for feature Y?" | **No** | Requires navigation knowledge |
| "What's the *pattern* for adding endpoints?" | **No** | Requires convention knowledge |
| "What are the most important files?" | **No** | Requires prioritization |

### The Gap Categories

Beyond insights (manual understanding), there are other non-greppable things:

#### 1. Relationships / Dependency Graph

**Question grep can't answer:** "What files depend on this one?" / "If I change X, what breaks?"

- You CAN grep for imports, but:
  - Different languages have different import syntax
  - Re-exports obscure relationships
  - Runtime dependencies don't appear in imports
  - Results are noisy and require manual assembly

**Potential value:** Index `file A → imports → file B` relationships as structured data. Enable "impact analysis" queries.

**Generation:** Computed (parse imports during ingest)

#### 2. Entry Points / Navigation Map

**Question grep can't answer:** "Where do I start reading to understand feature X?"

- This IS insight-shaped, but a specific high-value pattern:
  - "Auth flow starts at `src/auth/middleware.ts`"
  - "To add a new API endpoint, look at `src/routes/` first"
  - "The payment integration entry point is `src/billing/stripe.ts`"

**Potential value:** Systematically capture "reading order" for features. Reduce onboarding time.

**Generation:** Manual (prompted insights) or computed (detect main/index files)

#### 3. Auto-Generated Summaries

**Question grep can't answer:** "What does `OrderService` do in one sentence?"

- Docstrings exist but are often missing/stale
- Reading a 500-line file to understand its purpose is expensive
- Summaries could answer "what is this?" without reading code

**Potential value:** Generate on ingest, surface in search results. Provide instant orientation.

**Generation:** Computed (LLM-generated during ingest)

#### 4. Conventions / Patterns

**Question grep can't answer:** "What's the established way to do X here?"

- This IS insight-shaped, but a distinct category worth prompting for:
  - "All API errors go through `handleError()` in `utils/errors.ts`"
  - "Database queries use the repository pattern in `src/repos/`"
  - "New features get a folder in `src/features/` with index.ts entry point"

**Potential value:** Capture institutional knowledge. Enable consistency.

**Generation:** Manual (prompted after completing tasks)

#### 5. Importance / Hotspots

**Question grep can't answer:** "What are the most important files?" / "What's actively developed?"

- Could derive from:
  - Git change frequency (files changed often = important)
  - Import count (files imported by many = important)
  - File size / complexity
  - Explicit marking

**Potential value:** Rank search results by importance, not just relevance. Surface high-impact files.

**Generation:** Computed (git log analysis, import graph)

### Gap Classification

| Gap | Grep Limitation | Current Coverage | Generation | Value |
|-----|-----------------|------------------|------------|-------|
| **Understanding** | Can't search for meaning | Insights ✓ | Manual | **High** |
| **Relationships** | Noisy/incomplete | Not captured | Computed | **High** |
| **Navigation** | Can't know reading order | Insights (ad-hoc) | Manual/Computed | **Medium-High** |
| **Summaries** | Can't generate descriptions | Not captured | Computed | **Medium** |
| **Conventions** | Can't know patterns | Insights (ad-hoc) | Manual | **Medium** |
| **Importance** | No prioritization | Not captured | Computed | **Medium** |

### Key Distinction: Manual vs Computed

**Insights are manual understanding** - things you figured out and want to remember.

**Some gaps could be filled with computed/derived data:**
- Relationships: Parse imports automatically
- Summaries: LLM-generate on ingest
- Importance: Analyze git history

**The opportunity:** Combine manual semantic memory (insights) with computed structural knowledge (relationships, summaries, importance) to create a richer understanding layer that Grep fundamentally cannot provide.

### Highest-Value Opportunities

Based on this analysis, the gaps worth exploring (in priority order):

1. **Dependency Graph** (High value, computed)
   - Parse imports during ingest
   - Enable "what depends on X?" queries
   - Support impact analysis for changes

2. **Entry Point Detection** (High value, computed + manual)
   - Auto-detect main/index files
   - Prompt for feature entry points
   - Reduce navigation friction

3. **Importance Scoring** (Medium-high value, computed)
   - Git change frequency analysis
   - Import count / centrality
   - Use for search result ranking

4. **Convention Prompts** (Medium value, manual)
   - After completing tasks, prompt: "Save the pattern you used"
   - Build institutional knowledge over time

5. **Auto-Summaries** (Medium value, computed)
   - Generate file/module descriptions on ingest
   - Expensive (LLM calls) but could be optional

---

## Appendix: Raw Analysis Data

### A. Chunking Strategy Details

- **Default chunk size**: 1,500 characters
- **Overlap**: 200 characters
- **Language detection**: File extension → shebang → fallback
- **Supported languages**: Python, JS/TS, Java, Go, Rust, Ruby, PHP, C/C++/C#, Swift, Kotlin, Scala, Markdown, HTML, Solidity, Lua, Haskell, Elixir
- **Scope extraction**: Regex-based patterns for function/class names
- **Delta sync**: Git-based (fastest), hash-based (fallback), full (forced)

### B. Search Pipeline Details

1. **Hybrid search**: Vector (ChromaDB) + BM25 (rank_bm25 library)
2. **Fusion**: RRF with k=60
3. **Reranking**: FlashRank cross-encoder (ms-marco-MiniLM-L-12-v2)
4. **Recency boost**: `boost = max(0.5, e^(-age_days / 30))` for notes/commits
5. **Initiative boost**: 1.3x multiplier for focused initiative items
6. **Filtering**: Score >= 0.5, branch filtering for code, cross-branch for notes

### C. Document Type Comparison

| Feature | Code | Note | Insight | Commit |
|---------|------|------|---------|--------|
| Auto-generated | Yes | No | No | No |
| Linked files | No | No | **Yes** | Yes |
| File hash tracking | No | No | **Yes** | No |
| Staleness detection | No | Time-based | **File-based** | Time-based |
| Validation workflow | No | No | **Yes** | No |
| Initiative tagging | Implicit | Yes | Yes | Yes |
| Recency boost | No | Yes | Yes | Yes |
| Branch filtering | Yes | No | No | No |
