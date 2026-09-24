"""
GraphRAG Tool — Geospatial Knowledge Graph retrieval.

Adds a single tool function `query_geospatial_knowledge` that the Vision Agent
(and any other agent registered via FunctionTool) can call to retrieve grounded
context, methodology, and prior analyses from the PostgreSQL-GraphRAG service.

Behaviour is controlled by environment variables:
    GRAPHRAG_URL          Base URL of the GraphRAG query service
                          (e.g. https://graphrag-query.<env>.azurecontainerapps.io)
    GRAPHRAG_TIMEOUT_SEC  HTTP timeout (default 30)
    GRAPHRAG_STUB_MODE    If "true", short-circuit and return a deterministic
                          stub response. Useful for wiring/smoke tests before
                          ingesting any documents.

If GRAPHRAG_URL is unset and GRAPHRAG_STUB_MODE is not "true", the tool
returns a graceful "knowledge service unavailable" string rather than raising,
so the agent can continue with its other tools.

Auth:
    The GraphRAG service is expected to be deployed inside the same Container
    Apps environment with internal ingress, so no auth is sent here. If you
    move it to a public endpoint, add Entra ID Bearer token retrieval via
    DefaultAzureCredential.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


def _stub_response(query: str, intent: str) -> str:
    """Deterministic stub used for smoke testing before ingestion."""
    return (
        "[GRAPHRAG STUB] No knowledge graph data ingested yet. "
        f"Query: {query!r}, intent: {intent!r}. "
        "Once GRAPHRAG_URL points at a populated GraphRAG service, this tool "
        "will return ranked sources, methodology citations, and prior-analysis "
        "context grounded in pgvector + Apache AGE."
    )


def query_geospatial_knowledge(
    query: str,
    intent: str = "auto",
    bbox: Optional[str] = None,
) -> str:
    """Retrieve geospatial context, methodology, and prior analyses from the
    knowledge graph.

    Call this BEFORE imagery sampling when the user asks:
      - "What is the best dataset / collection / sensor for ..."
      - "How do I measure / detect / classify ..."
      - References a past analysis ("like we did for ...", "same as before")
      - Questions about regions, events, or relationships across collections

    Do NOT call this for direct pixel-value queries — use sample_raster_value
    or analyze_raster instead. This tool is for *context*, not measurements.

    :param query: Natural-language question for the knowledge graph
    :param intent: Optional hint — one of "collection_selection", "methodology",
                   "prior_analysis", "entity_lookup", or "auto" (default)
    :param bbox: Optional WGS84 bbox "minx,miny,maxx,maxy" to scope results
    :return: Plain-text answer with inline source citations, or a graceful
             "unavailable" string the agent can fall back from
    """
    logger.info(f"[GRAPHRAG] query={query[:80]!r} intent={intent} bbox={bbox}")

    if os.getenv("GRAPHRAG_STUB_MODE", "").lower() == "true":
        return _stub_response(query, intent)

    base_url = os.getenv("GRAPHRAG_URL", "").rstrip("/")
    if not base_url:
        logger.warning("[GRAPHRAG] GRAPHRAG_URL not configured; returning unavailable")
        return (
            "Knowledge graph service is not configured for this deployment. "
            "Continuing without graph-grounded context."
        )

    timeout = float(os.getenv("GRAPHRAG_TIMEOUT_SEC", "30"))

    payload = {
        "user_question": query,
        # Pass intent and bbox via session_state — the GraphRAG agent ignores
        # unknown keys but they are available to the answer synthesizer.
        "session_state": {
            "intent": intent,
            "bbox": bbox,
            "source": "planetary-explorer-vision-agent",
        },
    }

    url = f"{base_url}/v1.0/query"
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=payload)
        if resp.status_code != 200:
            logger.warning(
                f"[GRAPHRAG] Non-200 from {url}: {resp.status_code} {resp.text[:200]}"
            )
            return (
                "Knowledge graph query failed (status "
                f"{resp.status_code}). Continuing without graph-grounded context."
            )
        data = resp.json()
    except (httpx.HTTPError, ValueError) as e:
        logger.warning(f"[GRAPHRAG] Request error: {e}")
        return (
            "Knowledge graph service is unreachable. "
            "Continuing without graph-grounded context."
        )

    answer = (data.get("answer") or "").strip()
    sources = data.get("source_documents") or []
    follow_ups = data.get("follow_up_questions") or []

    parts: list[str] = []
    if answer:
        parts.append(answer)

    if sources:
        parts.append("\n**Sources**")
        for i, s in enumerate(sources[:5], start=1):
            title = s.get("title") or s.get("name") or s.get("id") or "source"
            excerpt = (s.get("excerpt") or s.get("content") or "").strip()
            if len(excerpt) > 240:
                excerpt = excerpt[:237] + "..."
            line = f"{i}. {title}"
            if excerpt:
                line += f" — {excerpt}"
            parts.append(line)

    if follow_ups:
        parts.append("\n**Suggested follow-ups**")
        for q in follow_ups[:3]:
            parts.append(f"- {q}")

    return "\n".join(parts) if parts else (
        "Knowledge graph returned no relevant results for this query."
    )
