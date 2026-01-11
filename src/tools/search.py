"""
Search Tool

MCP tool for searching Cortex memory.
"""

import json
import time
from typing import Optional

from logging_config import get_logger
from src.git import get_current_branch
from src.search import apply_recency_boost
from src.tools.services import CONFIG, get_collection, get_reranker, get_repo_path, get_searcher

logger = get_logger("tools.search")


def build_branch_aware_filter(
    project: Optional[str] = None,
    branches: Optional[list[str]] = None,
) -> Optional[dict]:
    """
    Build ChromaDB where filter that applies branch filtering
    only to code and skeleton documents.

    Notes, commits, tech_stack, initiatives are never filtered by branch.

    Args:
        project: Optional project filter
        branches: List of branches to include for code/skeleton

    Returns:
        ChromaDB where filter dict, or None if no filtering needed
    """
    if not branches or branches == ["unknown"]:
        # No branch filtering if unknown
        return {"project": project} if project else None

    # Types filtered by branch: code, skeleton
    # Types NOT filtered: note, commit, tech_stack, initiative
    branch_filter = {
        "$or": [
            # Code/skeleton: filter by branch
            {"$and": [
                {"type": {"$in": ["code", "skeleton"]}},
                {"branch": {"$in": branches}}
            ]},
            # Non-code types: always include (cross-branch)
            {"type": {"$in": ["note", "commit", "tech_stack", "initiative"]}}
        ]
    }

    if project:
        return {"$and": [{"project": project}, branch_filter]}

    return branch_filter


def search_cortex(
    query: str,
    project: Optional[str] = None,
    min_score: Optional[float] = None,
    branch: Optional[str] = None,
) -> str:
    """
    Search the Cortex memory for relevant code, documentation, or notes.

    Args:
        query: Natural language search query
        project: Optional project filter
        min_score: Minimum relevance score threshold (0-1, overrides config)
        branch: Optional branch filter. Defaults to auto-detect from cwd.
                Code/skeleton are filtered by branch; notes/commits are not.

    Returns:
        JSON with search results including content, file paths, and scores
    """
    if not CONFIG["enabled"]:
        logger.info("Search rejected: Cortex is disabled")
        return json.dumps({"error": "Cortex is disabled", "results": []})

    logger.info(f"Search query: '{query}' (project={project}, branch={branch})")
    start_time = time.time()

    try:
        collection = get_collection()
        searcher = get_searcher()
        reranker = get_reranker()

        # Determine branch context
        repo_path = get_repo_path()
        current_branch = get_current_branch(repo_path) if repo_path else "unknown"

        # Use explicit branch if provided, otherwise auto-detect
        effective_branch = branch if branch else current_branch

        # Build branch list: current + main (unless already on main/master)
        branches = [effective_branch]
        if effective_branch not in ("main", "master", "unknown"):
            branches.append("main")

        # Build smart where filter (code filters by branch, notes don't)
        where_filter = build_branch_aware_filter(
            project=project,
            branches=branches,
        )
        logger.debug(f"Branch filter: effective={effective_branch}, branches={branches}")

        # Hybrid search
        search_start = time.time()
        candidates = searcher.search(
            query=query,
            top_k=CONFIG["top_k_retrieve"],
            where_filter=where_filter,
            rebuild_index=True,
        )
        search_time = time.time() - search_start
        logger.debug(f"Hybrid search: {len(candidates)} candidates in {search_time*1000:.1f}ms")

        if not candidates:
            logger.info("Search: no candidates found")
            return json.dumps({
                "query": query,
                "results": [],
                "message": "No results found. Try ingesting code first with ingest_code_into_cortex.",
            })

        # Rerank with FlashRank
        rerank_start = time.time()
        reranked = reranker.rerank(
            query=query,
            documents=candidates,
            top_k=CONFIG["top_k_rerank"],
        )
        rerank_time = time.time() - rerank_start
        logger.debug(f"Reranking: {len(reranked)} results in {rerank_time*1000:.1f}ms")

        # Apply recency boost to notes/commits (not code)
        if CONFIG["recency_boost"]:
            reranked = apply_recency_boost(
                reranked,
                half_life_days=CONFIG["recency_half_life_days"],
            )
            logger.debug(f"Recency boost applied (half_life={CONFIG['recency_half_life_days']}d)")

        # Apply minimum score filter (use boosted_score if available)
        threshold = min_score if min_score is not None else CONFIG["min_score"]
        score_key = "boosted_score" if CONFIG["recency_boost"] else "rerank_score"
        filtered = [r for r in reranked if r.get(score_key, r.get("rerank_score", 0)) >= threshold]
        logger.debug(f"Score filter (>={threshold}): {len(filtered)} results")

        # Log top results
        for i, r in enumerate(filtered[:5]):
            meta = r.get("meta", {})
            logger.debug(f"  [{i}] score={r.get('rerank_score', 0):.3f} file={meta.get('file_path', 'unknown')}")

        # Format response
        results = []
        for r in filtered:
            meta = r.get("meta", {})
            final_score = r.get("boosted_score", r.get("rerank_score", 0))
            result = {
                "content": r.get("text", "")[:2000],
                "file_path": meta.get("file_path", "unknown"),
                "project": meta.get("project", "unknown"),
                "branch": meta.get("branch", "unknown"),
                "language": meta.get("language", "unknown"),
                "score": float(round(final_score, 4)),
            }
            if CONFIG["verbose"] and "recency_boost" in r:
                result["recency_boost"] = r["recency_boost"]
            results.append(result)

        # Fetch skeleton if we have results with a project
        skeleton_data = None
        detected_project = project
        if not detected_project and results:
            detected_project = results[0].get("project")

        if detected_project and detected_project != "unknown":
            try:
                # Try to get skeleton for current branch first
                skeleton_results = collection.get(
                    where={"$and": [
                        {"type": "skeleton"},
                        {"project": detected_project},
                        {"branch": {"$in": branches}},
                    ]},
                    include=["documents", "metadatas"],
                )
                # Fallback to any skeleton for this project if branch-specific not found
                if not skeleton_results["documents"]:
                    skeleton_results = collection.get(
                        where={"$and": [{"type": "skeleton"}, {"project": detected_project}]},
                        include=["documents", "metadatas"],
                    )
                if skeleton_results["documents"]:
                    skel_meta = skeleton_results["metadatas"][0]
                    skeleton_data = {
                        "project": detected_project,
                        "branch": skel_meta.get("branch", "unknown"),
                        "total_files": skel_meta.get("total_files", 0),
                        "total_dirs": skel_meta.get("total_dirs", 0),
                        "tree": skeleton_results["documents"][0],
                    }
                    logger.debug(f"Skeleton included: {skel_meta.get('total_files', 0)} files (branch={skel_meta.get('branch')})")
            except Exception as e:
                logger.debug(f"Skeleton fetch failed: {e}")

        # Fetch repository context (tech_stack + initiative)
        context_data = None
        if detected_project and detected_project != "unknown":
            try:
                tech_stack_id = f"{detected_project}:tech_stack"
                initiative_id = f"{detected_project}:initiative"
                context_results = collection.get(
                    ids=[tech_stack_id, initiative_id],
                    include=["documents", "metadatas"],
                )
                if context_results["documents"]:
                    context_data = {"repository": detected_project}
                    for i, doc_id in enumerate(context_results.get("ids", [])):
                        if i < len(context_results.get("documents", [])):
                            doc = context_results["documents"][i]
                            meta = context_results["metadatas"][i] if context_results.get("metadatas") else {}
                            if doc_id == tech_stack_id:
                                context_data["tech_stack"] = {
                                    "content": doc,
                                    "updated_at": meta.get("updated_at", "unknown"),
                                }
                            elif doc_id == initiative_id:
                                context_data["initiative"] = {
                                    "name": meta.get("initiative_name", ""),
                                    "status": meta.get("initiative_status", ""),
                                    "updated_at": meta.get("updated_at", "unknown"),
                                }
                    if not context_data.get("tech_stack") and not context_data.get("initiative"):
                        context_data = None
                    else:
                        logger.debug(f"Context included: tech_stack={bool(context_data.get('tech_stack'))}, initiative={bool(context_data.get('initiative'))}")
            except Exception as e:
                logger.debug(f"Context fetch failed: {e}")

        response = {
            "query": query,
            "results": results,
            "total_candidates": len(candidates),
            "returned": len(results),
        }

        if skeleton_data:
            response["project_skeleton"] = skeleton_data

        if context_data:
            response["project_context"] = context_data

        if CONFIG["verbose"]:
            response["config"] = CONFIG
            response["branch_context"] = current_branch

        total_time = time.time() - start_time
        logger.info(f"Search complete: {len(results)} results in {total_time*1000:.1f}ms")

        return json.dumps(response, indent=2)

    except Exception as e:
        logger.error(f"Search error: {e}")
        return json.dumps({"error": str(e), "results": []})
